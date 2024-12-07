from cotdantic import *
import random
import hashlib
from pathlib import Path
import pytest


def random_lat_lon():
	lat, lon = 38.695514, -77.140035
	return (
		lat + 0.01 * random.random(),
		lon + 0.01 * random.random(),
	)


def default_pli():
	lat, lon = random_lat_lon()
	callsign = f'cotdantic-{random.randint(0, 1000)}'
	iconsetpath = 'COT_MAPPING_2525C/a-u/a-u-G'

	point = Point(
		lat=lat,
		lon=lon,
	)

	detail = Detail(
		contact=Contact(callsign=callsign),
		archive=Archive(),
		usericon=Usericon(iconsetpath=iconsetpath),
	)

	event = Event(
		type='a-u-G',
		point=point,
		detail=detail,
	)

	return event


def sha256_file(file: Path):
	hasher = hashlib.sha256()
	with open(file, 'rb') as file:
		for byte_block in iter(lambda: file.read(4096), b''):
			hasher.update(byte_block)
		return hasher.hexdigest()


@pytest.mark.skip(reason='request wintak/atak utilities')
def test_zip_creation():
	from cotdantic.datapack import DataPack, Attachment, FileServer
	from cotdantic.multicast import TcpListener
	from cotdantic.utilities import pli_cot
	from contextlib import ExitStack
	from pathlib import Path
	import tempfile
	import time
	import uuid

	cot_uid = pli_cot('', 0, '').uid

	with ExitStack() as stack:
		port = 8002

		temp_dir = Path(stack.enter_context(tempfile.TemporaryDirectory()))
		_ = stack.enter_context(FileServer(port=port, directory=temp_dir))
		com = stack.enter_context(TcpListener(4242))

		event_a = default_pli()
		event_b = default_pli()
		event_c = default_pli()

		image = '/home/alpine/source/cotdantic/images/cli_tool.png'
		attachment = Attachment(
			file=Path(image),
			uid=event_a.uid,
		)

		filename = Path(f'datapack-{event_a.uid}.zip')
		datapack = DataPack()
		datapack.events.extend(
			[
				event_a,
				event_b,
				event_c,
			]
		)
		datapack.attachments.append(attachment)
		datapack.zip(temp_dir / filename)
		zip_file = temp_dir / filename

		url = f'http://192.168.1.200:{port}/{filename}'

		file_share = FileShare(
			filename=str(filename),
			sender_url=url,
			size_in_bytes=zip_file.lstat().st_size,
			sha256=sha256_file(zip_file),
			sender_callsign='cotdantic',
			sender_uid=cot_uid,
			name=filename.stem,
			peer_hosted=True,
		)

		detail = Detail(
			file_share=file_share,
			ack_request=AckRequest(
				uid=str(uuid.uuid4()),
				tag=filename.stem,
				ack_requested=True,
			),
		)

		event = Event(
			type='b-f-t-r',
			how='h-e',
			point=Point(lat=0, lon=0, hae=0),
			detail=detail,
		)

		xml = event.to_xml(pretty_print=True)
		proto = bytes(event)

		wintak = ('192.168.1.X', 4242)
		atak = ('192.168.1.X', 4242)

		com.send(proto, wintak)
		com.send(proto, atak)

		time.sleep(1000)

	assert True


if __name__ == '__main__':
	test_zip_creation()
