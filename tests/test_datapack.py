from cotdantic import *
import random
import hashlib
from pathlib import Path


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
		while True:
			chunk = file.read(4096)
			if not chunk:
				break
			hasher.update(chunk)
	return hasher.hexdigest()


def test_zip_creation():
	from cotdantic.datapack import DataPack, Attachment, FileServer
	from cotdantic.multicast import TcpListener
	from contextlib import ExitStack
	from pathlib import Path
	import tempfile
	import time

	with ExitStack() as stack:
		temp_dir = Path(stack.enter_context(tempfile.TemporaryDirectory()))
		_ = stack.enter_context(FileServer(directory=temp_dir))
		com = stack.enter_context(TcpListener(4242))

		# create datapack
		event_a = default_pli()
		event_b = default_pli()
		event_c = default_pli()
		attachment = Attachment(file=Path('/home/alpine/source/cotdantic/images/cli_tool.png'), uid=event_a.uid)
		datapack = DataPack()
		datapack.events.extend([event_a, event_b, event_c])
		datapack.attachments.append(attachment)
		filename = Path(f'datapack-{event_a.uid}.zip')
		datapack.zip(temp_dir / filename)
		zip_file = temp_dir / filename

		# create download message
		point = Point(lat=0, lon=0, hae=0)
		file_share = FileShare(
			filename=str(filename),
			senderUrl=f'http://192.168.1.200:8000/{filename}',
			size_in_bytes=zip_file.lstat().st_size,
			sha256=sha256_file(zip_file),
			sender_callsign='cotdantic',
			name=filename.stem,
			peerHosted=True,
		)

		detail = Detail(
			file_share=file_share,
		)

		event = Event(
			type='b-f-t-r',
			point=point,
			detail=detail,
		)

		server = ('192.168.1.171', 4242)
		com.send(bytes(event), server)

		time.sleep(60)

	assert True
