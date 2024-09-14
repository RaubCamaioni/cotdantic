from typing import List, Callable, Tuple
from threading import Thread
import platform
import socket


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

        self.processing_thread = Thread()
        self.processing_thread.start()

    def clear_observers(self):
        self.observers = []

    def add_observer(self, func: Callable[[bytes, Tuple[str, int]], None]):
        self.observers.append(func)

    def remove_observer(self, func: Callable[[bytes, Tuple[str, int]], None]):
        self.observers.remove(func)

    def _connect(self):
        """connects to multicast address:port on given network adapter"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**8)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:

            # platform dependent socket bind
            system_name = platform.system()
            if system_name == "Linux":
                self.sock.bind((self.address, self.port))
            elif system_name == "Windows":
                self.sock.bind((self.network_adapter, self.port))
            else:
                raise SystemError("unsupported system")

            # join multicast group and specify sending interface (IPPROTO_IP: windows supported for multicast options)
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
            with self.sock as s:

                while self.running:
                    data, server = s.recvfrom(65507)

                    if self.running:
                        self.process_observers(data, server)

                self.sock.setsockopt(
                    socket.IPPROTO_IP,
                    socket.IP_DROP_MEMBERSHIP,
                    socket.inet_aton(self.address)
                    + socket.inet_aton(self.network_adapter),
                )

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
