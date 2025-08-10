import json
from datetime import datetime, timedelta

from django.forms import model_to_dict
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now, is_naive, make_aware
from pytz import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WeatherForecast, WeatherPincodeMappedData, WeatherStatusImages, NotifyMediumType
from .serializers import WeatherForecastSerializer, WeatherPincodeMappedDataSerializer, WeatherStatusImagesSerializer
from ..CustomAuthentication import CustomAuthentication
from ..address.models import Address
from ..address.serializers import AddressSerializer
from ..core.perform import round_down_to_nearest_3hr, getTimeDelta, \
    TimeUnitType, prepare_forcast_update_request, CustomJSONEncoder, get_adjusted_time, prepare_forcast_create_request, \
    get_time_until_update, prepare_forcast_update_request_scheduleItem_obj, \
    prepare_forcast_update_request_for_schedule_obj
from ..core.weather_utils import fetch_weather_data_by_pincode, update_weather_data_for_pincode_entry, \
    create_weather_data_for_pincode_entry, update_forecast_entry, send_weather_notification, create_forecast_entry, \
    get_pincode_weather_data_single_entry, get_schedule_item_single_entry, send_weather_push_notification
from ..schedule_list.models import ScheduleItemList
from ..schedule_list.serializers import ScheduleItemListSerializers


class WeatherForecastAPIView(APIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.app_user
        current_time = now()

        user_scheduled_objects = ScheduleItemList.objects.filter(
            user_id=user.id,
            dateTime__gt=current_time,
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


class WeatherStatus(APIView):
    authentication_classes = [CustomAuthentication]  # Use the custom authentication class
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scheduledItemId = request.query_params.get('scheduledItemId')
        pincode = request.query_params.get('pincode')
        notifyMedium = request.query_params.get('notifyMedium')

        user = request.user
        user_id = user.emailIdLinked_id
        userEmailId = request.user.emailIdLinked.emailId

        user_scheduled_object = get_object_or_404(ScheduleItemList, user_id=user_id, id=scheduledItemId)

        if user_scheduled_object is not None:
            perform(pincode, user_scheduled_object, userEmailId, "", notifyMedium)

            weather_item_obj = WeatherForecast.objects.filter(scheduleItem=user_scheduled_object)
            weather_status_images = WeatherStatusImages.objects.all()

            response_data = {
                "weather_notify_details": WeatherForecastSerializer(weather_item_obj, many=True).data,
                "weather_status_images": WeatherStatusImagesSerializer(weather_status_images, many=True).data
            }
            return Response(response_data, status=status.HTTP_200_OK)

        else:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)


def get_weather_image_by_partial_status(partial_status: str) -> WeatherStatusImages | None:
    partial_status_upper = partial_status.upper()
    for image in WeatherStatusImages.objects.all():
        if image.status.upper() in partial_status_upper:
            return image
    return None



def perform(pincode, scheduleItem, userEmailId, fcmToken, notifyMedium):
    DIVISOR = 3600
    ist = timezone("Asia/Kolkata")
    current_time = now()

    if is_naive(current_time):
        current_time = make_aware(current_time, timezone=ist)
    else:
        current_time = current_time.astimezone(ist)

    weather_forecast_data = fetch_weather_data_by_pincode(pincode)

    try:
        pincode_weather_data = get_object_or_404(WeatherPincodeMappedData, pincode=pincode)

        if pincode_weather_data:

            last_updated = datetime.fromisoformat(pincode_weather_data["last_updated"])
            last_updated = make_aware(last_updated) if is_naive(last_updated) else last_updated.astimezone(ist)

            time_diff = abs((last_updated - current_time).total_seconds()) / DIVISOR

            if time_diff > 3:
                request = {
                    "weather_data": weather_forecast_data,
                    "updated_count": pincode_weather_data.updated_count + 1
                }
                serializer = WeatherPincodeMappedDataSerializer(pincode_weather_data, data=request.data, partial=True)

                if serializer.is_valid():
                    serializer.save()
                    print("WeatherPincodeMappedData UPDATED")
                else:
                    print("INVALID WeatherPincodeMappedData aaaaaaaaaaaaa")

        else:
            requestBody = {
                "pincode": pincode,
                "weather_data": weather_forecast_data,
                "updated_count": 0
            }
            serializer = WeatherPincodeMappedDataSerializer(data=requestBody)
            if serializer.is_valid():
                serializer.save()
                print("WeatherPincodeMappedData SAVED")
            else:
                print("INVALID WeatherPincodeMappedData bbbbbbbbbbbb")
            #create_weather_data_for_pincode_entry(pincode, weather_forecast_data)
    except Exception as e:

        print("Exception: ", e)

        requestBody = {
            "pincode": pincode,
            "weather_data": weather_forecast_data,
            "updated_count": 0
        }
        serializer = WeatherPincodeMappedDataSerializer(data=requestBody)
        if serializer.is_valid():
            serializer.save()
            print("WeatherPincodeMappedData SAVED")
        else:
            print("INVALID WeatherPincodeMappedData ccccccccccc", serializer.errors)

    # 2. Parse schedule datetime
    schedule_items_date_time = scheduleItem.dateTime.astimezone(ist)

    print(f"schedule_dt : {schedule_items_date_time}")

    if not (current_time <= schedule_items_date_time <= current_time + timedelta(hours=24)):
        """
            This block simple states that scheduled_date_time is expired, or
            it not scheduled within next day (current_Date_time + 24hrs).
        """
        from schedifyApp.schedule_list.models import ScheduleItemList

        # Step 1: Retrieve expired schedule items
        expired_schedule_items = ScheduleItemList.objects.filter(
            dateTime__lt=current_time
        )

        # Step 2: Update related forecasts if expired schedule items exist
        if expired_schedule_items.exists():
            # Using the ForeignKey relationship to fetch forecasts related to expired schedule items
            forecasts_to_update = WeatherForecast.objects.filter(
                scheduleItem__in=expired_schedule_items,  # Using the related field in ForeignKey
                isActive=True,
            )

            if forecasts_to_update.exists():
                updated_count = forecasts_to_update.update(
                    isActive=False,
                    # Assuming the WeatherForecast model has a field like 'last_updated'
                    last_updated=now()  # Example field if you have it
                )
                print(f"✅ Updated {updated_count} expired forecast(s).")
            else:
                print("✅ forecasts found is expired ")
        else:
            print("✅ schedule items found is expired ")

    else:
        """
            This block simple states that scheduled_date_time lies within next day (current_Date_time + 24hrs).
        """

        """ Logic to find weather data for scheduled_date_time from fetched Weather api data """
        pinned_weather_forecast_list = weather_forecast_data.get("list", [])
        rounded_schedule = round_down_to_nearest_3hr(schedule_items_date_time)
        revisedScheduleDateTime = schedule_items_date_time - getTimeDelta(1, TimeUnitType.Hour)

        matched_forecast = None
        for entry in pinned_weather_forecast_list:
            try:
                entry_time = datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S")
                if entry_time == rounded_schedule:
                    matched_forecast = entry
                    break
            except Exception as e:
                print("⛔ Error parsing fore cast entry:", e)

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
            nextNotifyAt = existing_weather_forecast_data.next_notify_at

            if nextNotifyAt is not None:
                # Convert the date and time into IST
                # Make schedule_time timezone-aware
                if is_naive(nextNotifyAt):
                    nextNotifyAt = make_aware(nextNotifyAt, timezone=ist)
                else:
                    nextNotifyAt = nextNotifyAt.astimezone(ist)

                isTimeToSendEmailWithUpdate = nextNotifyAt < current_time
                print("💡 isTimeToSendEmailWithUpdate:", isTimeToSendEmailWithUpdate, "| Time left:",
                      abs(nextNotifyAt - current_time))

                print("🟣 nextNotifyAt:", nextNotifyAt, "| current_time:", current_time)

                print("🔵 nextNotifyAt:", nextNotifyAt, "| revisedScheduleDateTime:", revisedScheduleDateTime)


                time_diff = int(abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / DIVISOR)

                if isTimeToSendEmailWithUpdate:
                    print("abs(nextNotifyAt - revisedScheduleDateTime).total_seconds():",
                          abs(nextNotifyAt - revisedScheduleDateTime).total_seconds())

                    print("abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / 60 (Mins LEFT):",
                          abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / 60)

                    print("💡 abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / 3600 (Hours LEFT):",
                          abs(nextNotifyAt - revisedScheduleDateTime).total_seconds() / 3600)

                    update_request = prepare_forcast_update_request_scheduleItem_obj(
                        current_time=current_time,
                        existing_weather_forecast_data=existing_weather_forecast_data,
                        nextNotifyAt=nextNotifyAt,
                        scheduledItem=scheduleItem,
                        time_diff=time_diff,
                        isNotifyAccountable=True
                    )
                    serializer = WeatherForecastSerializer(existing_weather_forecast_data, data=update_request,
                                                           partial=True)
                    if serializer.is_valid():
                        serializer.save()

                        print("Proceed to send email =>")
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
                                print(f"existing_weather_forecast_data.weatherType: {existing_weather_forecast_data.weatherType}")

                                getWeatherImageUrl = get_weather_image_by_partial_status(existing_weather_forecast_data.weatherType).url
                                print(f"existing_weather_forecast_data.weatherType : {existing_weather_forecast_data.weatherType} | getWeatherImageUrl : {getWeatherImageUrl}")
                                requestBody = {
                                    "title": f"{existing_weather_forecast_data.weatherType} Alert!",
                                    "body": f"{existing_weather_forecast_data.weatherType}, {existing_weather_forecast_data.weatherDescription} "
                                            f"is expected in your area,  {scheduleItem.title} was scheduled for {schedule_items_date_time.strftime("%d %b, %Y %I:%M %p")}",
                                    "channel": "ALERT",
                                    "token": fcmToken,
                                    "weather_image_url": getWeatherImageUrl,
                                    "uniqueId": existing_weather_forecast_data.unique_key
                                }
                                send_weather_push_notification(
                                    request=requestBody
                                )
                            except Exception as e:
                                print("⛔ Error while sending push notification:", e)


                else:
                    print("UPDATE update_forecast_entry: isNotifyAccountable : false")
                    update_request = prepare_forcast_update_request_scheduleItem_obj(
                        current_time=current_time,
                        existing_weather_forecast_data=existing_weather_forecast_data,
                        nextNotifyAt=nextNotifyAt,
                        scheduledItem=scheduleItem,
                        isNotifyAccountable=False
                    )
                    serializer = WeatherForecastSerializer(existing_weather_forecast_data, data=update_request, partial=True)
                    if serializer.is_valid():
                        serializer.save()

            else:
                print("🔴 Next_notify_at is None. 🔴")


        else:
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

            print("WHILE CREATE : revisedScheduleDateTime ->", revisedScheduleDateTime)
            print("WHILE CREATE : current_time ->", current_time)

            time_diff = abs((revisedScheduleDateTime - current_time).total_seconds()) / DIVISOR
            print("WHILE CREATE : time_diff of abs((revisedScheduleDateTime - current_time) ->", time_diff)

            time_diff = round(time_diff)
            print("WHILE CREATE : round off time_diff of abs((revisedScheduleDateTime - current_time) ->", time_diff)

            assumed_notify_time = get_adjusted_time(current_time, time_diff)
            print("assumed_notify_time :", assumed_notify_time)

            if assumed_notify_time is not None:
                if assumed_notify_time > revisedScheduleDateTime:
                    print("assumed_notify_time :", assumed_notify_time, "is GREATER THAN revisedScheduleDateTime :",
                          revisedScheduleDateTime)
                    notifyTime = revisedScheduleDateTime - timedelta(minutes=5)
                    print("notify time will be less than 5 min before current time i.e", notifyTime)
                    time_diff_for_notifyIn = abs(notifyTime - current_time).total_seconds() / DIVISOR

                else:
                    print("notify time will be assumed_notify_time:", assumed_notify_time)
                    notifyTime = assumed_notify_time
                    time_diff_for_notifyIn = time_diff

                print("time_diff_for_notifyIn :", time_diff_for_notifyIn)

                time_diff_for_notifyIn = round(time_diff_for_notifyIn)
                print("time_diff_for_notifyIn round : ", time_diff_for_notifyIn)

                requestBody = prepare_forcast_create_request(
                        weather_data=weather_data,
                        notifyTime=notifyTime,
                        notifyInTime=get_time_until_update(time_diff_for_notifyIn),
                        notifyMedium=notifyMedium
                    )
                serializer = WeatherForecastSerializer(data=requestBody)
                if serializer.is_valid():
                    serializer.save()

            else:
                requestBody = prepare_forcast_create_request(
                        weather_data=weather_data,
                        notifyTime=None,
                        notifyInTime=None
                    )
                serializer = WeatherForecastSerializer(data=requestBody)
                if serializer.is_valid():
                    serializer.save()