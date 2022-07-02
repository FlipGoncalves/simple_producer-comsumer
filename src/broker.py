"""Message Broker"""
import enum
from typing import Dict, List, Any, Tuple
import socket
import json, pickle, xml
from .PubSub import Protocol
import selectors

class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2


class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""
        self.canceled = False
        self._host = "localhost"
        self._port = 5000
        self.topics = {}
        self.subscribed = {}
        self.connecs = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self._host, self._port))
        self.sock.listen(100)
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)

    def list_topics(self) -> List[str]:
        """Returns a list of strings containing all topics."""
        return list(self.topics.keys())

    def get_topic(self, topic):
        """Returns the currently stored value in topic."""
        for tp in self.topics.keys():
            if topic.startswith(tp):
                if len(self.topics[topic]) != 0:
                    return self.topics[topic][-1]

        return None

    def put_topic(self, topic, value):
        """Store in topic the value."""
        if topic not in self.topics.keys():
            if value is None:
                self.topics[topic] = []
            else:
                self.topics[topic] = [value]
        else:
            if not value is None:
                self.topics[topic].append(value)

    def list_subscriptions(self, topic: str) -> List[socket.socket]:
        """Provide list of subscribers to a given topic."""
        sub_list = []
        for x in self.subscribed.keys():
            if x in topic:
                for client in self.subscribed[x]:
                    sub_list.append(client)
        return sub_list

    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        """Subscribe to topic by client in address."""
        if topic in self.subscribed.keys():
            if (address, _format) not in self.subscribed[topic]:
                self.subscribed[topic].append((address, _format))
        else: 
            self.subscribed[topic] = [(address, _format)]

    def unsubscribe(self, topic, address):
        """Unsubscribe to topic by client in address."""
        if topic in self.subscribed.keys():
            count = 0
            for x in self.subscribed[topic]:
                if address in x:
                    self.subscribed[topic].pop(count)
                count += 1

    def accept(self, sock, mask):
        conn, addr = sock.accept()
        self.connecs[conn] = int(Protocol.recv(conn))
        self.sel.register(conn, selectors.EVENT_READ, self.recv)

    def recv(self, conn, mask):
        msg = Protocol.recv(conn)
        if not msg:
            return None
        
        if self.connecs[conn] == 0:
            msg_dec = json.loads(msg)
        elif self.connecs[conn] == 2:
            msg_dec = pickle.loads(msg)
        elif self.connecs[conn] == 1:
            msg_dec = Protocol.Decode(msg)

        if msg_dec["command"] == "pub":
            self.put_topic(msg_dec["topic"], msg_dec["value"])
            self.broadcast(msg_dec["topic"], msg_dec["value"])
        elif msg_dec["command"] == "subscribe":
            self.subscribe(msg_dec["topic"], conn, self.connecs[conn])
            if self.get_topic(msg_dec["topic"]):
                get = self.get_topic(msg_dec["topic"])
                if self.connecs[conn] == 0:
                    Protocol.send(conn, Protocol.pub(Protocol.json(msg_dec["topic"], get)))
                elif self.connecs[conn] == 2:
                    Protocol.send(conn, Protocol.pub(Protocol.pickle(msg_dec["topic"], get)))
                elif self.connecs[conn] == 1:
                    Protocol.send(conn, Protocol.pub(Protocol.xml(msg_dec["topic"], get)))
        elif msg_dec["command"] == "unsubscribe":
            self.unsubscribe(msg_dec["topic"], conn)
        elif msg_dec["command"] == "listall":
            subs = self.list_subscriptions()
            if self.connecs[conn] == 0:
                Protocol.send(conn, Protocol.json(subs))
            elif self.connecs[conn] == 2:
                Protocol.send(conn, Protocol.pickle(subs))
            elif self.connecs[conn] == 1:
                Protocol.send(conn, Protocol.xml(subs))

    def broadcast(self, topic, value):
        for client in self.list_subscriptions(topic):
            if client[1] == 0:
                Protocol.send(client[0], Protocol.pub(Protocol.json(topic, value)))
            if client[1] == 2:
                Protocol.send(client[0], Protocol.pub(Protocol.pickle(topic, value)))
            if client[1] == 1:
                Protocol.send(client[0], Protocol.pub(Protocol.xml(topic, value)))

    def run(self):
        """Run until canceled."""
        while not self.canceled:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
                