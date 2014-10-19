from ConfigParser import SafeConfigParser
import requests

def pushover(message):
    config = SafeConfigParser()
    config.read('config.cfg')
    token = config.get('Pushover', 'token')
    user = config.get('Pushover', 'user')
    data = {
        'token': token,
        'user': user,
        'message': message
    }

    req = requests.post('https://api.pushover.net/1/messages.json', data=data)
    return req.text