import machine
import time
import gyroscope
import neopixel
import leaf

GYRO_MAX_RATE = 500 # degrees per second
PIXELS = 3
DEFAULT_GYRO_DATA=(
  x = [255.0, 0.0],
  y = [255.0, 0.0],
  z = [255.0, 0.0]
)

def rate_to_color(max_dps, rate):
    return round((abs(rate) / max_dps) * 256)

def get_range(rng, new_val):
    return [
      min(rng[0], new_val),
      max(rng[1], new_val)
    ]

### If the gyro is static when the program starts we can set thresholds
### for when we want to assume interaction is occurring
def get_threshold_range(sample_func, default_data=DEFAULT_GYRO_DATA):
    threshold_range = copy(DEFAULT_GYRO_DATA)

    ### Sample 20 times over 5 seconds
    for i in range(0, 20):
        x, y, z = sample_func()

        threshold_range.x = get_range(threshold_range.x, x)
        threshold_range.y = get_range(threshold_range.y, y)
        threshold_range.z = get_range(threshold_range.z, z)

        time.sleep(0.25)

    return threshold_range

### Returns true if the value is beyond the threshold
def out_threshold(thresholds, sample_func):
    x, y, z = sample_func()

    def test(rng, v):
        return v < rng[0] || v > rng[1]

    return test(thresholds.x, x) || test(thresholds.y, y) || test(thresholds.z, z)


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

    print("Getting thresholds...")
    thresholds = get_threshold_range(gyro.sample)
    print("Thresholds set.", thresholds)

    print("Initializing LED strip...")
    leds = neopixel.NeoPixel(machine.Pin(21, machine.Pin.OUT), PIXELS, timing=1)
    print("Cool.")

    print("Growing Leaf...")
    leaf = leaf.Leaf(out_threshold, leds)
    print("Leaf ready.")

    ### Removed touch
    ### pad = machine.TouchPad(machine.Pin(4))

    leds.fill((255, 0, 0))
    leds.write()

    # led_idx = 0

    while True:
        leaf.update()
        # if led_idx >= PIXELS:
        #     led_idx = 0

        # dat_x, dat_y, dat_z = gyro.sample()
        # print("Data:", [dat_x, dat_y, dat_z])

        # x, y, z = [rate_to_color(GYRO_MAX_RATE, x) for x in [dat_x, dat_y, dat_z]]

        # leds[led_idx] = (x, y, z)
        # leds.write()

        # led_idx += 1

        # print("Touch pad reading:", pad.read())




if __name__ == '__main__':
    main()
