from .converters import is_xml, xml2proto, is_proto
from .multicast import MulticastListener, TcpListener
from contextlib import ExitStack
from .cot_types import atom
from threading import Lock
from typing import Tuple
from .models import *
import logging
import uuid
import time

log = logging.getLogger(__name__)
print_lock = Lock()


def print_cot(data: bytes, server: Tuple[str, int], who: str = 'unknown', source: str = None):
	if source and server[0] != source:
		return

	with print_lock:
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

		log.info('=' * 100 + f' {who}-captured {data_type_string}')

		if proto_original is not None and proto_original != proto_reconstructed:
			log.debug(f'proto_original != proto_reconstructed {len(proto_original)} {len(proto_reconstructed)}')
			log.debug(f'{proto_original}')
			log.debug(f'{proto_reconstructed}')

		if xml_original is not None and xml_original != xml_reconstructed:
			log.debug(f'xml_original != xml_reconstructed {len(xml_original)} {len(xml_reconstructed)}')
			log.debug(f'{xml_original}')
			log.debug(f'{xml_reconstructed}')

		log.info(f'proto reconstructed: bytes: {len(proto_reconstructed)}')
		log.info(f'{proto_reconstructed}\n')

		log.info(f'xml reconstructed: bytes: {len(xml_reconstructed)}')
		log.info(f"{model.to_xml(pretty_print=True, encoding='UTF-8', standalone=True).decode().strip()}\n")


def cot(address: str, port: int) -> Event:
	uid = f'cotdantic-{uuid.getnode()}'
	cot_type = str(atom.friend.ground.unit.combat.infantry)
	point = Point(lat=38.691420, lon=-77.134600)
	contact = Contact(callsign='CotDantic', endpoint=f'{address}:{port}:tcp')
	group = Group(name='Cyan', role='Team Member')
	detail = Detail(contact=contact, group=group)
	event = Event(
		uid=uid,
		type=cot_type,
		point=point,
		detail=detail,
	)
	return event


def cot_listener():
	import argparse
	import sys

	parser = argparse.ArgumentParser()
	parser.add_argument('--maddress', type=str, default='239.2.3.1')
	parser.add_argument('--mport', type=int, default=6969)
	parser.add_argument('--minterface', type=str, default='0.0.0.0')
	parser.add_argument('--gaddress', type=str, default='224.10.10.1')
	parser.add_argument('--gport', type=int, default=17012)
	parser.add_argument('--ginterface', type=str, default='0.0.0.0')
	parser.add_argument('--uaddress', type=str, default='0.0.0.0')
	parser.add_argument('--uport', type=int, default=4242)
	parser.add_argument('--source', type=str, default=None)
	parser.add_argument(
		'-l',
		'--log-level',
		default='INFO',
		choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
		help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)',
	)
	args = parser.parse_args()

	maddress = args.maddress
	mport = args.mport
	minterface = args.minterface
	uaddress = args.uaddress
	uport = args.uport
	gaddress = args.gaddress
	gport = args.gport
	ginterface = args.ginterface
	source = args.source
	log_level = args.log_level

	numeric_level = getattr(logging, log_level, None)
	if not isinstance(numeric_level, int):
		raise ValueError(f'Invalid log level: {args.logging}')
	logging.basicConfig(level=numeric_level, format='%(message)s')

	logging.basicConfig(
		stream=sys.stdout,
		level=numeric_level,
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	)

	event = cot(uaddress, uport)

	with ExitStack() as stack:
		multicast = stack.enter_context(MulticastListener(maddress, mport, minterface))
		group_chat = stack.enter_context(MulticastListener(gaddress, gport, ginterface))
		unicast_udp = stack.enter_context(MulticastListener(uaddress, uport))
		unicast_tcp = stack.enter_context(TcpListener(uaddress, uport))

		multicast.add_observer(partial(print_cot, who='multicast', source=source))
		group_chat.add_observer(partial(print_cot, who='groupchat', source=source))
		unicast_udp.add_observer(partial(print_cot, who='unicast_udp', source=source))
		unicast_tcp.add_observer(partial(print_cot, who='unicast_tcp', source=source))

		while True:
			event.time = isotime()
			event.start = isotime()
			event.stale = isotime(minutes=5)
			multicast.send(event.to_bytes())
			time.sleep(30)
