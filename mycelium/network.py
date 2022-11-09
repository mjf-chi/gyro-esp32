from micropython import const
import random
import time
import socket
import json
import network
import select

from . import util
from .node_handle import NodeHandle


class Network:
    PORT = 8990
    DISCOVER_NET_TIMEOUT = (2000, 5000) # (min, max) milliseconds
    PEER_TIMEOUT = 30 * 1000 # 30 seconds in ms
    HEARTBEAT_INTERVAL = 1000 # ms
    MSG_MAX_BYTES = 1024 # bytes; fits in a single MTU

    def __init__(self, net_ssid, net_pass, debug=False):
        self._debug = debug
        self._net_ssid = net_ssid
        self._net_pass = net_pass
        self._last_heartbeat_t = None
        self._leader = None
        self._addr = None
        self._peers = {}
        self._is_leader = False
        
        self._timer_heartbeat = util.Timer(self.HEARTBEAT_INTERVAL)
        self._timer_peer_update = util.Timer(self.HEARTBEAT_INTERVAL)

        # attempt to scan to find the network; otherwise create one
        self._log("Initializing network...")
        self._is_leader, self._net = self._connect_net()
        
        if not self._is_leader:
            self._leader = NodeHandle(self, ("192.168.0.1", self.PORT))
            self._peers[self._leader.address[0]] = self._leader
        
        self._log(f"Assuming network address: {self.address}")
        self._net.ifconfig((self.address[0], "255.255.255.0", "192.168.0.1", self.address[0]))

        # open the message receive port
        self._poller = select.poll()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(self.address)
        self._poller.register(self._sock, select.POLLIN)
        self._log(f"Started listening for UDP on {self.address}.")

    @property
    def address(self):
        if self.is_leader:
            return ("192.168.0.1", self.PORT)
        if self._addr is None:
            # self-assign an address, hopefully non-conflicting /shrug
            self._addr = (f"192.168.0.{random.randrange(2, 254)}", self.PORT)
        return self._addr

    @property
    def leader(self):
        return self._leader

    @property
    def is_leader(self):
        return self._is_leader

    @property
    def peers(self):
        return self._peers

    def broadcast(self, data):
        """
        Send a message to all peers.
        """
        for peer in self._peers.values():
            if not peer.send_msg(data):
                self._peers.pop(peer.address[0])

    def communicate(self):
        # send a heartbeat to the leader
        if not self.is_leader and self._timer_heartbeat.expired:
            self._log("Sending heartbeat to leader", self.leader)
            self.leader._send_control("heartbeat", None)
            self._timer_heartbeat.reset()

        # if the inbound socket is ready to be read, handle a packet
        if self._poller.poll(0):
            data, addr = self._sock.recvfrom(self.MSG_MAX_BYTES)
            self._handle_packet(addr, data)

        # if we are the leader, we're responsible for some additional work
        if self.is_leader:
            self._leader_manage_peers()

    def _log(self, *args):
        if self._debug:
            flag = "(L)" if self.is_leader else ""
            print(f"{time.ticks_ms()} [Network{flag}]", *args)

    def _connect_net(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        # wait some random amount of time (<30s) to see if we can find a network
        # that matches the gossip network we wish to join
        t_start = time.ticks_ms()
        timeout = util.Timer(random.randrange(*self.DISCOVER_NET_TIMEOUT))
        self._log(f"Searching for gossip network (timeout after {timeout.interval_ms}ms)...")
        while not timeout.expired:
            for n in wlan.scan():
                if n[0].decode() != self._net_ssid:
                    continue
                # we found a network to join!
                wlan.connect(self._net_ssid, self._net_pass)
                while not wlan.isconnected() and not timeout.expired:
                    pass
                return (False, wlan)
        
        # we couldn't find a network to join; homemade is fine
        self._log(f"Failed to discover existing SSID; creating one as leader.")
        wlan.active(False)
        
        # create our own network
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=self._net_ssid,
                  authmode=network.AUTH_WPA_WPA2_PSK,
                  password=self._net_pass)
        self._log(f"Entered AP mode. Broadcasting ESSID {self._net_ssid}.")

        return (True, ap)


    def _broadcast_control(self, typ, data):
        for peer in self._peers.values():
            if not peer._send_control(typ, data):
                self._peers.pop(peer.address)

    def _update_peers(self, msg):
        for addr, port in msg['data']['peers']:
            if addr not in self._peers and addr != self.address[0]:
                self._peers[addr] = NodeHandle(self, (addr, port))
        peer_addrs = [a[0] for a in msg['data']['peers']]
        for addr in self._peers:
            if addr not in peer_addrs and addr != self.leader.address[0]:
                self._peers.pop(addr)
        self._log("Peers updated to:", self._peers)

    def _handle_packet(self, addr, data):
        # if the packet comes from a node we don't yet recognize, add a peer
        sender = None
        if addr[0] not in self._peers:
            sender = NodeHandle(self, addr)
            self._log("Packet from new node. Adding to peers.", sender)
            self._peers[sender.identifier] = sender
        else:
            sender = self._peers[addr[0]]
        sender._msg_received(len(data))
        
        # unpack the message and handle it
        msg = json.loads(data)
        if msg['type'] == 'peer_update':
            # if we're a follower, update list of peers
            if self.is_leader:
                raise Exception("peer_update received from follower", sender)
            self._update_peers(msg)
        elif msg['type'] == 'heartbeat':
            self._log("Received heartbeat from peer", sender)
        elif msg['type'] == 'msg':
            # dispatch to our message handler
            self._handler(sender, msg['data'])
        else:
            self._log("Unhandled message type from peer", sender, msg)
        
        # return the peer from which the packet was received
        return sender

    def _leader_manage_peers(self):
        # remove all peers from whom we haven't seen a message in longer 
        # than PEER_TIMEOUT
        peers_changed = False
        for peer in self._peers.values():
            thresh = (time.ticks_ms() + self.PEER_TIMEOUT + (self.PEER_TIMEOUT * 0.2))
            if peer._last_msg_t > thresh:
                peers_changed = True
                self._log("Pruning peer:", peer)
                self._peers.pop(peer.identifier)
        
        if self._timer_peer_update.expired or peers_changed:
            # notify all peers of the current peer list
            self._log("Broadcasting peer update:", self._peers)
            self._broadcast_control("peer_update", {
                'peers': [p.address for p in self._peers.values()]
            })
            self._timer_peer_update.reset()