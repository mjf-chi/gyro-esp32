import machine
import time
import gossip

led = machine.Pin(2, machine.Pin.OUT)

def update(data):
    print("Received message:", data)
    led.on()
    time.sleep_ms(150)
    led.off()

def main():
    net = gossip.Network("mycelium", "mushroom-shibboleth", update)
    while True:
        net.broadcast("hello")
        print("Gossiping...")
        net.gossip()
        time.sleep_ms(300)


if __name__ == '__main__':
    main()