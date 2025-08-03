from os import path

import firebase_admin
from firebase_admin import credentials, messaging

from schedifyApp.communication.utils import get_split_expense_image_url

filepath = path.join(path.abspath(path.join(path.dirname(__file__), '..', '..')), 'schedify_fb.json').replace("\\", "/")
cred = credentials.Certificate(filepath)
firebase_admin.initialize_app(cred)

def sendPush(title, body, channel, token, weather_image_url, uniqueId):
    message = messaging.MulticastMessage(
        data={
            'body': body,
            'title': title,
            'weather_image_url': weather_image_url,
            'uniqueId': str(uniqueId),
            'channel': channel,
            'displayNotification': 'YES'
        },
        tokens=[token] if isinstance(token, str) else token
    )

    response = messaging.send_each_for_multicast(message)
    print('Successfully sent message:', response)


def sendSplitExpensePush(title, body, tokens, pushNotificationType):
    # Ensure tokens is a list
    if isinstance(tokens, str):
        tokens = [tokens]

    # Avoid sending if token list is empty
    if not tokens:
        print("No tokens provided.")
        return

    print("body --------> ", body)
    print("title --------> ", title)

    message = messaging.MulticastMessage(
        data={
            'body': body,
            'title': title,
            'weather_image_url': get_split_expense_image_url(pushNotificationType=pushNotificationType),
            'uniqueId': "XI0234BH",
            'channel': "ALERT",
            'displayNotification': 'YES'
        },
        tokens=tokens
    )

    # Send and log result
    response = messaging.send_each_for_multicast(message)
    print(f'Successfully sent message to {len(response.responses)} recipients.')
