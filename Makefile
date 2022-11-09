upload:
	@for f in $(shell ls /dev/tty.usbserial*); do \
		echo ">>> Uploading to $${f}..."; \
		rshell -p $${f} rsync -m mycelium/ /pyboard/mycelium/; \
		rshell -p $${f} cp main.py /pyboard/main.py; \
	done;

console:
	screen /dev/tty.usbserial-0001 115200