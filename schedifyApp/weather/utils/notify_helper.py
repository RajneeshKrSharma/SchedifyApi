from django.utils.timezone import now, is_naive, make_aware
from pytz import timezone
from datetime import datetime, timedelta

from schedifyApp.core.perform import format_datetime_or_none
from schedifyApp.weather.utils.notify_enums import TimeUnitType

TIME_DIVISOR = 3600
ist = timezone("Asia/Kolkata")

def get_current_time() -> datetime:
    current_time = now()

    if is_naive(current_time):
        return make_aware(current_time, timezone=ist)
    else:
        return current_time.astimezone(ist)

def eligibleTimeDifferenceToNotify(divisor) -> int:
    if divisor == 3600:
        return 1 # Hr
    elif divisor == 60:
        return 60 # Min
    else: # default
        return 1 # Hr

def get_unit(divisor):
    if divisor == 3600:
        return "Hr/s"
    elif divisor == 60:
        return "Min/s"
    else:
        return "N/A"


def get_time_until_update(
    time_diff
) -> str:
    print(f"get_time_until_update ~~~~~~~~~~~~~~~~~> time-diff: ${time_diff}")
    timeUnitType = getTimeUnitType(TIME_DIVISOR)

    if time_diff >= 3:
        delay = getTimeDelta(2, timeUnitType)
    elif time_diff >= 2:
        delay = getTimeDelta(1, timeUnitType)
    elif time_diff >= 1:
        delay = getTimeDelta(0, timeUnitType)
    else:
        return f"NOTIFY BLOCKED: ${"{:.2f}".format(time_diff)}"

    return f"{delay}"


def getTimeUnitType(divisor) -> TimeUnitType:
    if divisor == 3600:
        return TimeUnitType.Hour
    elif divisor == 60:
        return TimeUnitType.Minute
    else: # default
        return TimeUnitType.Hour



def getTimeDelta(
        value: int,
        unit: TimeUnitType
) -> timedelta:
    if unit == TimeUnitType.Hour:
         return timedelta(hours=value)
    elif unit == TimeUnitType.Minute:
        return timedelta(minutes=value)
    else:
        return timedelta(seconds=value)
    # if unit == TimeUnitType.Hour:
    #     return timedelta(minutes=value)
    # else:
    #     return timedelta(minutes=value)

def get_adjusted_time(
    time: datetime,
    time_diff
) -> dict:

    logs = {}

    td = time

    logs[f"{get_formatted_datetime()}"] = f"⮞ get_adjusted_time | time : {time} , time_diff : {time_diff}"

    timeUnitType = getTimeUnitType(TIME_DIVISOR)
    logs[f"{get_formatted_datetime()}"] = f"⮞ get_adjusted_time | timeUnitType : {timeUnitType}"

    if time_diff >= 3:
        timeDelta = getTimeDelta(2, timeUnitType)
        logs[f"{get_formatted_datetime()}"] = f"⮞ get_adjusted_time | eligible timedelta --> {timeDelta}"
        td = time + timeDelta

    elif time_diff >= 2:
        timeDelta = getTimeDelta(1, timeUnitType)
        logs[f"{get_formatted_datetime()}"] = f"⮞ get_adjusted_time | eligible timedelta --> {timeDelta}"
        td = time + getTimeDelta(1, timeUnitType)

    elif time_diff >= 1:
        logs[f"{get_formatted_datetime()}"] = f"⮞ get_adjusted_time | eligible timedelta --> {None}"
        td = None

    logs[f"{get_formatted_datetime()}"] = f"⮞ get_adjusted_time | next_notify_time : {td}"
    logs["next-notify-time"] = td

    return logs

def prepare_forcast_update_request(
    existing_weather_forecast_data,
    notifyTime,
    time_diff = None
) -> dict:
    weather_data = {}

    weather_data.update({
        "updated_count": existing_weather_forecast_data.updated_count + 1,
        "notify_count": existing_weather_forecast_data.notify_count + 1,
        "next_notify_in": get_time_until_update(
            time_diff
        ),
        "next_notify_at": format_datetime_or_none(notifyTime),
    })

    return weather_data


def get_formatted_datetime():
    current_time = now()
    return current_time.strftime("%d-%m-%Y_%H-%M-%S-%f")