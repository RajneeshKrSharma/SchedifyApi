from os import path
from typing import Dict, Any

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


from typing import Dict, Any
from firebase_admin import messaging

def sendSplitExpensePush(
    title: str,
    body: str,
    email_fcm_map: Dict[str, str],  # email → fcmToken
    pushNotificationType
) -> Dict[str, Dict[str, Any]]:
    if not email_fcm_map:
        print("No tokens provided.")
        return {}

    tokens = list(email_fcm_map.values())  # Extract FCM tokens for sending

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

    # Send messages
    response = messaging.send_each_for_multicast(message)

    # Map email → status instead of token
    token_status_map: Dict[str, Dict[str, Any]] = {}
    for (email, token), res in zip(email_fcm_map.items(), response.responses):
        token_status_map[email] = {
            "notified": res.success,
            "message_id": res.message_id if res.success else None,
            "error": str(res.exception) if not res.success else None
        }

    print("\n" + "-"*50)
    print(f'Notify Status : {token_status_map}')
    print("-"*50 + "\n")

    return token_status_map