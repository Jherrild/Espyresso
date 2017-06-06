import pyb
import math
import time
import machine
import micropython
from Espyresso.lib.ssd1306 import Display
from Espyresso.lib.inputs import Switch
from Espyresso.lib.engine import Controller, rectangle, text, format_temp

micropython.alloc_emergency_exception_buf(100)
DEFAULT_SET_TEMP = 200
DEFAULT_STEAM_TEMP = 240
MAX_TEMP = 250

PUMP_ON = 1
PUMP_OFF = 0
SHOT = 1
STEAM = 0


# Views:
def main_screen(w, h, set_temp, current_temp):
    yield from text(x=0, y=0, string='Temp:', size=2)
    yield from text(x=60, y=0, string=current_temp, size=2)
    yield from text(x=0, y=30, string='Set:', size=3)
    yield from text(x=65, y=30, string=set_temp , size=3)


def shot_timer(w, h, t, current_temp):
    yield from text(x=0, y=0, string='Temp:', size=2)
    yield from text(x=60, y=0, string=current_temp, size=2)
    yield from text(x=0, y=30, string='Time:', size=3)
    yield from text(x=80, y=30, string=t , size=3)


def view(state):
    if state['state'] == PUMP_ON:
        yield from shot_timer(w=state['display']['width'],
                              h=state['display']['height'],
                              t=str(round((pyb.elapsed_millis(state['start_time'])) / 1000)),
                              current_temp=format_temp(state['boiler_temp'], 1))
    else:
        if state['mode'] == SHOT:
            yield from main_screen(w=state['display']['width'],
                                   h=state['display']['height'],
                                   set_temp=format_temp(state['set_temp'], 0),
                                   current_temp=format_temp(state['boiler_temp'], 1))
        else:
            yield from main_screen(w=state['display']['width'],
                                   h=state['display']['height'],
                                   set_temp=format_temp(state['steam_temp'], 0),
                                   current_temp=format_temp(state['boiler_temp'], 1))


def controller(state):
    if state['state'] == PUMP_OFF:
        state['state'] = PUMP_OFF
    elif state['state'] == PUMP_ON:
        state['state'] = PUMP_ON
    state.update()
    return state


pid_controller = Controller(display=Display(pinout={'sda': 'Y10',
                                                    'scl': 'Y9'},
                                            height=64,
                                            external_vcc=False),
                            initial_state={'state': PUMP_OFF,
                                           'mode': SHOT,
                                           'start_time': pyb.millis(),
                                           'set_temp': DEFAULT_SET_TEMP,
                                           'steam_temp': DEFAULT_STEAM_TEMP,
                                           'max_temp': MAX_TEMP,
                                           'boiler_temp': 0},
                            view=view,
                            controller=controller,
                            up_pin='X9',
                            down_pin='X10',
                            shot_switch=Switch('X11'),
                            steam_switch=Switch('Y8'))


if __name__ == '__main__':
    pid_controller.run()
