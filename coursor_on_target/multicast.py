from typing import List, Callable, Tuple
from threading import Thread
import platform
import socket
import select
import os

UDP_MAX_LEN = 65507


class MulticastListener:
    """binds to a multicast address and publishes messages to observers"""

    def __init__(self, address: str, port: int, network_adapter: str = ""):
        """create multicast socket store network configuration"""
        self.address = address
        self.port = port
        self.network_adapter = network_adapter
        self.running = False
        self.observers: List[Callable[[bytes], None]] = []

        self.sock: socket.socket = None
        self.pipe_r, self.pipe_w = socket.socketpair()

        # create "stopped" thread
        self.processing_thread = Thread()
        self.processing_thread.start()

    def clear_observers(self):
        self.observers = []

    def add_observer(self, func: Callable[[bytes, Tuple[str, int]], None]):
        self.observers.append(func)

    def remove_observer(self, func: Callable[[bytes, Tuple[str, int]], None]):
        self.observers.remove(func)

    def _connect(self):
        """join multicast group address:port:adapter and bind socket"""

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**8)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:

            system_name = platform.system()
            if system_name == "Linux":
                self.sock.bind((self.address, self.port))
            elif system_name == "Windows":
                self.sock.bind((self.network_adapter, self.port))
            else:
                raise SystemError("unsupported system")

            self.sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_ADD_MEMBERSHIP,
                socket.inet_aton(self.address) + socket.inet_aton(self.network_adapter),
            )

            self.sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_IF,
                socket.inet_aton(self.network_adapter),
            )

        except Exception as e:
            self.stop()
            return

    def stop(self):
        """stop publishing thread and close socket"""

        self.running = False
        if self.pipe_w:
            self.pipe_w.send(b"1")

        self.processing_thread.join(5)

        self.pipe_w.close()
        self.pipe_r.close()
        self.sock.close()

    def send(self, data: bytes):
        """send bytes over multicast"""
        self.sock.sendto(data, (self.address, self.port))

    def process_observers(self, data, server):
        """process observer functions"""
        for observer in self.observers:
            try:
                observer(data, server)
            except Exception as e:
                print(
                    f"Removing Observer ({observer.__name__}): ({type(e).__name__}) {e}"
                )
                self.remove_observer(observer)
                continue

    def start(self) -> "MulticastListener":
        """start multicast publisher"""

        self._connect()

        def _publisher():

            self.running = True

            with self.sock, self.pipe_r:

                while self.running:

                    select.select([self.sock, self.pipe_r], [], [])

                    if not self.running:
                        break

                    data, server = self.sock.recvfrom(UDP_MAX_LEN)
                    self.process_observers(data, server)

                self.sock.setsockopt(
                    socket.IPPROTO_IP,
                    socket.IP_DROP_MEMBERSHIP,
                    socket.inet_aton(self.address)
                    + socket.inet_aton(self.network_adapter),
                )

            self.running = False

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
