from os import path

import firebase_admin
from firebase_admin import credentials, messaging

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


def sendSplitExpensePush(title, body, tokens):
    # Ensure tokens is a list
    if isinstance(tokens, str):
        tokens = [tokens]

    # Avoid sending if token list is empty
    if not tokens:
        print("No tokens provided.")
        return

    message = messaging.MulticastMessage(
        data={
            'body': body,
            'title': title,
            'weather_image_url': "https://schedify.pythonanywhere.com/media/pictures/collaborator_image.png",
            'uniqueId': "XI0234BH",
            'channel': "ALERT",
            'displayNotification': 'YES'
        },
        tokens=tokens
    )

    # Send and log result
    response = messaging.send_each_for_multicast(message)
    print(f'Successfully sent message to {len(response.responses)} recipients.')
