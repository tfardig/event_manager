import redis
import json
import time
from ConfigParser import SafeConfigParser

import notifications

config = SafeConfigParser()
config.read('config.cfg')
DB_HOST = config.get('Redis', 'host')
DB = config.get('Redis', 'db')

def get_db():
    db = redis.StrictRedis(host=DB_HOST, db=DB)
    return db


def get_alerts(streamname):
    """

    :rtype : [dict]
    """
    db = get_db()
    json.loads(db.get('alert:%s' % streamname))


def set_alerts(streamname, alerts):
    db = get_db()
    db.set('alert:%s' % streamname, json.dumps(alerts))


def add_alert(streamname, alert):
    db = get_db()
    alerts = get_alerts(streamname)
    alerts.append(alert)


def _check_alert_part(tuple, value, time_diff, value_diff):
    return {
        'or': any([_check_alert_part(t) for t in tuple[1]]),
        'and': all([_check_alert_part(t) for t in tuple[1]]),
        'lt': value < tuple[1],
        'gt': value > tuple[1],
        'time_diff': time_diff == None or time_diff > tuple[1],
        'value_diff': value_diff == None or value_diff > tuple[1]
    }[tuple[0]]


def check_alert(alert, streamname, value):
    last_alert = alert.get('last_alert')
    if last_alert:
        time_diff = time.time() - last_alert['time']
        value_diff = value - last_alert['value']

    if _check_alert_part(alert['alert_when', value, time_diff, value_diff]):
        notifications = alert.get('notifications')
        for notification in notifications:
            _notify(notification, streamname, value)


def check_alerts(streamname, value):
    for alert in get_alerts(streamname):
        check_alert(alert, streamname, value)


def _get_notification_message(formatstring, streamname, value):
    return formatstring.replace('{streamname}', streamname).replace('{value}', value)


def _notify(notification, streamname, value):
    message = _get_notification_message(notification['message'], streamname, value)
    {
        'pushover': notifications.pushover
    }[notification['type']](message)


def set_min_alert(streamname, minval):
    db = get_db()
    alert = {
        'alert_when': ('and', [
            ('lt', minval),
            ('or', [('time_diff', 60000), ('value_diff', 2)])
        ]),
        'last_alert': {
            'time': None,
            'value': None
        },
        'notifications': [
            {
                'type': 'pushover',
                'message': '{streamname} temperature is below %s ({value})' % minval
            }

        ]
    }
    add_alert(streamname, alert)

def set_max_alert(streamname, maxval):
    db = get_db()
    alert = {
        'alert_when': ('and', [
            ('gt', maxval),
            ('or', [('time_diff', 60000), ('value_diff', 2)])
        ]),
        'last_alert': {
            'time': None,
            'value': None
        },
        'notifications': [
            {
                'type': 'pushover',
                'message': '{streamname} temperature is above %s ({value})' % maxval
            }

        ]
    }
    add_alert(streamname, alert)


def add_offset_alert(streamname, optimal, offset):
    set_min_alert(streamname, optimal - offset)
    set_max_alert(streamname, optimal + offset)



