from .converters import is_xml, xml2proto, is_proto
from .multicast import MulticastListener
from .models import Event
from contextlib import ExitStack
import time


def print_cot(data: bytes, who: str):
	proto = None

	if is_xml(data):
		proto = xml2proto(data)

	if is_proto(data):
		proto = data

	if proto is not None:
		model = Event.from_bytes(proto)
		xml = model.to_xml()

		print('=' * 100 + f' {who}-captured')
		print(f'proto: bytes: {len(proto)}')
		print(proto, '\n')
		print(f'xml: bytes: {len(xml)}')
		print(model.to_xml(pretty_print=True).decode().strip())


def cot_listener():
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('--maddress', type=str, default='239.2.3.1')
	parser.add_argument('--mport', type=int, default=6969)
	parser.add_argument('--minterface', type=str, default='0.0.0.0')
	parser.add_argument('--uaddress', type=str, default='0.0.0.0')
	parser.add_argument('--uport', type=int, default=4242)
	args = parser.parse_args()

	maddress = args.maddress
	mport = args.mport
	minterface = args.minterface
	uaddress = args.uaddress
	uport = args.uport

	print('Multicast COT Listener:')
	print(f'  address: {maddress}')
	print(f'  port: {mport}')
	print(f'  interface: {minterface}')

	print('Unicast COT Listener:')
	print(f'  address: {uaddress}')
	print(f'  port: {uport}')

	with ExitStack() as stack:
		multicast = stack.enter_context(MulticastListener(maddress, mport, minterface))
		unicast = stack.enter_context(MulticastListener(uaddress, uport))

		multicast.add_observer(lambda data, server: print_cot(data, 'multicast'))
		unicast.add_observer(lambda data, server: print_cot(data, 'unicast'))

		while True:
			time.sleep(30)
