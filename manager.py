import tellcore.telldus as td
import time
import datetime
import logging
import redis
import trollius

import readings
import devices
import alerts

class EventManager():

    def __init__(self):
        
        logging.basicConfig(filename='/home/pi/logs/EventManager.log', level=logging.INFO)
        logging.info('Initialzing...')
        
        loop = trollius.get_event_loop()
        dispatcher = td.AsyncioCallbackDispatcher(loop)
        self.core = td.TelldusCore(callback_dispatcher=dispatcher)
#        self.core.register_raw_device_event(self.parse_event)
        self.core.register_device_event(self.parse_device_event)
        self.core.register_sensor_event(self.parse_sensor_event)

        logging.info('Initialized. Starting listener loop')
        
        loop.run_forever()
#        while True:
#            self.handledevents = []
#            self.core.callback_dispatcher.process_pending_callbacks()
#            time.sleep(0.5)

    def already_handled(self, data):
        """Check if the given data string has already been handled"""
        if data in self.handledevents:
            return True
        self.handledevents.append(data)
        self.handledevents = self.handledevents[-20:]

        return False
        

    def parse_device_event(self, _id, method, data, cid):
        for d in self.core.devices():
            logging.info(d.id)
        logging.info({"id": _id, "method": method, "data": data, "cid": cid})


    def parse_sensor_event(self, protocol, model, id_, dataType, value, timestamp, cid):
        if dataType == 1:
            dataType = "temp"
        elif dataType == 2:
            dataType = "humidity"
        else:
            return


        logging.info('Got reading %s (%s)' % (value, dataType))
        try:
            readings.insert_recent_reading(timestamp, id_, dataType, value)
            stream = readings.get_sensor_stream(id_)
            if stream:
                logging.info('Stream: %s' % stream)
                readings.insert_reading(timestamp, stream, dataType, value)
                if dataType == "temp":
                    alerts.check_alerts(stream, value)
        except redis.exceptions.ConnectionError:
            logging.warning('Could not connect to Redis. Falling back to writing to readings.txt')
            with open('/home/pi/data/readings.txt', 'a') as f:
                f.write('%s,%s,%s,%s\n' % (timestamp, id_, dataType, value))

if __name__ == "__main__":
    EventManager()
