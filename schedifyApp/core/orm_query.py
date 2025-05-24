from django.db import connection

from schedifyApp.address.models import Address


query = """
SELECT a.*, s.dateTime AS schedule_time, s.id AS sid
FROM schedifyApp_address AS a
INNER JOIN schedifyApp_emailidregistration AS e ON a.user_id = e.id
INNER JOIN schedifyApp_scheduleitemlist AS s ON s.user_id = e.id
WHERE s.isWeatherNotifyEnabled = TRUE;
"""
results = list(Address.objects.raw(query))
