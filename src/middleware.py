"""Middleware to communicate with PubSub Message Broker."""
from collections.abc import Callable
from enum import Enum
from queue import LifoQueue, Empty
from typing import Any
from .PubSub import Protocol
import socket
import json, xml, pickle

class MiddlewareType(Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2


class Queue:
    """Representation of Queue interface for both Consumers and Producers."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        self.topic = topic
        self._type = _type
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection.connect(('localhost', 5000))

    def push(self, value):
        """Sends data to broker."""
        if self.type == "json":
            msg = Protocol.json(self.topic, value)
        elif self.type == "xml":
            msg = Protocol.xml(self.topic, value)
        elif self.type == "pickle":
            msg = Protocol.pickle(self.topic, value)
        Protocol.send(self.connection, Protocol.pub(msg))


    def pull(self) -> (str, Any):
        """Waits for (topic, data) from broker.
        Should BLOCK the consumer!"""
        msg = Protocol.recv(self.connection)
        if self.type == "json":
            msg = json.loads(msg)
        elif self.type == "xml":
            msg = Protocol.Decode(msg)
        elif self.type == "pickle":
            msg = pickle.loads(msg)

        return self.topic, msg["value"]
        

    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        if self.type == "json":
            msg = Protocol.json()
        elif self.type == "xml":
            msg = Protocol.xml()
        elif self.type == "pickle":
            msg = Protocol.pickle()

        Protocol.send(self.connection, Protocol.listall(msg))


    def cancel(self):
        """Cancel subscription."""
        if self.type == "json":
            msg = Protocol.json(self.topic)
        elif self.type == "xml":
            msg = Protocol.xml(self.topic)
        elif self.type == "pickle":
            msg = Protocol.pickle(self.topic)

        Protocol.send(self.connection, Protocol.unsub(msg))




class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""
    def __init__(self, topic, _type):
        self.type = "json"
        super().__init__(topic, _type=_type)
        Protocol.sendFirst(self.connection, "0")
        Protocol.send(self.connection, Protocol.sub(Protocol.json(topic)))


class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""
    def __init__(self, topic, _type):
        self.type = "xml"
        super().__init__(topic, _type=_type)
        Protocol.sendFirst(self.connection, "1")
        Protocol.send(self.connection, Protocol.sub(Protocol.xml(topic)))


class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""
    def __init__(self, topic, _type):
        self.type = "pickle"
        super().__init__(topic, _type=_type)
        Protocol.sendFirst(self.connection, "2")
        Protocol.send(self.connection, Protocol.sub(Protocol.pickle(topic)))