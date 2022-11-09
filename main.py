import machine
import math
import time
import mycelium
import mycelium.util

# use this LED for debugging
led = machine.Pin(2, machine.Pin.OUT)
touchpad = machine.TouchPad(machine.Pin(13))


class Node(mycelium.Node):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.touch = 1000
        self._touchpad_update = mycelium.util.Timer(100)

    def on_message(self, sender, data):
        # print("[received]", sender, data)
        if data['touch'] < 550:
            led.on()
        else:
            led.off()
    
    def update(self):
        # update the touchpad value
        if self._touchpad_update.expired:
            self.touch = touchpad.read()
            self.broadcast({"touch": self.touch})
            self._touchpad_update.reset()


def main():
    me = Node("mycelium", "mushroom-shibboleth", debug=True)
    perf_print_timer = mycelium.util.Timer(1000)

    loop_count = 0
    while True:
        me.communicate()
        me.update()
        loop_count += 1

        if perf_print_timer.expired:
            print(f"Network update rate: {loop_count}Hz")
            loop_count = 0
            perf_print_timer.reset()


if __name__ == '__main__':
    main()