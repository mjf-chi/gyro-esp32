import machine
import time
import gyroscope
import neopixel
import leaf

GYRO_MAX_RATE = 500 # degrees per second
PIXELS = 3
DEFAULT_GYRO_DATA={'x':[255.0, 0.0], 'y':[255.0, 0.0], 'z':[255.0, 0.0]}

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
    threshold_range = DEFAULT_GYRO_DATA.copy()

    ### Values tend to be sporadic for the first moments
    print('Waiting to settle down...')
    time.sleep(4)

    print('Beginning threshold test')
    ### Sample 20 times over 5 seconds
    for i in range(0, 20):
        x, y, z = sample_func()
        print(f'Sample {i}: {x}, {y} , {z}')

        threshold_range['x'] = get_range(threshold_range['x'], x)
        threshold_range['y'] = get_range(threshold_range['y'], y)
        threshold_range['z'] = get_range(threshold_range['z'], z)

        time.sleep(0.25)

    return threshold_range

def build_threshold_func(thresholds, sample_func):
    def test(rng, v):
        return v < rng[0] or v > rng[1]

    def hasAttention():
        x, y, z = sample_func()
        print(f'Sample: {x}, {y} , {z}')

        if test(thresholds['x'], x):
          print('X outside threshold ', thresholds['x'])
          return True
        elif test(thresholds['y'], y):
          print('Y outside threshold ', thresholds['y'])
          return True
        elif test(thresholds['z'], z):
          print('Z outside threshold ', thresholds['z'])
          return True

        return False

        #return test(thresholds['x'], x) or test(thresholds['y'], y) or test(thresholds['z'], z)

    return hasAttention


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

    attentionFunc = build_threshold_func(thresholds, gyro.sample)

    print("Growing Leaf...")
    foliage = leaf.Leaf(attentionFunc, leds)
    print("Leaf ready.")

    ### Removed touch
    ### pad = machine.TouchPad(machine.Pin(4))

    leds.fill((255, 0, 0))
    leds.write()

    # led_idx = 0

    while True:
        foliage.update()
        # if led_idx >= PIXELS:
        #     led_idx = 0

        # dat_x, dat_y, dat_z = gyro.sample()
        # print("Data:", [dat_x, dat_y, dat_z])

        # x, y, z = [rate_to_color(GYRO_MAX_RATE, x) for x in [dat_x, dat_y, dat_z]]

        # leds[led_idx] = (x, y, z)
        # leds.write()

        # led_idx += 1

        # print("Touch pad reading:", pad.read())

        time.sleep(0.5)



if __name__ == '__main__':
    main()
