import datetime
import time
import redis
import json
import random
from ConfigParser import SafeConfigParser

config = SafeConfigParser()
config.read('config.cfg')
DB_HOST = config.get('Redis', 'host')
DB = config.get('Redis', 'db')

def lock_key(key, db):
    ok = False
    id_ = random.randint(1000000,9999999)

    tries = 0
    while not ok:

        ok = db.setnx('lock:%s' % key, id_)
        if ok:
            id_ = db.get('lock:%s' % key)
            db.expire('lock:%s' % key, 10)
            return id_

        tries += 1
        if tries > 10:
            return False

        time.sleep(0.1)
    
    return id_


def unlock_key(key, value, db):
    cid = db.get('lock:%s' % key)
    if cid:
        if str(cid) == str(value):
            db.delete('lock:%s' % key)
            return True
        else:
            return False
    else:
        return True


def get_db():
    db = redis.StrictRedis(host=DB_HOST, db=DB)
    return db


def insert_reading(timestamp, streamname, type, value, db=None):
    if not db:
        db = get_db()

    time_ = datetime.datetime.utcfromtimestamp(timestamp)
    key = "%s:%s:%s" % (streamname, type, time_.date().strftime('%Y%m%d'))

    # Lock the key so we can update edit the json object and reinsert it safely.
    l_key = lock_key(key, db)
    if not l_key:
        print('ERROR: Could not lock key!')
        return

    try:
        doc = db.get(key)
        doc = json.loads(doc.decode())
    except:
        doc = None
    if not doc:
        doc = {}
        
    hour = doc.setdefault(str(time_.hour), {})
    hour[str(time_.minute)] = value
    print("%s %s:%s: %s" % (key, str(time_.hour), str(time_.minute), value))
    db.set(key, json.dumps(doc))
    unlock_key(key, l_key, db)

    db.set("current:%s:%s" % (streamname, type), value)


def insert_recent_reading(timestamp, sensor, type, value, db=None):
    if not db:
        db = get_db()

        time_ = datetime.datetime.utcfromtimestamp(timestamp)
        db.lpush('recent:%s' % str(sensor), '{"type":"%s", "value":"%s", "time":"%s"}' % (type, value, time_.strftime('%Y%m%d %H:%M')))
        db.ltrim('recent:%s' % str(sensor), 0, 10)


def get_sensor_stream(sid, db=None):
    if not db:
        db = get_db()

    stream = db.get("sensor:%s" % sid)
    if stream:
        return stream.decode()
    else:
        db.set("sensor:%s" % sid, "") 
        return ""
