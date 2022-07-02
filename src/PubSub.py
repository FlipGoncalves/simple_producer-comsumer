"""Protocol Publisher/Subscriber"""

import json, pickle, xml
import xml.etree.ElementTree as ET
from socket import socket

class Message:
    """PubSub Protocol"""
    def __init__(self):
        pass

class JsonMessage(Message):
    def __init__(self, topic = None, value = None):			#this will be the format of a Json message object
        self.type = 'Json'						# all of the objects will have a type, which indicates the type of message for easier management
        self.topic = topic
        self.value = value
        super().__init__()

class XmlMessage(Message):
    def __init__(self, topic = None, value = None):
        self.type = 'Xml'
        self.topic = topic
        self.value = value
        super().__init__()

class PickleMessage(Message):
    def __init__(self, topic = None, value = None):
        self.type = 'Pickle'
        self.topic = topic
        self.value = value
        super().__init__()

class Subscribe(Message):						#this will create a object, which creates a message with the format desired
    def __init__(self, msg: Message):
        self.type = msg.type
        self.decoded = {"command": "subscribe", "type": msg.type, "topic": msg.topic}			#message still not coded
        if isinstance(msg, JsonMessage):				#if the msg is an JsonMessage object, it will use the json.dumps() function to convert it
            self.encoded = json.dumps(self.decoded).encode()
        elif isinstance(msg, XmlMessage):
            self.encoded = Protocol.Encode(self.decoded)
        elif isinstance(msg, PickleMessage):
            self.encoded = pickle.dumps(self.decoded)
        super().__init__()

class Unsubscribe(Message):
    def __init__(self, msg: Message):
        self.type = msg.type
        self.decoded = {"command": "unsubscribe", "type": msg.type, "topic": msg.topic}
        if isinstance(msg, JsonMessage):
            self.encoded = json.dumps(self.decoded).encode()
        elif isinstance(msg, XmlMessage):
            self.encoded = Protocol.Encode(self.decoded)
        elif isinstance(msg, PickleMessage):
            self.encoded = pickle.dumps(self.decoded)
        super().__init__()

class ListAll(Message):
    def __init__(self, msg: Message):
        self.type = msg.type
        self.decoded = {"command": "listall", "type": msg.type}
        if isinstance(msg, JsonMessage):
            self.encoded = json.dumps(self.decoded).encode()
        elif isinstance(msg, XmlMessage):
            self.encoded = Protocol.Encode(self.decoded)
        elif isinstance(msg, PickleMessage):
            self.encoded = pickle.dumps(self.decoded)
        super().__init__()

class Publish(Message):
    def __init__(self, msg: Message):
        self.type = msg.type
        self.decoded = {"command": "pub", "type": msg.type, "topic": msg.topic, "value": msg.value}
        if isinstance(msg, JsonMessage):
            self.encoded = json.dumps(self.decoded).encode()
        elif isinstance(msg, XmlMessage):
            self.encoded = Protocol.Encode(self.decoded)
        elif isinstance(msg, PickleMessage):
            self.encoded = pickle.dumps(self.decoded)
        super().__init__()

class Protocol:
    """Type of the message"""
      
    @classmethod
    def Encode(cls, msg):				#encondes a message to xml format
        msg2 = {}
        for key in msg:
            msg2[str(key)] = str(msg[key])
        parent = ET.Element("msg", attrib=msg2)
        return ET.tostring(parent)

    @classmethod
    def Decode(cls, data):				#decodes a message to xml format
        bytes = ET.fromstring(data)
        if bytes.tag == 'msg':
            return bytes.attrib
        else:
            return None

    @classmethod
    def json(cls, topic = None, value = None) -> JsonMessage:		# Each one of the next classmethods return a message object of the type of message desired to be sent
        json = JsonMessage(topic, value)
        return json

    @classmethod
    def xml(cls, topic = None, value = None) -> XmlMessage:
        xml = XmlMessage(topic, value)
        return xml
    
    @classmethod
    def pickle(cls, topic = None, value = None) -> PickleMessage:
        pickle = PickleMessage(topic, value)
        return pickle

    """Command of the message"""
    @classmethod
    def sub(cls, msg: Message) -> Subscribe:
        subs = Subscribe(msg)
        return subs

    @classmethod
    def unsub(cls, msg: Message) -> Unsubscribe:
        unsubs = Unsubscribe(msg)
        return unsubs
    
    @classmethod
    def listall(cls, msg: Message) -> ListAll:
        lall = ListAll(msg)
        return lall

    @classmethod
    def pub(cls, msg: Message) -> Publish:
        pubs = Publish(msg)
        return pubs

    @classmethod
    def send(cls, connection: socket, msg: Message):
        header = len(msg.encoded).to_bytes(2, "big")			# when sending, sends another two bytes with the length of the message
        try:                     
            connection.send(header+msg.encoded)				# tries to send the message with the length
        except:
            pass
        
    @classmethod
    def sendFirst(cls, connection: socket, msg: str):			# first message to be sent by a client, that says in which type their messages will be sent (Json, xml or Pickle)
        header = len(msg).to_bytes(2, "big")                     
        connection.send(header+msg.encode())

    @classmethod
    def recv(cls, connection: socket) -> str:
        try:
            header = int.from_bytes(connection.recv(2), "big")       	# tries to read the message, the two first bytes indicate the length, so that the quantity received is exactly the same as the one sent, so that no data is lost
            message_encoded = connection.recv(header)
            return message_encoded
        except:
            pass
    
class ProtocolBadFormat(Exception):
    """Exception when source message is not Protocol"""

    def __init__(self, original_msg: bytes = None):
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        return self._original.decode("utf-8")
