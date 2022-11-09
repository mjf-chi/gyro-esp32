import time

def enum(**enums: int):
    return type('Enum', (), enums)


class Timer:

    def __init__(self, interval_ms):
        self.interval_ms = interval_ms
        self.reset()
    
    def reset(self):
        self.last_reset_ms = time.ticks_ms()
    
    @property
    def expired(self):
        return time.ticks_ms() >= (self.last_reset_ms + self.interval_ms)