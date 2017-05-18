import pyb
import micropython
import lib.onewire
from lib.ds18x20 import DS18X20

# Sensors
def get_temp(sensor):
    return sensor.read_temp_f()

# Callbacks
def adjust_set_up(p):
    global last_up
    if (last_up + 32) < pyb.millis():
        state['set_temp']=state['set_temp'] + 1
        last_up = pyb.millis()

def adjust_set_down(p):
    global last_down
    if (last_down + 32) < pyb.millis():
        state['set_temp']=state['set_temp'] + 1
        last_down = pyb.millis()

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

#Formatting
def format_temp(value, precision=0):
    return str(round(value, precision))+chr(247)

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
        state['boiler_temp'] = get_temp(self.sensor)
        if state['state'] != self.shot_switch.on:
            state['state'] = self.shot_switch.on
            state['start_time'] = pyb.millis()
        return dict(state,
                display={'width': self.display.width,
                         'height': self.display.height})

    def run(self):
        self.sensor = DS18X20(pyb.Pin('X12'))
        global last_up, last_down
        last_up = 0
        last_down = 0
        pyb.ExtInt(self.up_pin, pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_DOWN, adjust_set_up)
        pyb.ExtInt(self.down_pin, pyb.ExtInt.IRQ_FALLING, pyb.Pin.PULL_DOWN, adjust_set_down)

        while True:
            state = self._update_devices_info()
            state = self.controller(state)
            primitives = self.view(state)

            with self.display:
                self._draw(primitives)
            pyb.wfi()