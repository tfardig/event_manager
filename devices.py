import redis
import json

def get_redis_db():
    return redis.StrictRedis(host='192.168.1.6', port=6379, db=0)

class Device():


    def __init__(self, house, unit, status='-', name=''):
        self.house = house
        self.unit = unit
        self.status = status
        self.name = name
        

    def _save(self):
        db = get_redis_db()

        dev = {"house":self.house, "unit": self.unit, "status": self.status, "name": self.name}
        db.set('device:%s:%s' % (self.house, self.unit), json.dumps(dev))
        
        
    def _set_status(self, status):
        self.status = status
        self._save()


    def turn_off(self):
        self._set_status('off')


    def turn_on(self):
        self._set_status('on')


    def rename(self, name):
        self.name = name
        self._save()


def get_device(house, unit, db=None):
    db = get_redis_db()

    key = 'device:%s:%s' % (house, unit)
    k = db.keys(key)
    if k:
        raw = db.get(key)
        dev = json.loads(raw.decode())
        device = Device(house, unit, dev['status'], dev['name'])
    else:
        device = Device(house, unit)
    
    return device


def turn_on_group(house):
    _set_group(house, 'on')


def turn_off_group(house):
    _set_group(house, 'off')


def _set_group(house, status):
    db = get_redis_db()

    keys = db.keys('device:%s*' % house)
    for key in keys:
        raw = db.get(key)
        dev = json.loads(raw.decode())
        device = Device(house, dev['unit'], dev['status'], dev['name'])
        device._set_status(status)

        
        
