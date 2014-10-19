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
    db = get_db()
    alertsstr = db.get('alerts:%s' % streamname)
    if alertsstr:
       return json.loads(alertsstr)
    else:
       return []


def set_alerts(streamname, alerts):
    db = get_db()
    db.set('alerts:%s' % streamname, json.dumps(alerts))


def add_alert(streamname, alert):
    db = get_db()
    alerts = get_alerts(streamname)
    alerts.append(alert)
    set_alerts(streamname, alerts)


def _check_alert_part(tuple, value, time_diff, value_diff):
    r = {
        'or': lambda:any([_check_alert_part(t, value, time_diff, value_diff) for t in tuple[1]]),
        'and': lambda:all([_check_alert_part(t, value, time_diff, value_diff) for t in tuple[1]]),
        'lt': lambda:value < tuple[1],
        'gt': lambda:value > tuple[1],
        'time_diff': lambda:time_diff == None or time_diff > tuple[1],
        'value_diff': lambda:value_diff == None or value_diff > tuple[1]
    }[tuple[0]]()
    return r


def check_alert(alert, streamname, value):
    value = float(value)
    last_alert = alert.get('last_alert')
    time_diff = None
    value_diff = None
    if last_alert.get('time') and last_alert.get('value'):
        time_diff = time.time() - last_alert['time']
        value_diff = value - last_alert['value']

    if _check_alert_part(alert['alert_when'], value, time_diff, value_diff):
        print 'alerting'
        alert['last_alert'] = {'time': time.time(), 'value': value}
        notifications = alert.get('notifications')
        for notification in notifications:
            _notify(notification, streamname, value)


def check_alerts(streamname, value):
    alerts = get_alerts(streamname)
    for alert in alerts:
        check_alert(alert, streamname, value)
    set_alerts(streamname, alerts)


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



