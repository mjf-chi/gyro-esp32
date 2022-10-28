upload:
	rshell -p /dev/tty.usbserial-0001 cp main.py /pyboard/main.py
	rshell -p /dev/tty.usbserial-0001 cp gossip.py /pyboard/gossip.py
	rshell -p /dev/tty.usbserial-0001 cp util.py /pyboard/util.py

console:
	screen /dev/tty.usbserial-0001 115200