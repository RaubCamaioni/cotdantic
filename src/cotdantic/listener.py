from .multicast import MulticastListener, TcpListener
from .converters import is_xml, xml2proto, is_proto
from .contacts import *
from .utilities import *
from contextlib import ExitStack
from .cot_types import atom
from threading import Lock
from typing import Tuple
from .models import *
from collections import deque
import textwrap
import logging
import curses
import time
from itertools import islice

log = logging.getLogger(__name__)
print_lock = Lock()


def lock_decorator(func):
	def inner(*args, **kwargs):
		with print_lock:
			return func(*args, **kwargs)

	return inner


class Pad:
	def __init__(self, height, width, title=None):
		self.title = title or ''
		self.pad = curses.newpad(height, width)
		self.max_x = width - 2
		self.max_y = height - 2
		self._text = deque(maxlen=1000)
		self.selected = False
		self.pause_updates = False

	def toggle_pause(self):
		self.pause_updates = not self.pause_updates

	def border(self):
		self.pad.border()
		self.pad.move(0, 5)
		attr = 1 if self.selected else 0
		attr = 2 if self.pause_updates else attr
		self.pad.addnstr(self.title, self.max_x, curses.color_pair(attr))

	def clear(self):
		if self.pause_updates:
			return

		self.pad.clear()

	def erase(self):
		if self.pause_updates:
			return

		self.pad.erase()

	def refresh(self, x1, y1, x2, y2, x3, y3):
		self.pad.refresh(x1, y1, x2, y2, x3, y3)

	def print(self, text: str):
		split_newline = text.split('\n')
		for newline in split_newline:
			if newline == '':
				self._text.append('')
				continue
			split_wrapped = textwrap.wrap(newline, width=self.max_x)
			for line in split_wrapped:
				self._text.append(line)

	def render(self):
		if self.pause_updates:
			return

		length = len(self._text)
		self.current_line = 1
		for line in islice(self._text, max(length - self.max_y, 0), None):
			self.pad.move(self.current_line, 1)
			self.pad.addnstr(line, self.max_x)
			self.current_line += 1


class Cockpit:
	def __init__(self, stdscr: curses.window):
		curses.use_default_colors()
		curses.curs_set(0)
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
		curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
		self.stdscr = stdscr
		self.stdscr.clear()
		self.h, self.w = stdscr.getmaxyx()

		self.ht = self.h - self.h // 3
		self.hb = self.h - self.ht
		self.wl = self.w // 3
		self.wr = self.w - self.wl

		self.topa = Pad(self.ht, self.w, 'Situational Awareness')
		self.botl = Pad(self.hb, self.wl, 'Contacts')
		self.botr = Pad(self.hb, self.wr - 1, 'Chat')

		self.selected = 0
		self.update_selected()

	def next_select(self, next: int = 1):
		self.selected = (self.selected + next) % 3
		self.update_selected()

	def update_selected(self):
		self.topa.selected = bool(0 == self.selected)
		self.botl.selected = bool(1 == self.selected)
		self.botr.selected = bool(2 == self.selected)

	def clear(self):
		self.topa.clear()
		self.botl.clear()
		self.botr.clear()

	def erase(self):
		self.topa.erase()
		self.botl.erase()
		self.botr.erase()

	def border(self):
		self.topa.border()
		self.botl.border()
		self.botr.border()

	def refresh(self):
		self.erase()
		self.border()
		self.topa.render()
		self.botl.render()
		self.botr.render()

		self.topa.refresh(0, 0, 0, 0, self.ht, self.w)
		self.botl.refresh(0, 0, self.ht, 0, self.h, self.wl)
		self.botr.refresh(0, 0, self.ht, self.wl + 1, self.h, self.w)


@lock_decorator
def to_console(
	data: bytes,
	server: Tuple[str, int],
	pad: Pad,
	who: str = 'unknown',
):
	xml_original = None
	xml_reconstructed = None
	proto_original = None
	proto_reconstructed = None

	data_type_string = 'unknown'
	if is_xml(data):
		data_type_string = 'xml'
		xml_original = data
		model = Event.from_xml(data)
		proto_reconstructed = model.to_bytes()
		xml_reconstructed = model.to_xml()
	else:
		data_type_string = 'protobuf'
		proto_original = data
		model = Event.from_bytes(proto_original)
		proto_reconstructed = model.to_bytes()
		xml_reconstructed = model.to_xml()

	who_string = f'  {who}-captured {data_type_string}  '
	pad.print('-' * (pad.max_x - len(who_string)) + who_string)

	if proto_original is not None and proto_original != proto_reconstructed:
		pad.print(f'proto_original ({len(proto_original)} bytes) != reconstructed proto')
		pad.print(f'{proto_original}\n')

	if xml_original is not None and xml_original != xml_reconstructed:
		pad.print(f'xml_original ({len(xml_original)} bytes) != reconstructed xml')
		pad.print(f'{xml_original}\n')

	pad.print(f'proto reconstructed ({len(proto_reconstructed)} bytes)')
	pad.print(f'{proto_reconstructed}\n')

	pad.print(f'xml reconstructed ({len(xml_reconstructed)} bytes)')
	pad.print(
		f"{model.to_xml(pretty_print=True, encoding='UTF-8', standalone=True).decode().strip()}\n"
	)

	if model.detail.raw_xml:
		pad.print(f'unknown tags: {model.detail.raw_xml}')


def chat_ack(data: bytes, server: Tuple[str, int], socket: TcpListener, pad: Pad):
	event = Event.from_bytes(data)

	if 'GeoChat' in event.uid:
		pad.print(f'{event.detail.chat.sender_callsign}: {event.detail.remarks.text}')
		event1, event2 = ack_message(event)
		socket.send(event1.to_bytes(), (server[0], 4242))
		socket.send(event2.to_bytes(), (server[0], 4242))
		socket.send(echo_chat(event).to_bytes(), (server[0], 4242))


def _cot_listener(stdscr):
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('--maddress', type=str, default='239.2.3.1', help='SA address')
	parser.add_argument('--mport', type=int, default=6969, help='SA port')
	parser.add_argument('--minterface', type=str, default='0.0.0.0', help='SA interface')
	parser.add_argument('--gaddress', type=str, default='224.10.10.1', help='Chat address')
	parser.add_argument('--gport', type=int, default=17012, help='Chat port')
	parser.add_argument('--ginterface', type=str, default='0.0.0.0', help='Chat interface')
	parser.add_argument('--uaddress', type=str, default='0.0.0.0', help='Direct address')
	parser.add_argument('--uport', type=int, default=4242, help='Direct port')
	parser.add_argument('--source', type=str, default=None, help='Filter for messages from source')
	parser.add_argument(
		'--unicast',
		default='tcp',
		choices=['tcp', 'udp'],
		help='Set endpoint communication protocol',
	)
	args = parser.parse_args()

	maddress = args.maddress
	gaddress = args.gaddress
	uaddress = args.uaddress
	minterface = args.minterface
	ginterface = args.ginterface
	mport = args.mport
	gport = args.gport
	uport = args.uport
	unicast = args.unicast

	converter = Converter()
	contacts = Contacts()
	event = pli_cot(uaddress, uport, unicast=unicast)

	cockpit = Cockpit(stdscr)

	with ExitStack() as stack:
		multicast = stack.enter_context(MulticastListener(maddress, mport, minterface))
		group_chat = stack.enter_context(MulticastListener(gaddress, gport, ginterface))
		unicast_udp = stack.enter_context(MulticastListener(uaddress, uport))
		unicast_tcp = stack.enter_context(TcpListener(uaddress, uport))

		multicast.add_observer(partial(to_console, pad=cockpit.topa, who='multicast'))
		group_chat.add_observer(partial(to_console, pad=cockpit.topa, who='groupchat'))
		unicast_udp.add_observer(partial(to_console, pad=cockpit.topa, who='unicast_udp'))
		unicast_tcp.add_observer(partial(to_console, pad=cockpit.topa, who='unicast_tcp'))

		group_chat.add_observer(partial(chat_ack, socket=unicast_tcp, pad=cockpit.botr))
		unicast_udp.add_observer(partial(chat_ack, socket=unicast_tcp, pad=cockpit.botr))
		unicast_tcp.add_observer(partial(chat_ack, socket=unicast_tcp, pad=cockpit.botr))

		multicast.add_observer(converter.process_observers)
		converter.add_observer(contacts.pli_listener)

		def contact_display_update(contacts: Contacts):
			cockpit.botl._text = []
			cockpit.botl.print(f'{contacts}')

		contacts.add_observer(contact_display_update)

		last_send = 0

		stdscr.nodelay(True)
		while True:
			key = stdscr.getch()
			if key == ord('q'):
				break
			elif key == ord('p'):
				cockpit.topa.toggle_pause()
			elif key == curses.KEY_RIGHT:
				cockpit.next_select()
			elif key == curses.KEY_LEFT:
				cockpit.next_select(next=-1)

			if time.time() - last_send > 10:
				last_send = time.time()
				event.time = isotime()
				event.start = isotime()
				event.stale = isotime(minutes=5)
				multicast.send(event.to_bytes())

			cockpit.refresh()
			time.sleep(0.05)


def cot_listener():
	from contextlib import suppress

	with suppress(KeyboardInterrupt):
		curses.wrapper(_cot_listener)
