from typing import Tuple, Callable, Dict
from .converters import is_xml
from .models import *
import traceback
import logging

log = logging.getLogger(__name__)


class Converter:
	def __init__(self):
		self.observers: List[Callable[[Event, Tuple[str, int]], None]] = []

	def clear_observers(self):
		self.observers = []

	def add_observer(self, func: Callable[[Event, Tuple[str, int]], None]):
		self.observers.append(func)

	def remove_observer(self, func: Callable[[Event, Tuple[str, int]], None]):
		self.observers.remove(func)

	def process_observers(self, packet: Tuple[bytes, Tuple[str, int]]):
		data, server = packet

		for observer in self.observers:
			if is_xml(data):
				event = Event.from_xml(data)
			else:
				event = Event.from_bytes(data)

			try:
				observer(event, server)
			except Exception as e:
				log.error(f'Removing Observer ({observer.__name__}): ({type(e).__name__}) {e}')
				log.error(traceback.format_exc())
				self.remove_observer(observer)
				continue


class Contacts:
	def __init__(self):
		self.contacts: Dict[str, Tuple[Event, Tuple[str, int]]] = {}
		self.observers: List[Callable[['Contacts'], None]] = []

	def clear_observers(self):
		self.observers = []

	def add_observer(self, func: Callable[['Contacts'], None]):
		self.observers.append(func)

	def remove_observer(self, func: Callable[['Contacts'], None]):
		self.observers.remove(func)

	def pli_listener(self, event: Event, server: Tuple[str, int]):
		if event.detail.group is None:
			return

		if event.detail.contact is None:
			return

		if event.detail.contact.callsign is None:
			return

		self.contacts[event.uid] = (event, server)
		self.process_observers()

	def process_observers(self):
		for observer in self.observers:
			try:
				observer(self)
			except Exception as e:
				log.error(f'Removing Observer ({observer.__name__}): ({type(e).__name__}) {e}')
				log.error(traceback.format_exc())
				self.remove_observer(observer)
				continue

	def __str__(self):
		c = []
		for uid, (event, server) in self.contacts.items():
			contact = event.detail.contact
			c.append(f'{contact.callsign}: {contact.endpoint}')
		return '\n'.join(c)
