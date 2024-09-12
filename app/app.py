from typing import List, Callable, Tuple
from threading import Thread
import platform
import socket
import time

from takproto import parse_proto, xml2proto, TAKProtoVer
from takproto.functions import msg2proto

import xml.etree.ElementTree as ET
import cot


def is_xml(data: bytes) -> bool:
    try:
        return ET.fromstring(data.decode())
    except ET.ParseError:
        return None
    except UnicodeDecodeError:
        return None


def is_proto(data: bytes) -> bool:
    try:
        tak_message = parse_proto(data)
        return bool(tak_message)
    except Exception as e:
        return False


def parse_cot(data):

    if is_xml(data):
        p = xml2proto(data)
        return True, parse_proto(p)

    if is_proto(data):
        return True, parse_proto(data)

    return False, None


class MulticastListener:
    """binds to a multicast address and publishes messages to observers"""

    def __init__(self, address: str, port: int, network_adapter: str = ""):
        """creates multicast socket for send/recv on address:port"""
        self.address = address
        self.port = port
        self.network_adapter = network_adapter
        self.running = True
        self.observers: List[Callable[[bytes], None]] = []

        self.sock: socket.socket = None
        self._connect(self.address, self.port, self.network_adapter)

        self.processing_thread = Thread()
        self.processing_thread.start()

    def clear_observers(self):
        self.observers = []

    def add_observer(self, func: Callable[[bytes, Tuple[str, int]], None]):
        self.observers.append(func)

    def remove_observer(self, func: Callable[[bytes, Tuple[str, int]], None]):
        self.observers.remove(func)

    def _connect(self, address: str, port: int, network_adapter: str):
        """connects to multicast address:port on given network adapter"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**8)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:

            # platform dependent socket bind
            system_name = platform.system()
            if system_name == "Linux":
                self.sock.bind((address, port))
            elif system_name == "Windows":
                self.sock.bind((network_adapter, port))
            else:
                raise SystemError("unsupported system")

            # join multicast group and specify sending interface (IPPROTO_IP: windows supported for multicast options)
            self.sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_ADD_MEMBERSHIP,
                socket.inet_aton(address) + socket.inet_aton(network_adapter),
            )
            self.sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_IF,
                socket.inet_aton(network_adapter),
            )

        except Exception as e:
            self.running = False
            self.sock.close()
            return

    def stop(self):
        """stop publishing thread and close socket"""

        if self.running:
            self.running = False
            try:
                # release socket from waiting for message
                self.sock.sendto(b"", (self.address, self.port))
            except socket.error as e:
                print(f"socket close error: {e}")

        self.processing_thread.join(5)

    def send(self, data: bytes):
        """send bytes over multicast"""
        self.sock.sendto(data, (self.address, self.port))

    def start(self) -> "MulticastListener":
        """start multicast publisher"""

        def _publisher():
            with self.sock as s:
                while self.running:
                    try:
                        data, server = s.recvfrom(2**10)
                        if self.running:
                            [o(data, server) for o in self.observers]
                    except Exception as e:
                        print(f"exception processing data: {e}")
                        continue

        self.processing_thread = Thread(target=_publisher, args=(), daemon=True)
        self.processing_thread.daemon = True
        self.processing_thread.start()

        return self

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exec_value, traceback):
        self.stop()
        if exc_type is KeyboardInterrupt:
            return True


def generate_cot():
    point = cot.Point(lat=38.696644, lon=-77.140433)
    contact = cot.Contact(callsign="DogMan", endpoint="172.16.0.128:4242:tcp")
    contact = cot.Contact(callsign="DogMan", endpoint=None)
    detail = cot.Detail(contact=contact)
    event = cot.Event(
        type="a-f-G-U-C-I",
        point=point,
        detail=detail,
    )
    event.type = "a-f-A-M-H-Q-r"

    xml = event.to_xml(
        pretty_print=True, encoding="UTF-8", standalone=True, skip_empty=True
    )

    return xml


def print_cot(data: bytes):

    proto = None

    if is_xml(data):
        proto = xml2proto(data)

    if is_proto(data):
        proto = data

    if proto is not None:
        print("========================================================")
        print("proto:")
        print(proto, "\n")
        print("xml:")
        print(cot.proto2model(proto).to_xml(pretty_print=True).decode())


if __name__ == "__main__":

    print("Starting Multicast Listener: \n")
    with MulticastListener("239.2.3.1", 6969, "0.0.0.0") as mcl:

        mcl.add_observer(lambda data, server: print_cot(data))

        while True:
            time.sleep(30)

    print("Exiting")
