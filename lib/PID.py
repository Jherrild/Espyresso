class PIDController(object):
    def __init__(self, p=2.0, i=0.0, d=1.0, set_temp=200, i_max=500, i_min=-500):
        self.kp = p
        self.ki = i
        self.kd = d
        self.set_point = set_temp
        self.i_max = i_max
        self.i_min = i_min

        self.dev = 0
        self.int = 0
        self.error = 0

    def set_temp(self, temp):
        self.set_point = temp
        self.dev = 0
        self.int = 0

    def set_kp(self, kp):
        self.kp = kp

    def set_ki(self, ki):
        self.ki = ki

    def set_kd(self, kd):
        self.kd = kd

    def update(self, current_temp):
        self.error = self.set_point - current_temp
        p_value = self.kp * self.error
        d_value = self.kd * (self.error - self.dev)
        self.dev = self.error
        self.int = self.int + self.error

        if self.int > self.i_max:
            self.int = self.i_max
        elif self.int < self.i_min:
            self.int = self.i_min

        i_value = self.int * self.ki

        output = p_value + i_value + d_value
        print(self.set_point)
        return output
