from flask import Flask, jsonify
from tellcore import telldus

app = Flask(__name__)

# Method mappings from telldus api
# http://developer.telldus.com/doxygen/group__core.html#gaa732c3323e53d50e893c43492e5660c9
TELLSTICK_TURNON = 1
TELLSTICK_TURNOFF = 2
# TELLSTICK_BELL = 4
# TELLSTICK_TOGGLE = 8
# TELLSTICK_DIM = 16
# TELLSTICK_EXECUTE = 64
# TELLSTICK_UP = 128
# TELLSTICK_DOWN = 256
# TELLSTICK_STOP = 512
# TELLSTIC_ALL = 513


def _json_error(status_code, message):
    response = jsonify(message=message)
    response.status_code = status_code
    return response


def _get_devices():
    core = telldus.TelldusCore()
    return core.devices


def _get_device_status(device):
    v = device.get_last_command(TELLSTICK_TURNON | TELLSTICK_TURNOFF)
    try:
        return {
            1: 'on',
            2: 'off',
        }[v]
    except KeyError:
        return 'unkown'


@app.route("/devices/")
def list_devices():
    devices = _get_devices()

    ds = []
    for device in _get_devices():
        ds.append({
            'id': device.id,
            'name': device.name,
            'status': _get_device_status(device)
        })

    def _get_device_by_id(device_id):
        return next((x for x in devices if x.id == device_id), None)

    @app.route("/turnon/<int:device_id>")
    def turn_on(device_id):
        d = _get_device_by_id()
        if d:
            d.turn_on()
            return jsonify(message='Device was turned on')
        else:
            return _json_error(404, 'Device not found')

    @app.route("/turnoff/<int:device_id>")
    def turn_off(device_id):
        d = _get_device_by_id(device_id)
        if d:
            d.turn_off()
            return jsonify(message='Device was turned off')
        else:
            return _json_error(404, 'Device not found')

if __name__ == "__main__":
    app.run()
