import machine
import time
import gyroscope
import neopixel

GYRO_MAX_RATE = 500 # degrees per second
PIXELS = 3


def rate_to_color(max_dps, rate):
    return round((abs(rate) / max_dps) * 256)

def main():
    # set up peripherals
    sys_led = machine.Pin(2, machine.Pin.OUT)
    print("Instantiated sys led...")

    i2c_bus = machine.SoftI2C(scl=machine.Pin(18), sda=machine.Pin(19), freq=400_000)
    print("Instantiated I2C bus...")
    print(i2c_bus.scan())

    print("Initializing gyro...")
    gyro = gyroscope.L3GD20(i2c_bus, gyroscope.L3GD20.RANGE_500DPS)
    print("Gyro initialized.", gyro)

    print("Initializing LED strip...")
    leds = neopixel.NeoPixel(machine.Pin(21, machine.Pin.OUT), PIXELS, timing=1)
    print("Cool.")

    pad = machine.TouchPad(machine.Pin(4))

    leds.fill((255, 0, 0))
    leds.write()

    led_idx = 0
    while True:
        if led_idx >= PIXELS:
            led_idx = 0
        
        x, y, z = [rate_to_color(GYRO_MAX_RATE, x) for x in gyro.sample()]

        leds[led_idx] = (x, y, z)
        leds.write()
         
        led_idx += 1

        print("Touch pad reading:", pad.read())




if __name__ == '__main__':
    main()