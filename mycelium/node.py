from .node_handle import NodeHandle
from .network import Network


class Node(NodeHandle):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Node, cls).__new__(cls)
        return cls.instance

    def __init__(self, ssid, password, debug=False):
        net = Network(ssid, password, debug)
        net._handler = self.on_message
        super().__init__(net, net.address)
    
    def on_message(self, sender, data):
        raise NotImplementedError("no on_message method implemented for Node subclass")

    def send_msg(self, msg):
        raise Exception("cannot send a message to yourself")
    
    @property
    def peers(self):
        return self._net.peers
    
    def broadcast(self, obj):
        self._net.broadcast(obj)
    
    def communicate(self):
        self._net.communicate()