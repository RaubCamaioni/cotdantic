from .multicast import MulticastListener, TcpListener
from .converters import is_xml, xml2proto, is_proto
from .windows import Pad, PadHandler
from contextlib import ExitStack
from .cot_types import atom
from threading import Lock
from typing import Tuple
from .utilities import *
from .contacts import *
from .models import *
import logging
import curses
import time

log = logging.getLogger(__name__)
print_lock = Lock()


def lock_decorator(func):
	def inner(*args, **kwargs):
		with print_lock:
			return func(*args, **kwargs)

	return inner


@lock_decorator
def to_pad(
	data: bytes,
	server: Tuple[str, int],
	pad: Pad,
	source: str = 'unknown',
	debug: bool = False,
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
	elif is_proto(data):
		data_type_string = 'protobuf'
		proto_original = data
		model = Event.from_bytes(proto_original)
		proto_reconstructed = model.to_bytes()
		xml_reconstructed = model.to_xml()
	else:
		return

	pad.print(f'\n{source}: {data_type_string}', 1)

	if debug and proto_original is not None and proto_original != proto_reconstructed:
		pad.print(f'proto_original ({len(proto_original)} bytes) != reconstructed proto')
		pad.print(f'{proto_original}\n')

	if debug and xml_original is not None and xml_original != xml_reconstructed:
		pad.print(f'xml_original ({len(xml_original)} bytes) != reconstructed xml')
		pad.print(f'{xml_original}\n')

	if debug:
		pad.print(f'proto reconstructed ({len(proto_reconstructed)} bytes)')
		pad.print(f'{proto_reconstructed}\n')

	if debug:
		pad.print(f'xml reconstructed ({len(xml_reconstructed)} bytes)')
	pad.print(
		f"{model.to_xml(pretty_print=True, encoding='UTF-8', standalone=True).decode().strip()}\n"
	)

	if model.detail.raw_xml:
		pad.print(f'unknown tags: {model.detail.raw_xml}')


def chat_ack(data: bytes, server: Tuple[str, int], socket: TcpListener, pad: Pad, ack: bool = True):
	event = Event.from_bytes(data)

	if 'GeoChat' in event.uid:
		pad.print(f'{event.detail.chat.sender_callsign}: {event.detail.remarks.text}')

		if not ack:
			return

		event1, event2 = ack_message(event)
		socket.send(event1.to_bytes(), (server[0], 4242))
		socket.send(event2.to_bytes(), (server[0], 4242))
		socket.send(echo_chat(event).to_bytes(), (server[0], 4242))


def cotdantic(stdscr, args):
	maddress = args.maddress
	minterface = args.minterface
	mport = args.mport

	gaddress = args.gaddress
	ginterface = args.ginterface
	gport = args.gport

	address = args.address
	interface = args.interface
	uport = args.uport
	tport = args.tport

	unicast = args.unicast
	debug = args.debug
	echo = args.echo

	converter = Converter()
	contacts = Contacts()
	event = pli_cot(address, tport, unicast=unicast)

	phandler = PadHandler(stdscr)

	with ExitStack() as stack:
		multicast = stack.enter_context(MulticastListener(maddress, mport, minterface))
		group_chat = stack.enter_context(MulticastListener(gaddress, gport, ginterface))
		unicast_udp = stack.enter_context(MulticastListener(address, uport, interface))
		unicast_tcp = stack.enter_context(TcpListener(address, tport))

		multicast.add_observer(partial(to_pad, pad=phandler.topa, source='SA', debug=debug))
		group_chat.add_observer(partial(to_pad, pad=phandler.topa, source='CHAT', debug=debug))
		unicast_udp.add_observer(partial(to_pad, pad=phandler.topa, source='UDP', debug=debug))
		unicast_tcp.add_observer(partial(to_pad, pad=phandler.topa, source='TCP', debug=debug))

		group_chat.add_observer(partial(chat_ack, socket=unicast_tcp, pad=phandler.botr, ack=False))
		unicast_udp.add_observer(partial(chat_ack, socket=unicast_tcp, pad=phandler.botr, ack=echo))
		unicast_tcp.add_observer(partial(chat_ack, socket=unicast_tcp, pad=phandler.botr, ack=echo))

		multicast.add_observer(converter.process_observers)
		converter.add_observer(contacts.pli_listener)

		def contact_display_update(contacts: Contacts):
			phandler.botl._text = []
			phandler.botl.print(f'{contacts}')

		contacts.add_observer(contact_display_update)

		last_send = 0

		stdscr.nodelay(True)
		while True:
			key = stdscr.getch()

			if key == ord('q'):
				break
			elif key == curses.KEY_RIGHT:
				phandler.next_select()
			elif key == curses.KEY_LEFT:
				phandler.next_select(next=-1)

			phandler.update(key)

			if time.time() - last_send > 10:
				last_send = time.time()
				event.time = isotime()
				event.start = isotime()
				event.stale = isotime(minutes=5)
				multicast.send(event.to_bytes())

			phandler.refresh()
			time.sleep(0.01)


def main():
	from contextlib import suppress
	import argparse

	ip = default_ip()
	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--maddress', type=str, default='239.2.3.1', help='SA address')
	parser.add_argument('--mport', type=int, default=6969, help='SA port')
	parser.add_argument('--minterface', type=str, default=ip, help='SA interface')
	parser.add_argument('--gaddress', type=str, default='224.10.10.1', help='Chat address')
	parser.add_argument('--gport', type=int, default=17012, help='Chat port')
	parser.add_argument('--ginterface', type=str, default=ip, help='Chat interface')
	parser.add_argument('--address', type=str, default=ip, help='default TCP/UDP send address')
	parser.add_argument('--interface', type=str, default=ip, help='TCP/UDP bind interface')
	parser.add_argument('--uport', type=int, default=17012, help='UDP port')
	parser.add_argument('--tport', type=int, default=4242, help='TCP port')
	parser.add_argument('--debug', type=bool, default=False, help='Print debug information')
	parser.add_argument(
		'--unicast', default='tcp', choices=['tcp', 'udp'], help='Endpoint protocol'
	)
	parser.add_argument('--echo', action='store_true', help='Echo back direct messages')
	args = parser.parse_args()

	with suppress(KeyboardInterrupt):
		curses.wrapper(cotdantic, args)
