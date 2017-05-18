import pyb

class Button(object):
    def __init__(self, pin):
        self._btn = pyb.Pin(pin, pyb.Pin.IN, pyb.Pin.PULL_UP)

    @property
    def clicked(self):
        return self._btn_one.value()

class Switch(object):
    def __init__(self, pin):
        self._switch = pyb.Pin(pin, pyb.Pin.IN, pyb.Pin.PULL_UP)

    @property
    def on(self):
        return self._switch.value()
