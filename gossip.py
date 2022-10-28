from micropython import const
import random
import time
import socket
import ubinascii
import machine
import json

import util
import network


class Peer:

    def __init__(self, net, addr):
        self._net = net
        self._addr = addr
        self._last_msg_t = None
        self._msg_count = None
    
    def _send_raw(self, data):
        try:
            self._net._sock.sendto(data, self._addr)
            return True
        except:
            return False
    
    def _send_control(self, typ, data):
        return self._send_raw(json.dumps({"type": typ, "data": data}))

    def send_msg(self, msg):
        return self._send_control("msg", msg)

    def _msg_received(self):
        self._last_msg_t = time.ticks_ms()

    @property
    def identifier(self):
        return self._addr[0]

    @property
    def address(self):
        return self._addr

    def __repr__(self):
        return f"<Peer({self.identifier})>"


class Network:

    Roles = util.enum(
        FOLLOWER = const(0),
        LEADER = const(1),
    )

    PORT = 8990
    DEBUG = True
    DISCOVER_NET_TIMEOUT = (2, 5) # (min, max) seconds
    PEER_TIMEOUT = 30 * 1000 # 30 seconds in ms
    HEARTBEAT_INTERVAL = 1000 # ms

    def _log(self, *args):
        if self.DEBUG:
            print(f"{time.ticks_ms()} [Network]", *args)

    def __init__(self, net_ssid, net_pass, handler):
        self._net_ssid = net_ssid
        self._net_pass = net_pass
        self._handler = handler
        self._last_heartbeat_t = None
        self._leader = None
        self._peers = {}
        
        # attempt to scan to find the network; otherwise create one
        self._log("Starting peer network discovery...")
        self._is_leader, self._net = self.peer_network()
        
        if not self._is_leader:
            self._leader = Peer(self, ("192.168.0.1", self.PORT))

        # self-assign an address, hopefully non-conflicting
        self._addr = "192.168.0.1" if self._is_leader else f"192.168.0.{random.randrange(2, 254)}"
        
        self._log(f"Joining '{self._net_ssid}' as", self._addr)
        self._net.ifconfig((self._addr, "255.255.255.0", "192.168.0.1", self._addr))

        # open the message receive port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self._addr, self.PORT))
        self._log(f"Started listening for UDP on {self._addr}:{self.PORT}.")

    @property
    def leader(self):
        return self._leader
    
    @property
    def is_leader(self):
        return self._is_leader

    def peer_network(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        # wait some random amount of time (<30s) to see if we can find a network
        # that matches the gossip network we wish to join
        t_start = time.time()
        t_timeout = t_start + random.randrange(*self.DISCOVER_NET_TIMEOUT)
        self._log(f"Started discovery at {t_start}; running until {t_timeout}.")
        while time.time() < t_timeout:
            for n in wlan.scan():
                if n[0].decode() != self._net_ssid:
                    continue
                # we found a network to join!
                wlan.connect(self._net_ssid, self._net_pass)
                while not wlan.isconnected() and time.time() < t_timeout:
                    pass
                return (False, wlan)
        
        self._log(f"Failed to discover existing SSID; creating one.")

        # we failed to find an existing network, so turn off wifi and get ready 
        # to reenable so we can create our own
        wlan.active(False)
        
        # create our own network
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=self._net_ssid,
                  authmode=network.AUTH_WPA_WPA2_PSK,
                  password=self._net_pass)
        self._log(f"Entered AP mode. SSID created.")

        return (True, ap)
    
    def broadcast(self, data):
        """
        Send a message to all peers (including yourself, if you're the leader!)
        """
        for peer in self._peers.values():
            if not peer.send_msg(data):
                self._peers.pop(peer.address)

    def _update_peers(self, msg):
        for addr, port in msg['data']['peers']:
            if addr not in self._peers:
                self._peers[addr] = Peer(self, addr)
        peer_addrs = [a[0] for a in msg['data']['peers']]
        for addr in self._peers:
            if addr not in peer_addrs:
                self._peers.pop(addr)

    def gossip(self):
        # TODO(KK): add polling

        if not self.is_leader:
            if self._last_heartbeat_t is None \
                or self._last_heartbeat_t < (time.ticks_ms() - self.HEARTBEAT_INTERVAL):
                self.leader._send_control("heartbeat", None)

        # receive a packet from another node on the network
        data, addr = self._sock.recvfrom(1024)

        # if the packet comes from a node we don't yet recognize, add a peer
        sender = None
        if addr[0] not in self._peers:
            sender = Peer(self, addr)
            self._peers[sender.identifier] = peer

        # update the last time we received a message from the peer
        sender._msg_received()

        # if we are the leader, we're responsible for some additional work
        if self.is_leader:
            # remove all peers from whom we haven't seen a message in longer 
            # than PEER_TIMEOUT
            for peer in self._peers.values():
                thresh = time.ticks_ms() - self.PEER_TIMEOUT
                if peer._last_msg_t < thresh:
                    self._log("Pruning peer:", peer)
                    self._peers.pop(peer.identifier)

            # notify all peers of the current peer list
            msg = {
                "type": "peer_update",
                "peers": [p.address for p in self._peers.values()],
            }
            for peer in self._peers.values():
                peer.send(msg)
        
        # unpack the message and handle it
        msg = json.loads(data)
        if msg['type'] == 'peer_update':
            # update our peer set
            self._update_peers(msg)
        elif msg['type'] == 'msg':
            # dispatch to our message handler
            self._handler(data)
        else:
            self._log("Unhandled message type from peer", peer, msg)