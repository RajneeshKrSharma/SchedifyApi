import json
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now, is_naive, make_aware
from pytz import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WeatherForecast, WeatherPincodeMappedData, NotifyMediumType
from .serializers import WeatherForecastSerializer, WeatherPincodeMappedDataSerializer
from .utils.notify_helper import get_current_time, TIME_DIVISOR, ist, eligibleTimeDifferenceToNotify, get_unit, \
    prepare_forcast_update_request, get_adjusted_time, getTimeDelta, get_time_until_update, get_formatted_datetime
from ..CustomAuthentication import CustomAuthentication
from ..address.models import Address
from ..address.serializers import AddressSerializer
from ..core.perform import prepare_forcast_create_request, round_down_to_nearest_3hr, CustomJSONEncoder, \
    prepare_forcast_update_request_scheduleItem_obj
from ..core.weather_utils import fetch_weather_data_by_pincode, send_weather_notification, \
    send_weather_push_notification, getUrlByWeatherType
from ..post_login.models import PostLoginUserDetail
from ..schedule_list.models import ScheduleItemList
from ..schedule_list.serializers import ScheduleItemListSerializers


class WeatherForecastAPIView(APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.app_user

        user_scheduled_objects = ScheduleItemList.objects.filter(
            user_id=user.id,
        )

        pincode = request.query_params.get('pincode')

        forecasts = WeatherForecast.objects.filter(
            scheduleItem__in=user_scheduled_objects,
            pincode = pincode,
            scheduleItem__isWeatherNotifyEnabled=True
        )

        serializer = WeatherForecastSerializer(forecasts, many=True)
        return Response(serializer.data)

    def post(self, request):

        serializer = WeatherForecastSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):

        forecast_id = request.query_params.get('forecast_id')

        try:
            instance = WeatherForecast.objects.get(id=forecast_id)
        except WeatherForecast.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = WeatherForecastSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_count=instance.updated_count + 1)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.db.models import Q


def weather_stats_view(request):
    query = request.GET.get("q", "").strip()
    weather_type = request.GET.get("weather_type", "").strip()
    pincode = request.GET.get("pincode", "").strip()
    is_active = request.GET.get("is_active", "").strip()  # NEW

    # Start by getting all forecasts
    forecasts = WeatherForecast.objects.filter(
        scheduleItem__isWeatherNotifyEnabled=True  # Filter by related ScheduleItem's isWeatherNotifyEnabled field
    ).order_by('-last_updated')
    # Apply filtering based on the search query
    if query:
        forecasts = forecasts.filter(
            Q(pincode__icontains=query) |
            Q(scheduleItemId__icontains=query) |
            Q(weatherType__icontains=query) |
            Q(weatherDescription__icontains=query)
        )

    if weather_type:
        forecasts = forecasts.filter(weatherType__icontains=weather_type)

    if pincode:
        forecasts = forecasts.filter(pincode__icontains=pincode)

    if is_active == "1":
        forecasts = forecasts.filter(isActive=True)
    elif is_active == "0":
        forecasts = forecasts.filter(isActive=False)

    # Apply the slicing after filtering
    forecasts = forecasts[:20]  # Latest 20 entries after filtering

    return render(request, "weather_stats.html", {
        "forecasts": forecasts,
        "query": query,
        "eligible_time_diff": eligibleTimeDifferenceToNotify(TIME_DIVISOR),
        "eligible_time_diff_unit": get_unit(TIME_DIVISOR),
        "weather_type": weather_type,
        "pincode": pincode,
        "is_active": is_active,
    })


class WeatherPincodeMappedDataAPIView(APIView):

    def get(self, request, format=None):
        pincode = request.query_params.get('pincode')
        if pincode:
            instance = get_object_or_404(WeatherPincodeMappedData, pincode=pincode)
            serializer = WeatherPincodeMappedDataSerializer(instance)
            return Response(serializer.data)
        else:
            all_data = WeatherPincodeMappedData.objects.all()
            serializer = WeatherPincodeMappedDataSerializer(all_data, many=True)
            return Response(serializer.data)

    def post(self, request, format=None):
        serializer = WeatherPincodeMappedDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, format=None):
        pincode = request.query_params.get('pincode')
        if not pincode:
            return Response({'error': 'Pincode is required for PATCH'}, status=status.HTTP_400_BAD_REQUEST)

        instance = get_object_or_404(WeatherPincodeMappedData, pincode=pincode)
        serializer = WeatherPincodeMappedDataSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WeatherScheduledData(APIView):
    def get(self, request, format=None):
        bulk_data = []
        user_info = None  # assume only one user context for now
        pincodes = set()  # to store unique pincodes

        # Get all schedule items where weather notification is enabled
        schedule_items = ScheduleItemList.objects.filter(
            isWeatherNotifyEnabled=True
        ).select_related('user')

        for schedule in schedule_items:
            user = schedule.user
            addresses = Address.objects.filter(user=user)

            # Serialize once per user
            if user_info is None:
                user_info = {
                    "id": user.id,
                    "emailId": user.emailId,
                    "otp": user.otp,
                    "otpTimeStamp": user.otpTimeStamp
                }

            schedule_serialized = ScheduleItemListSerializers(schedule).data

            for address in addresses:
                address_serialized = AddressSerializer(address).data
                pincode = address_serialized.get("pincode")

                if pincode:
                    pincodes.add(pincode)

                bulk_data.append({
                    "address": address_serialized,
                    "schedule_item": schedule_serialized
                })

        return Response({
            "bulk_data": bulk_data,
            "user_info": user_info,
            "pincodes": list(pincodes)  # convert set to list for JSON serialization
        })


class GetWeatherNotifyStatus(APIView):
    authentication_classes = [CustomAuthentication]  # Use the custom authentication class
    permission_classes = [IsAuthenticated]

    def get(self, request):
        listOfResults = []

        logs_result_dict = {}
        print("◦◦◦◦◦◦> STARTED >◦◦◦◦◦◦")
        logs_result_dict[f"{get_formatted_datetime()}"] = "◦◦◦◦◦◦> STARTED >◦◦◦◦◦◦"
        current_time = now()
        upcoming_window = current_time + timedelta(hours=12)

        scheduleItemsList = ScheduleItemList.objects.filter(
            isWeatherNotifyEnabled=True,
            pincode__isnull=False,
            dateTime__gte=current_time,
            dateTime__lt=upcoming_window

        ).exclude(
            pincode__exact=""
        )

        for scheduleItem in scheduleItemsList:
            fcmToken = get_object_or_404(PostLoginUserDetail, user_id=scheduleItem.user_id).fcmToken
            print(f"➜ ScheduleItem Info : {scheduleItem.id} | {scheduleItem.title}, Perform notify logic check . . .")
            logs_result_dict[f"{get_formatted_datetime()}"] = f"➜ ScheduleItem Info : {scheduleItem.id} | {scheduleItem.title}, Perform notify logic check . . ."
            result = performNotifyCheck(scheduleItem.pincode, scheduleItem, "", fcmToken, "PUSH_NOTIFICATION", logs_result_dict)
            additionalLogs = {f"{get_formatted_datetime()}": f"◦◦◦◦◦◦< END <◦◦◦◦◦◦"}
            result["logs"].update(additionalLogs)
            listOfResults.append(result)

        # scheduledItemId = request.query_params.get('scheduledItemId')
        # pincode = request.query_params.get('pincode')
        # notifyMedium = request.query_params.get('notifyMedium')

        # user = request.user
        # user_id = user.emailIdLinked_id
        # userEmailId = request.user.emailIdLinked.emailId

        #user_scheduled_object = get_object_or_404(ScheduleItemList, user_id=user_id, id=scheduledItemId)

        # if user_scheduled_object is not None:
        #     performNotifyCheck(pincode, user_scheduled_object, userEmailId, "", notifyMedium)
        #
        #     weather_item_obj = WeatherForecast.objects.filter(scheduleItem=user_scheduled_object)
        #     weather_status_images = WeatherStatusImages.objects.all()
        #
        #     response_data = {
        #         "weather_notify_details": WeatherForecastSerializer(weather_item_obj, many=True).data,
        #         "weather_status_images": WeatherStatusImagesSerializer(weather_status_images, many=True).data
        #     }
        #     return Response(response_data, status=status.HTTP_200_OK)

        #else:
        #    return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"notifyResult": listOfResults, "logs_result_dict": logs_result_dict, "scheduleItemsListSize": len(scheduleItemsList)}, status=status.HTTP_200_OK)

def checkAndSaveWeatherData(current_time, pincode) -> dict:
    weather_data_dict = {}
    logs = {}
    try:
        # pehle check kro ki kya weather data rakha hua hai particular pincode ke liye ?
        pincode_weather_data = get_object_or_404(WeatherPincodeMappedData, pincode=pincode)

        if pincode_weather_data:
            # agar exist krta hai to check kro ki jada purana to nai hai ?
            print("weather data for pincode exists !")
            logs[f"{get_formatted_datetime()}"] = f"⮞ weather data for pincode exists !"
            last_updated = pincode_weather_data.last_updated
            last_updated = make_aware(last_updated) if is_naive(last_updated) else last_updated.astimezone(ist)
            time_diff = abs((last_updated - current_time).total_seconds()) / TIME_DIVISOR

            if time_diff > 3: #agr 3 min ya phir 3 ghante se jada purana hai to update kro
                print("weather data older than 3")
                logs[f"{get_formatted_datetime()}"] = f"weather data older than 3 {get_unit(TIME_DIVISOR)}"

                result = fetch_weather_data_by_pincode(pincode)
                if isinstance(result, dict):
                    print("⮞ Weather data fetched ✅")
                    logs[f"{get_formatted_datetime()}"] = f"⮞ Weather data fetched ✅"
                    request = {
                        "weather_data": result,
                        "updated_count": pincode_weather_data.updated_count + 1
                    }
                    weather_data_dict["weather_data"] = result
                    serializer = WeatherPincodeMappedDataSerializer(pincode_weather_data, data=request, partial=True)

                    if serializer.is_valid():
                        serializer.save()
                        print("WeatherPincodeMappedData UPDATED")
                    else:
                        print("WeatherPincodeMappedData Error : ", serializer.errors)
                else:
                    logs[f"{get_formatted_datetime()}"] = f"Error while getting data - {result}"
            else:
                weather_data_dict["weather_data"] = pincode_weather_data.weather_data
                print("WeatherPincodeMappedData is valid data, not expired yet !")


    except Exception as e:
        # exist ni karta save kr lo weather ka data particular pincode ke liye
        print("Exception: ", e)
        logs[f"{get_formatted_datetime()}"] = f"Exception --> {e}"

        result = fetch_weather_data_by_pincode(pincode)
        if isinstance(result, dict):
            print("⮞ Weather data fetched ✅")
            logs[f"{get_formatted_datetime()}"] = f"⮞ Weather data fetched ✅"

            requestBody = {
                "pincode": pincode,
                "weather_data": result,
                "updated_count": 0
            }
            weather_data_dict["weather_data"] = result

            serializer = WeatherPincodeMappedDataSerializer(data=requestBody)
            if serializer.is_valid():
                serializer.save()
                print("WeatherPincodeMappedData SAVED")
            else:
                print("WeatherPincodeMappedData Error : ", serializer.errors)

        else:
            logs[f"{get_formatted_datetime()}"] = f"Error while getting data - {result}"

    weather_data_dict["logs"] = logs

    return weather_data_dict

def calculateRevisedNotifyDetails(
        current_time, revisedScheduleDateTime, logs_result_dict
) -> dict:
    print("⮞ CALCULATION FOR NOTIFY TIME : STARTED 🟠")
    logs_result_dict[f"{get_formatted_datetime()}"] = "⮞ CALCULATION FOR NOTIFY TIME : STARTED 🟠"

    calculate_time_diff_for_next_notify = abs(
        (revisedScheduleDateTime - current_time).total_seconds()) / TIME_DIVISOR

    logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ calculate_time_diff_for_next_notify : {calculate_time_diff_for_next_notify}"
    logs = get_adjusted_time(current_time, calculate_time_diff_for_next_notify)

    next_notify_time = logs["next-notify-time"]
    logs_result_dict.update(logs)

    #print("⮞ Notify time will be same as assumed_notify_time: ")

    #logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ Notify time will be same as assumed_notify_time: {logs_result_dict}"

    print("⮞ Next notify time diff: calculate_time_diff_for_next_notify :", calculate_time_diff_for_next_notify)
    logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ Next notify time diff: {calculate_time_diff_for_next_notify}"

    return { "revisedNotifyTime": next_notify_time, "next_notify_time_time_diff": calculate_time_diff_for_next_notify, "logs_result_dict": logs_result_dict }

def getWeatherDataForScheduledDateTime(rounded_schedule, pinned_weather_forecast_list):
    for entry in pinned_weather_forecast_list:
        try:
            entry_time = datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S")
            if entry_time == rounded_schedule:
                return entry  # direct return when match found
        except Exception as e:
            print("⛔ Error parsing forecast entry:", e)
            continue

    return None  # agar kuch match nahi hua

def prepareWeatherData(weather_data):
    weather_data = {}

def markScheduleItemAsNotEligibleForNotify(
    notifyMedium, time_diff, weather_data
) -> dict:
    result_dict = {}

    requestBody = prepare_forcast_create_request(
        weather_data=weather_data,
        notifyTime=None,
        notifyInTime=None,
        notifyMedium=notifyMedium
    )
    requestBody["isActive"] = False
    requestBody["elig_diff"] = time_diff
    requestBody["elig_diff_unit"] = get_unit(TIME_DIVISOR)

    # also update isActive to false & lastUpdated time
    serializer = WeatherForecastSerializer(data=requestBody)
    if serializer.is_valid():
        serializer.save()
        result_dict["result"] = serializer.data

    return result_dict

def markUpdateScheduleItemAsNotEligibleForNotify(
    time_diff, existing_weather_forecast_data
) -> dict:
    result_dict = {}

    requestBody = prepare_forcast_update_request(
        existing_weather_forecast_data=existing_weather_forecast_data,
        notifyTime=None,
        time_diff=time_diff
    )
    print(f"requestBody -------------------------------> ${requestBody}")
    requestBody["isActive"] = False
    requestBody["elig_diff"] = time_diff
    requestBody["elig_diff_unit"] = get_unit(TIME_DIVISOR)

    # also update isActive to false & lastUpdated time
    serializer = WeatherForecastSerializer(existing_weather_forecast_data, data=requestBody, partial=True)
    if serializer.is_valid():
        serializer.save()

        print("------------------------------------------>")
        result_dict["result"] = serializer.data
    else:
        print(f"exceptions --------> ${serializer.errors}")

    return result_dict

def performNotifyCheck(pincode, scheduleItem, userEmailId, fcmToken, notifyMedium, logs_result_dict) -> dict:
    final_result_dict = {}
    current_time = get_current_time()

    # First : fetch weather data for pincode

    print(f"⮞  checkAndSaveWeatherData : STARTED")
    logs_result_dict[f"{get_formatted_datetime()}"] = "⮞ checkAndSaveWeatherData : STARTED"
    data = checkAndSaveWeatherData(current_time=current_time, pincode=pincode)
    print(f"⮞ checkAndSaveWeatherData ✔️ ")
    logs_result_dict = data["logs"]
    logs_result_dict[f"{get_formatted_datetime()}"] = "⮞ checkAndSaveWeatherData ✔️"

    # 2. Parse schedule datetime
    schedule_items_date_time = scheduleItem.dateTime.astimezone(ist)
    print(f"schedule_dt : {schedule_items_date_time}")
    logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ schedule_dt : {schedule_items_date_time}"
    rounded_schedule = round_down_to_nearest_3hr(schedule_items_date_time)
    print(f"rounded_schedule value nearest_3hr : {rounded_schedule}")
    logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ rounded_schedule value nearest_3hr : {rounded_schedule}"


    """ Logic to find weather data for scheduled_date_time from fetched Weather api data """
    pinned_weather_forecast_list = data["weather_data"].get("list", [])
    revisedScheduleDateTime = schedule_items_date_time

    matched_forecast = getWeatherDataForScheduledDateTime(rounded_schedule=rounded_schedule, pinned_weather_forecast_list=pinned_weather_forecast_list)

    """ Below code start to create request body params data to create/update Weather Forecast Data."""

    unique_key = f"{pincode}-{scheduleItem.id}"
    forecast_time_dt = datetime.strptime(matched_forecast["dt_txt"], "%Y-%m-%d %H:%M:%S")
    forecast_time_ist = timezone("Asia/Kolkata").localize(forecast_time_dt)
    forecast_time_str = forecast_time_ist.strftime("%Y-%m-%dT%H:%M:%S")

    existing_weather_forecast_data: WeatherForecast = WeatherForecast.objects.filter(
        unique_key=unique_key,
        pincode=pincode
    ).first()

    if existing_weather_forecast_data:
        print(f"⮞ Executing existing_weather_forecast_data block")
        logs_result_dict[f"{get_formatted_datetime()}"] = "⮞ Executing existing_weather_forecast_data block"

        # already has entry in WeatherForecast

        nextNotifyAt = existing_weather_forecast_data.next_notify_at
        # nextNotifyAt mila

        if nextNotifyAt is not None:
            print(f"⮞ nextNotifyAt is not none")
            logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ nextNotifyAt is not none"

            # Convert the date and time into IST
            # Make schedule_time timezone-aware
            if is_naive(nextNotifyAt):
                nextNotifyAt = make_aware(nextNotifyAt, timezone=ist)
            else:
                nextNotifyAt = nextNotifyAt.astimezone(ist)

            isTimeToNotify = nextNotifyAt < current_time
            print(f"💡 isTimeToNotify: {isTimeToNotify} | Time left: {abs(nextNotifyAt - current_time)}")
            logs_result_dict[f"{get_formatted_datetime()}"] = f"💡 isTimeToNotify: {isTimeToNotify} | Time left: {abs(nextNotifyAt - current_time)}"

            print(f"⮞ nextNotifyAt: {nextNotifyAt} | revisedScheduleDateTime: {revisedScheduleDateTime}")
            logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ nextNotifyAt: {nextNotifyAt} | revisedScheduleDateTime: {revisedScheduleDateTime}"

            time_diff = abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / TIME_DIVISOR
            # ye check kr lo kya aur notify krne ke liye time_diff eligible hai ?
            logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ Is satisfy eligibleTimeDifferenceToNotify(TIME_DIVISOR), time_diff -> {time_diff}"


            if not (time_diff > eligibleTimeDifferenceToNotify(TIME_DIVISOR)):
                # agar ni hai to not eligible mark kr do
                print(f"🔴 In fresh data, markScheduleItemAsNotEligibleForNotify")
                logs_result_dict[
                    f"{get_formatted_datetime()}"] = f"🔴 In fresh data, markScheduleItemAsNotEligibleForNotify"
                data = markUpdateScheduleItemAsNotEligibleForNotify(
                    existing_weather_forecast_data=existing_weather_forecast_data,
                    time_diff=time_diff
                )
                final_result_dict["weatherForcastData"] = data["result"]

            else:
                # wapas se data calculate kr lo aur
                print(f"⮞ Existing weather forcast data, Is satisfy eligibleTimeDifferenceToNotify(TIME_DIVISOR) : YES")
                logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ Existing weather forcast data, Is satisfy eligibleTimeDifferenceToNotify(TIME_DIVISOR) : YES"

                if isTimeToNotify:
                    seconds_left = f"⮞ abs(nextNotifyAt - revisedScheduleDateTime).total_seconds(): {abs(nextNotifyAt - revisedScheduleDateTime).total_seconds()}"
                    print(seconds_left)
                    logs_result_dict[f"{get_formatted_datetime()}"] = seconds_left

                    minutes_left = f"⮞ abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / 60 (Mins LEFT): {abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / 60}"

                    print(minutes_left)
                    logs_result_dict[f"{get_formatted_datetime()}"] = minutes_left

                    hours_left = f"⮞ abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / 3600 (Hours LEFT): {abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / 3600}"
                    print(hours_left)
                    logs_result_dict[f"{get_formatted_datetime()}"] = hours_left

                    # now calculate next notify time

                    notifyDetails = calculateRevisedNotifyDetails(
                        current_time=nextNotifyAt,
                        revisedScheduleDateTime=revisedScheduleDateTime,
                        logs_result_dict=logs_result_dict,
                    )
                    logs_result_dict.update(notifyDetails["logs_result_dict"])
                    print("⮞ CALCULATION FOR NOTIFY TIME : END 🟢\n")
                    logs_result_dict[f"{get_formatted_datetime()}"] = "⮞ CALCULATION FOR NOTIFY TIME : END 🟢"

                    notifyTime = notifyDetails["revisedNotifyTime"]
                    next_notify_time_time_diff = notifyDetails["next_notify_time_time_diff"]

                    requestBody = prepare_forcast_update_request_scheduleItem_obj(
                        existing_weather_forecast_data=existing_weather_forecast_data,
                        notifyTime=notifyTime,
                        scheduledItem=scheduleItem,
                        time_diff=next_notify_time_time_diff,
                        isNotifyAccountable=True
                    )
                    requestBody["elig_diff"] = next_notify_time_time_diff
                    requestBody["elig_diff_unit"] = get_unit(TIME_DIVISOR)
                    requestBody["isActive"] = notifyTime is not None

                    serializer = WeatherForecastSerializer(existing_weather_forecast_data, data=requestBody,
                                                           partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        final_result_dict["weatherForcastData"] = serializer.data

                        print("⮞ Proceed to notify . . ")
                        logs_result_dict[f"{get_formatted_datetime()}"] = "⮞ Proceed to notify . . "
                        if existing_weather_forecast_data.notify_medium == NotifyMediumType.EMAIL.name:
                            emailRequestBody = {
                                "emailId": userEmailId,
                                "task_name": scheduleItem.title,
                                "schedule_date_time": schedule_items_date_time.strftime("%d %b, %Y %I:%M %p"),
                                "weather_status": f"{existing_weather_forecast_data.weatherType}, {existing_weather_forecast_data.weatherDescription}"
                            }
                            send_weather_notification(
                                request=emailRequestBody
                            )
                        elif existing_weather_forecast_data.notify_medium == NotifyMediumType.PUSH_NOTIFICATION.name:
                            try:
                                print(
                                    f"⮞ existing_weather_forecast_data.weatherType: {existing_weather_forecast_data.weatherType}")
                                logs_result_dict[
                                    f"{get_formatted_datetime()}"] = f"⮞ existing_weather_forecast_data.weatherType: {existing_weather_forecast_data.weatherType}"

                                # getWeatherImageUrl = get_weather_image_by_partial_status(
                                #     existing_weather_forecast_data.weatherType).url

                                requestBody = {
                                    "title": f"{existing_weather_forecast_data.weatherType} Alert!",
                                    "body": f"{existing_weather_forecast_data.weatherType}, {existing_weather_forecast_data.weatherDescription} "
                                            f"is expected in your area,  {scheduleItem.title} was scheduled for {schedule_items_date_time.strftime("%d %b, %Y %I:%M %p")}",
                                    "channel": "ALERT",
                                    "token": fcmToken,
                                    "weather_image_url": getUrlByWeatherType(existing_weather_forecast_data.weatherType),
                                    "uniqueId": existing_weather_forecast_data.unique_key
                                }
                                result = send_weather_push_notification(
                                    request=requestBody
                                )
                                print(f"⮞ Notify result : {result}")
                                logs_result_dict[
                                    f"{get_formatted_datetime()}"] = f"⮞ Notify result : {result}"

                            except Exception as e:
                                print("⛔ Error while sending push notification:", e)
                                logs_result_dict[
                                    f"{get_formatted_datetime()}"] = f"⛔ Error while sending push notification: {e}"
                else:
                    logs_result_dict[
                        f"{get_formatted_datetime()}"] = f"⮞ Abhi time ni hua notify krne ke liye !"

            # agar time ni hua hai to kuch mt kro

            # else:
            #     print("UPDATE update_forecast_entry: isNotifyAccountable : false")
            #     update_request = prepare_forcast_update_request_scheduleItem_obj(
            #         current_time=current_time,
            #         existing_weather_forecast_data=existing_weather_forecast_data,
            #         nextNotifyAt=nextNotifyAt,
            #         scheduledItem=scheduleItem,
            #         isNotifyAccountable=False
            #     )
            #     serializer = WeatherForecastSerializer(existing_weather_forecast_data, data=update_request,
            #                                            partial=True)
            #     if serializer.is_valid():
            #         serializer.save()

        else:
            # nextNotifyAt mila aur wo None hai yani ki expired hai no actionable block ushke liye
            print("🔴 Next_notify_at is None. 🔴")
            logs_result_dict[f"{get_formatted_datetime()}"] = "🔴 Next_notify_at is None. 🔴"

    # for fresh data
    else:
        print(f"⮞ Executing for fresh weather_forecast_data block")
        logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ Executing for fresh weather_forecast_data block"
        # for fresh data
        weather_data = {
            "pincode": pincode,
            "unique_key": unique_key,
            "forecast_time": forecast_time_str,
            "timeStamp": matched_forecast["dt"],
            "weatherType": matched_forecast["weather"][0]["main"],
            "weatherDescription": matched_forecast["weather"][0]["description"],
            "temperature_celsius": matched_forecast["main"]["temp"],
            "humidity_percent": matched_forecast["main"]["humidity"],
            "scheduleItem": json.dumps(scheduleItem, cls=CustomJSONEncoder)
        }

        print("⮞ revisedScheduleDateTime ->", revisedScheduleDateTime)
        logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ revisedScheduleDateTime -> {revisedScheduleDateTime}"
        print("⮞ current_time ->", current_time)
        logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ current_time -> {current_time}"

        calculate_time_diff_to_check_eligibility_for_notify = abs((revisedScheduleDateTime - current_time).total_seconds()) / TIME_DIVISOR
        print("⮞ calculate_time_diff_to_check_eligibility_for_notify of abs((revisedScheduleDateTime - current_time) ->", calculate_time_diff_to_check_eligibility_for_notify)
        logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ calculate_time_diff_to_check_eligibility_for_notify of abs((revisedScheduleDateTime - current_time) -> {calculate_time_diff_to_check_eligibility_for_notify}"

        if not (calculate_time_diff_to_check_eligibility_for_notify > eligibleTimeDifferenceToNotify(TIME_DIVISOR)):
            #kya apko notify kiya ja sakta hai ya nahi

            print(f"🔴 In fresh data, mark Schedule Item As Not Eligible For Notify")
            logs_result_dict[
                f"{get_formatted_datetime()}"] = f"🔴 In fresh data, mark Schedule Item As Not Eligible For Notify"
            data = markScheduleItemAsNotEligibleForNotify(
                weather_data=weather_data,
                notifyMedium=notifyMedium,
                time_diff=calculate_time_diff_to_check_eligibility_for_notify
            )
            final_result_dict["weatherForcastData"] = data["result"]

        else:
            print(f"⮞ In fresh data, Eligible for notify")
            logs_result_dict[f"{get_formatted_datetime()}"] = f"⮞ In fresh data, Eligible for notify"

            # fresh created and also eligible to notify
            notifyDetails = calculateRevisedNotifyDetails(
                current_time=current_time,
                revisedScheduleDateTime=revisedScheduleDateTime,
                logs_result_dict=logs_result_dict,
            )
            logs_result_dict.update(notifyDetails["logs_result_dict"])
            print("⮞ CALCULATION FOR NOTIFY TIME : END 🟢\n")
            logs_result_dict[f"{get_formatted_datetime()}"] = "⮞ CALCULATION FOR NOTIFY TIME : END 🟢"

            notifyTime = notifyDetails["revisedNotifyTime"]
            next_notify_time_time_diff = notifyDetails["next_notify_time_time_diff"]

            notifyInTime = get_time_until_update(next_notify_time_time_diff)
            print(f"notifyTime -------> {notifyTime}")
            print(f"notifyInTime -------> {notifyInTime}")
            requestBody = prepare_forcast_create_request(
                weather_data=weather_data,
                notifyTime=notifyTime,
                notifyInTime=notifyInTime,
                notifyMedium=notifyMedium
            )
            requestBody["elig_diff"] = next_notify_time_time_diff
            requestBody["elig_diff_unit"] = get_unit(TIME_DIVISOR)
            requestBody["isActive"] = notifyTime is not None
            serializer = WeatherForecastSerializer(data=requestBody)
            print("->"*100)
            if serializer.is_valid():
                serializer.save()
                final_result_dict["weatherForcastData"] = serializer.data

            else:
                print("---------------------------------------------------------------------------------->")
                print(f"error: {serializer.errors}")


    final_result_dict["logs"] = logs_result_dict

    return final_result_dict

    # # expiring ki condition hai ye
    # if not (current_time <= schedule_items_date_time <= current_time + timedelta(hours=24)):
    #     """
    #         This block simple states that scheduled_date_time is expired, or
    #         it not scheduled within next day (current_Date_time + 24hrs).
    #     """
    #
    #     # hm yha un expired scheduled items ke isActive=False and last_updated=now se update kr denge
    #     from schedifyApp.schedule_list.models import ScheduleItemList
    #
    #     # Step 1: Retrieve expired schedule items
    #     expired_schedule_items = ScheduleItemList.objects.filter(
    #         dateTime__lt=current_time
    #     )
    #
    #     # Step 2: Update related forecasts if expired schedule items exist
    #     if expired_schedule_items.exists():
    #         # Using the ForeignKey relationship to fetch forecasts related to expired schedule items
    #         forecasts_to_update = WeatherForecast.objects.filter(
    #             scheduleItem__in=expired_schedule_items,  # Using the related field in ForeignKey
    #             isActive=True,
    #         )
    #
    #         if forecasts_to_update.exists():
    #             updated_count = forecasts_to_update.update(
    #                 isActive=False,
    #                 # Assuming the WeatherForecast model has a field like 'last_updated'
    #                 last_updated=now()  # Example field if you have it
    #             )
    #             print(f"✅ Updated {updated_count} expired forecast(s).")
    #         else:
    #             print("✅ forecasts found is expired ")
    #     else:
    #         print("✅ schedule items found is expired ")