import tellcore.telldus as td
import time
import datetime

import readings
import devices
import alerts

class EventManager():

    def __init__(self):
        self.core = td.TelldusCore()
        self.core.register_raw_device_event(self.parse_event)
        self.core.register_device_event(self.parse_device_event)
        self.core.register_sensor_event(self.parse_sensor_event)

        while True:
            self.handledevents = []
            self.core.callback_dispatcher.process_pending_callbacks()
            time.sleep(0.5)

    def already_handled(self, data):
        """Check if the given data string has already been handled"""
        if data in self.handledevents:
            return True
        self.handledevents.append(data)

        # Only keep most recent events
        self.handledevents = self.handledevents[-20:]
        return False
        
    def handle_sensor_event(self, values):
        print(values)
        sid = values.get("id")
        if sid:
            stream = readings.get_sensor_stream(sid)
            valuekeys = [k for k in values.keys() if k not in ["class", "model", "protocol", "id"]]
            for k in valuekeys:
                readings.insert_recent_reading(datetime.datetime.now(), sid, k, values[k])
                if stream:
                    readings.insert_reading(datetime.datetime.now(), stream, k, values[k])
   

    def handle_command_event(self, values):
        if values.get("protocol") == "arctech":
            print(values)
            house = values.get("house")
            unit = values.get("unit")
            group = values.get("group")
            method = values.get("method")

            device = devices.get_device(house, unit)

            if group == "0":
                if method == "turnon":
                    device.turn_on()
                elif method == "turnoff":
                    device.turn_off()
            else:
                if method == "turnon":
                    devices.turn_on_group(house)
                elif method == "turnoff":
                    devices.turn_off_group(house)

    def parse_event(self, data, controller_id, cid):

        if not self.already_handled(data):

            values = {}
            for d in data.split(";"):
                v = d.split(":")
                if len(v) == 2:
                    values[v[0]] = v[1]

            if values["class"] == "sensor":
                pass
#                self.handle_sensor_event(values)
            elif values["class"] == "command":
                print(data)
#                self.handle_command_event(values)

    def parse_device_event(self, _id, method, data, cid):
        print({"id": _id, "method": method, "data": data, "cid": cid})


    def parse_sensor_event(self, protocol, model, id_, dataType, value, timestamp, cid):
        if dataType == 1:
            dataType = "temp"
        elif dataType == 2:
            dataType = "humidity"
        else:
            return

        readings.insert_recent_reading(timestamp, id_, dataType, value)
        stream = readings.get_sensor_stream(id_)
        if stream:
            readings.insert_reading(timestamp, stream, dataType, value)
            if dataType == "temp":
                alerts.check_alert(stream, value)

if __name__ == "__main__":
    EventManager()
