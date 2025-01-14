from .multicast import MulticastPublisher, TcpListener, UdpListener
from .converters import is_xml, is_proto
from .windows import Pad, PadHandler
from contextlib import ExitStack
from threading import Lock
from typing import Tuple
from .templates import *
from .utilities import *
from .contacts import *
from .models import *
from . import UID, CALLSIGN
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
	packet: Tuple[bytes, Tuple[str, int]],
	pad: Pad,
	source: str = 'unknown',
	debug: bool = False,
):
	try:
		data, _ = packet
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
		pad.print(f'{model.to_xml(pretty_print=True, encoding="UTF-8", standalone=True).decode().strip()}\n')

		if model.detail.raw_xml:
			pad.print(f'unknown tags: {model.detail.raw_xml}')

	except Exception as e:
		pad.print(f'Exception: {e}\n')


def chat_ack(packet: Tuple[bytes, Tuple[str, int]], socket: TcpListener, pad: Pad, ack: bool = True):
	data, server = packet
	event = Event.from_bytes(data)

	try:
		if 'GeoChat' in event.uid:
			pad.print(f'{event.detail.chat.sender_callsign}: {event.detail.remarks.text}')

			if not ack:
				return

			event1, event2 = ack_message(event)
			socket.send(bytes(event1), (server[0], 4242))
			socket.send(bytes(event2), (server[0], 4242))
			socket.send(bytes(echo_chat(event)), (server[0], 4242))

	except Exception as e:
		pad.print(f'\n\n{type(e)}')


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
	phandler = PadHandler(stdscr)

	with ExitStack() as stack:
		multicast = stack.enter_context(MulticastPublisher(maddress, mport, minterface))
		group_chat = stack.enter_context(MulticastPublisher(gaddress, gport, ginterface))
		unicast_udp = stack.enter_context(UdpListener(uport, interface))
		unicast_tcp = stack.enter_context(TcpListener(tport, interface))

		multicast.add_observer(partial(to_pad, pad=phandler.topa, source='SA', debug=debug))
		group_chat.add_observer(partial(to_pad, pad=phandler.topa, source='CHAT', debug=debug))
		unicast_udp.add_observer(partial(to_pad, pad=phandler.topa, source='UDP', debug=debug))
		unicast_tcp.add_observer(partial(to_pad, pad=phandler.topa, source='TCP', debug=debug))

		group_chat.add_observer(partial(chat_ack, socket=unicast_tcp, pad=phandler.botr, ack=False))
		unicast_udp.add_observer(partial(chat_ack, socket=unicast_udp, pad=phandler.botr, ack=echo))
		unicast_tcp.add_observer(partial(chat_ack, socket=unicast_tcp, pad=phandler.botr, ack=echo))

		def contact_display_update(contacts: Contacts):
			phandler.botl._text = []
			phandler.botl.print(f'{contacts}')

		multicast.add_observer(converter.process_observers)
		converter.add_observer(contacts.pli_listener)
		contacts.add_observer(contact_display_update)

		event = default_blue_force(
			uid=UID,
			callsign=CALLSIGN,
			group_name='Cyan',
			group_role='Team Member',
			address=address,
			lat=38.691420,
			lon=-77.134600,
			unicast=unicast,
		)

		@throttle(10 if address else -1)
		def pli_send():
			event.time = isotime()
			event.start = isotime()
			event.stale = isotime(minutes=5)
			multicast.send(event.to_xml())

		while phandler.running:
			pli_send()
			phandler.update()
			phandler.refresh()
			time.sleep(0.02)


def main():
	from contextlib import suppress
	import argparse

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--maddress', type=str, default='239.2.3.1', help='SA address')
	parser.add_argument('--mport', type=int, default=6969, help='SA port')
	parser.add_argument('--minterface', type=str, default='0.0.0.0', help='SA interface')
	parser.add_argument('--gaddress', type=str, default='224.10.10.1', help='Chat address')
	parser.add_argument('--gport', type=int, default=17012, help='Chat port')
	parser.add_argument('--ginterface', type=str, default='0.0.0.0', help='Chat interface')
	parser.add_argument('--address', type=str, default=None, help='default TCP/UDP send address')
	parser.add_argument('--interface', type=str, default='0.0.0.0', help='TCP/UDP bind interface')
	parser.add_argument('--uport', type=int, default=17012, help='UDP port')
	parser.add_argument('--tport', type=int, default=4242, help='TCP port')
	parser.add_argument('--unicast', default='tcp', choices=['tcp', 'udp'], help='Endpoint protocol')
	parser.add_argument('--debug', action='store_true', help='Print debug information')
	parser.add_argument('--echo', action='store_true', help='Echo back direct messages')
	args = parser.parse_args()

	with suppress(KeyboardInterrupt):
		curses.wrapper(cotdantic, args)
