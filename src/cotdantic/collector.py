from .multicast import MulticastPublisher
from . import Event

from contextlib import ExitStack, suppress
from functools import partial
from typing import Tuple
import logging
import socket
import ssl


def ssl_context(
	client_cert: str,
	client_key: str,
	server_cert: str,
	check_hostname: bool = False,
):
	context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
	context.minimum_version = ssl.TLSVersion.TLSv1_2
	context.maximum_version = ssl.TLSVersion.TLSv1_3
	context.verify_mode = ssl.CERT_REQUIRED
	context.check_hostname = check_hostname
	context.load_cert_chain(certfile=client_cert, keyfile=client_key)
	context.load_verify_locations(cafile=server_cert)
	return context


def local_to_remote(callback: Tuple[bytes, Tuple[str, int]], sock: socket.socket):
	data, _ = callback

	event = Event.from_cot(data)

	if event is None:
		return

	logging.info(f'local->remote: {event.uid}')
	sock.send(event.to_xml())


def tak_probe(
	address: str,
	port: int,
	client_cert: str,
	client_key: str,
	server_cert: str,
	interface: str = '0.0.0.0',
):
	with ExitStack() as stack:
		m_addr, m_port = '239.2.3.1', 6969
		logging.info(f'Multicast Probe: {m_addr}:{m_port}:{interface}')

		stack.enter_context(suppress(KeyboardInterrupt))
		multi = stack.enter_context(MulticastPublisher(m_addr, m_port, interface))

		context = ssl_context(client_cert, client_key, server_cert)
		sock = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
		ssock = stack.enter_context(context.wrap_socket(sock))

		logging.info(f'Attempting connect remote: {address}:{port}')
		ssock.connect((address, port))
		logging.info('Success connect remote.')
		multi.add_observer(partial(local_to_remote, sock=ssock))

		for data in iter(lambda: ssock.recv(4096), None):
			event = Event.from_cot(data)
			if event is None:
				continue
			logging.info(f'remote->local: {event.uid}')
			multi.send(data)

	logging.info('Exiting')


def main():
	import argparse
	import sys

	logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--address', type=str, required=True, help='Tak Server Address')
	parser.add_argument('--port', type=int, required=True, help='Tak Server Port')
	parser.add_argument('--client_cert', type=str, required=True, help='Client Cert')
	parser.add_argument('--client_key', type=str, required=True, help='Client Key')
	parser.add_argument('--server_trust', type=str, required=True, help='Server Trust')
	parser.add_argument('--interface', type=str, default='0.0.0.0', help='Multicast Interface')
	args = parser.parse_args()

	tak_probe(
		args.address,
		args.port,
		args.client_cert,
		args.client_key,
		args.server_trust,
		args.interface,
	)
