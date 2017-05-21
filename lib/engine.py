import pyb
import micropython
import Espyresso.lib.onewire
from Espyresso.lib.ds18x20 import DS18X20

#Formatting
def format_temp(value, precision=0):
    return str(round(value, precision))+chr(247)

# Sensors/Sensor functions
def get_temp(sensor):
    try:
        return sensor.read_temp_f()
    except IndexError:
        return "No Sensor"

#Debounce logic
def debounce(last, wait):
    return (last + wait) < pyb.millis()

# Callback functions
def adjust_set_up(p):
    global last_up, temp_changed
    if debounce(last_up, 200):
        state['set_temp']=state['set_temp'] + 1
        last_up = pyb.millis()
        temp_changed = True

def adjust_set_down(p):
    global last_down, temp_changed
    if debounce(last_down, 200):
        state['set_temp']=state['set_temp'] - 1
        last_down = pyb.millis()
        temp_changed = True

# TODO: Run on timer interrupt to periodically backup settings
def save_settings():
    global temp_changed, last_saved
    if temp_changed:
        settings_file = open('/sd/dat/settings.dat', 'w')
        settings_file.write("set_temp " + str(state['set_temp']))
        #TODO: Add steam temp
        settings_file.close()
        temp_changed = False
        last_saved = pyb.millis()
        print("Settings saved")


def restore_settings():
    with open('/sd/dat/settings.dat', 'r') as file:
        settings = [line.strip('\n') for line in file.readlines()]

    for property in settings:
        print("\tLoading property: " + property)
        restore_setting(property)

    return

def restore_setting(property):
    pair = property.split()
    if len(pair) == 2:
        state[str(pair[0])] = int(pair[1])
    return

# Primitives:
class Point(object):
    def __init__(self, x, y, fill):
        self.x = int(x)
        self.y = int(y)
        self.fill = bool(fill)

    def draw(self, display):
        display.set_pixel(self.x, self.y, self.fill)

    def translate(self, x, y):
        return Point(x + self.x, y + self.y, self.fill)

class Text(object):
    def __init__(self, x, y, string, size=1, space=1):
        self.x = x
        self.y = y
        self.string = string
        self.size = size
        self.space = space

    def draw(self, display):
        display.draw_text(self.x, self.y, self.string, self.size, self.space)

    def translate(self, x, y):
        return Text(x + self.x, y + self.y, self.string, self.size, self.space)

def relative(fn):
    def wrapper(x, y, *args, **kwargs):
        for primitive in fn(*args, **kwargs):
            yield primitive.translate(x, y)

    return wrapper

# Components:
@relative
def rectangle(w, h, fill):
    for x in range(w):
        for y in range(h):
            yield Point(x, y, fill)

def point(x, y, fill):
    yield Point(x, y, fill)

def text(x, y, string, size=1, space=1):
    yield Text(x, y, string, size, space)

class Controller(object):
    def __init__(self, display, initial_state, controller, view, up_pin, down_pin, shot_switch, steam_switch):
        global state
        state = initial_state
        self.display = display
        self.controller = controller
        self.view = view
        self.up_pin = up_pin
        self.down_pin = down_pin
        self.shot_switch = shot_switch
        self.steam_switch = steam_switch

    def _draw(self, primitives):
        for primitive in primitives:
            primitive.draw(self.display)

    def _update_devices_info(self):
        print("_update_device_info")
        state['boiler_temp'] = get_temp(self.sensor)
        if state['state'] != self.shot_switch.on:
            state['state'] = self.shot_switch.on
            state['start_time'] = pyb.millis()
        return dict(state,
                display={'width': self.display.width,
                         'height': self.display.height})

    def run(self):
        global last_up, last_down, last_saved, temp_changed
        last_up = pyb.millis()
        last_down = last_up
        last_saved = last_up
        temp_changed = False

        restore_settings()
        self.sensor = DS18X20(pyb.Pin('X12'))
        pyb.ExtInt(self.up_pin, pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_DOWN, adjust_set_up)
        pyb.ExtInt(self.down_pin, pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_DOWN, adjust_set_down)

        while True:
            state = self._update_devices_info()
            state = self.controller(state)
            primitives = self.view(state)

            if debounce(last_saved, 6000):
                save_settings()

            with self.display:
                self._draw(primitives)
            #pyb.wfi()
