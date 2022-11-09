import json
import time


class NodeHandle:

    def __init__(self, net, addr):
        self._net = net
        self._addr = addr
        self._last_msg_t = None
        self._msg_count = None
        self._bytes_received = 0
    
    def _send_raw(self, data):
        try:
            self._net._sock.sendto(data, self._addr)
            return True
        except:
            return False
    
    def _send_control(self, typ, data):
        return self._send_raw(json.dumps({"type": typ, "data": data}))

    def _msg_received(self, length):
        self._last_msg_t = time.ticks_ms()
        self._bytes_received += length

    def send_msg(self, msg):
        """
        Send a message to this peer. msg may be any JSON-serializable object 
        less than Network. in size after serialization. Returns false if an 
        error occurs during transmission.
        """
        return self._send_control("msg", msg)

    @property
    def identifier(self):
        """
        An identifier that can be used to refer to this peer in the future.
        """
        return self._addr[0]

    @property
    def address(self):
        """
        Return the network IP address and messaging port as a tuple in the form 
        (str(address), int(port)).
        """
        return self._addr
    
    @property
    def stats(self):
        """
        Retrieve statistics about communication with this peer as a tuple 
        containing the number of messages received from the peer, total number 
        of bytes received, and the number of millisecond ticks at which the 
        last message was received.
        """
        return (self._msg_count, self._bytes_received, self._last_msg_t)

    def __repr__(self):
        return f"<Node({self.identifier})>"