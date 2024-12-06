from typing import List, Callable, Tuple, Union, Optional, TypeVar, Generic
from threading import Thread
import platform
import socket
import select

T = TypeVar('T')


UDP_MAX_LEN = 65507


class SelectEvent:
	"""thread.Event signal equivalent"""

	def __init__(self):
		self.r, self.w = socket.socketpair()
		self.triggered = False

	def set(self):
		if not self.triggered:
			self.triggered = True
			self.w.send(b'1')

	def clear(self):
		if self.triggered:
			self.triggered = False
			self.r.recv(1)

	def wait(self, waitable):
		readable, _, _ = select.select([waitable, self], [], [])
		return self in readable

	def close(self):
		self.r.close()
		self.w.close()

	def fileno(self):
		return self.r.fileno()


class Publisher(Generic[T]):
	"""generic publisher parent class pattern"""

	def __init__(self):
		self.observers: List[Callable[[T], None]] = []

	def clear_observers(self):
		self.observers = []

	def add_observer(self, func: Callable[[T], None]):
		self.observers.append(func)

	def remove_observer(self, func: Callable[[T], None]):
		self.observers.remove(func)

	def process_observers(self, data: T):
		for observer in self.observers:
			try:
				observer(data)
			except Exception:
				self.remove_observer(observer)
				continue


class MulticastPublisher(Publisher[Tuple[bytes, Tuple[str, int]]]):
	"""multicast socket to publisher pattern"""

	def __init__(self, address: str, port: int, network_adapter: str = '0.0.0.0'):
		super().__init__()

		self.address = address
		self.port = port
		self.network_adapter = network_adapter

		self.sock: socket.socket = None
		self.select_event = SelectEvent()

		self.processing_thread: Union[Thread, None] = None

	def _connect(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**8)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		{
			'Linux': lambda: self.sock.bind((self.address, self.port)),
			'Windows': lambda: self.sock.bind((self.network_adapter, self.port)),
		}.get(platform.system(), lambda: SystemError('unsupported system'))()

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

	def stop(self):
		self.select_event.set()

		if self.processing_thread:
			self.processing_thread.join(5)

		self.select_event.close()
		self.sock.close()

	def send(self, data: bytes):
		self.sock.sendto(data, (self.address, self.port))

	def start(self) -> 'MulticastPublisher':
		self._connect()

		def _publisher():
			with self.sock:
				while True:
					if self.select_event.wait(self.sock):
						break
					self.process_observers(self.sock.recvfrom(UDP_MAX_LEN))

				self.sock.setsockopt(
					socket.IPPROTO_IP,
					socket.IP_DROP_MEMBERSHIP,
					socket.inet_aton(self.address) + socket.inet_aton(self.network_adapter),
				)

		self.processing_thread = Thread(target=_publisher, args=(), daemon=True)
		self.processing_thread.start()

		return self

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exec_value, traceback):
		self.stop()
		if exc_type is KeyboardInterrupt:
			return True


class TcpListener(Publisher[Tuple[bytes, Tuple[str, int]]]):
	"""tcp socket to publisher pattern"""

	def __init__(self, port: int, network_adapter: str = '0.0.0.0'):
		super().__init__()
		self.port = port
		self.network_adapter = network_adapter
		self.recv_sock: socket.socket = None
		self.select_event = SelectEvent()
		self.processing_thread: Union[Thread, None] = None

	def _connect(self):
		self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.recv_sock.bind((self.network_adapter, self.port))
		self.recv_sock.listen()

	def start(self) -> 'TcpListener':
		self._connect()

		def _publisher():
			with self.recv_sock:
				while True:
					if self.select_event.wait(self.recv_sock):
						break
					conn, server = self.recv_sock.accept()
					with conn:
						data = []
						while True:
							b = conn.recv(1024)
							if not b:
								break
							data.append(b)
						data = b''.join(data)

						if data:
							self.process_observers((data, server))

		self.processing_thread = Thread(target=_publisher, args=(), daemon=True)
		self.processing_thread.start()

		return self

	def send(self, data: bytes, server: Tuple[str, int]):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.settimeout(5)
			sock.connect(server)
			sock.sendall(data)

	def stop(self):
		self.select_event.set()

		if self.processing_thread:
			self.processing_thread.join(5)

		self.select_event.close()
		self.recv_sock.close()

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exec_value, traceback):
		self.stop()
		if exc_type is KeyboardInterrupt:
			return True


class UdpListener(Publisher[Tuple[bytes, Tuple[str, int]]]):
	"""udp socket to publisher pattern"""

	def __init__(self, port: int, network_adapter: str = '0.0.0.0'):
		super().__init__()
		self.port = port
		self.network_adapter = network_adapter

		self.sock: socket.socket = None
		self.select_event = SelectEvent()

		self.processing_thread: Union[Thread, None] = None

	def _connect(self):
		"""join multicast group address:port:adapter and bind socket"""
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**8)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind((self.network_adapter, self.port))

	def stop(self):
		self.select_event.set()

		if self.processing_thread:
			self.processing_thread.join(5)

		self.select_event.close()
		self.sock.close()

	def send(self, data: bytes, server: Tuple[str, int]):
		self.sock.sendto(data, server)

	def start(self) -> 'MulticastPublisher':
		self._connect()

		def _publisher():
			with self.sock:
				while True:
					if self.select_event.wait(self.sock):
						break

					data, server = self.sock.recvfrom(UDP_MAX_LEN)
					self.process_observers((data, server))

		self.processing_thread = Thread(target=_publisher, args=(), daemon=True)
		self.processing_thread.start()

		return self

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exec_value, traceback):
		self.stop()
		if exc_type is KeyboardInterrupt:
			return True
