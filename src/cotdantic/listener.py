from .converters import is_xml, xml2proto, is_proto
from .multicast import MulticastListener
from .models import *
from .cot_types import atom
from contextlib import ExitStack
import platform
import time
import uuid


def print_cot(data: bytes, who: str):
	proto = None

	if is_xml(data):
		proto = xml2proto(data)

	proto2 = None
	if is_proto(data):
		proto = data
		model = Event.from_bytes(proto)
		proto2 = model.to_bytes()

	if proto is not None:
		model = Event.from_bytes(proto)
		xml = model.to_xml()

		print('=' * 100 + f' {who}-captured')

		if proto2 is not None and proto != proto2:
			print(f'WARNING: proto and reconstruction not identical: bytes: {len(proto2)}')
			print(proto2, '\n')

		print(f'proto: bytes: {len(proto)}')
		print(proto, '\n')

		print(f'xml: bytes: {len(xml)}')
		print(model.to_xml(pretty_print=True).decode().strip())


def cot(address: str, port: int) -> Event:
	uid = f'cotdantic-{uuid.getnode()}'
	cot_type = str(atom.friend.ground.unit.combat.infantry)
	point = Point(lat=38.691420, lon=-77.134600)
	contact = Contact(callsign='CotDantic', endpoint=f'{address}:{port}:udp')
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

	parser = argparse.ArgumentParser()
	parser.add_argument('--maddress', type=str, default='239.2.3.1')
	parser.add_argument('--mport', type=int, default=6969)
	parser.add_argument('--minterface', type=str, default='0.0.0.0')
	parser.add_argument('--gaddress', type=str, default='224.10.10.1')
	parser.add_argument('--gport', type=int, default=17012)
	parser.add_argument('--ginterface', type=str, default='0.0.0.0')
	parser.add_argument('--uaddress', type=str, default='0.0.0.0')
	parser.add_argument('--uport', type=int, default=4242)
	args = parser.parse_args()

	maddress = args.maddress
	mport = args.mport
	minterface = args.minterface
	uaddress = args.uaddress
	uport = args.uport
	gaddress = args.gaddress
	gport = args.gport
	ginterface = args.ginterface

	event = cot(uaddress, uport)

	with ExitStack() as stack:
		multicast = stack.enter_context(MulticastListener(maddress, mport, minterface))
		group_chat = stack.enter_context(MulticastListener(gaddress, gport, ginterface))
		unicast = stack.enter_context(MulticastListener(uaddress, uport))

		multicast.add_observer(lambda data, server: print_cot(data, 'multicast'))
		group_chat.add_observer(lambda data, server: print_cot(data, 'groupchat'))
		unicast.add_observer(lambda data, server: print_cot(data, 'unicast'))

		while True:
			event.time = isotime()
			event.start = isotime()
			event.stale = isotime(minutes=5)
			multicast.send(event.to_bytes())
			time.sleep(30)
