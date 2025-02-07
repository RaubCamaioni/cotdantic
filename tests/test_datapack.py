from cotdantic.datapack import DataPack, Attachment, FileServer, create_file_share
from cotdantic.templates import default_marker
from cotdantic.multicast import TcpListener
from contextlib import ExitStack
from pathlib import Path
import cotdantic
import tempfile
import random
import uuid


def random_lat_lon():
	# Fort Belvoir
	lat, lon = 38.695514, -77.140035
	return (
		lat + 0.01 * (random.random() - 0.5),
		lon + 0.01 * (random.random() - 0.5),
	)


def send_zip(address_server: str, address_client: str):
	with ExitStack() as stack:
		port = 8002

		temp_dir = Path(stack.enter_context(tempfile.TemporaryDirectory()))
		file_server = stack.enter_context(FileServer(port=port, directory=temp_dir))
		com = stack.enter_context(TcpListener(4242))

		datapack = DataPack()

		event_a = default_marker('marker1', str(uuid.uuid4()), *random_lat_lon())
		event_b = default_marker('marker2', str(uuid.uuid4()), *random_lat_lon())
		event_c = default_marker('marker3', str(uuid.uuid4()), *random_lat_lon())
		datapack.events.extend(
			[
				event_a,
				event_b,
				event_c,
			]
		)

		# Image Attachment Example
		# attachment = Attachment(
		# 	file=Path(image),
		# 	uid=event_a.uid,
		# )
		# datapack.attachments.append(attachment)

		zip_file = temp_dir / Path(f'datapack-{uuid.uuid4()}.zip')
		datapack.zip(zip_file)

		event = create_file_share(
			zip_file,
			f'http://{address_server}:{port}/{zip_file.name}',
			cotdantic.COTDANTIC_IOD,
			cotdantic.COTDANTIC_CALLSIGN,
		)

		com.send(bytes(event), (address_client, 4242))
		file_server.serve_until_download()


if __name__ == '__main__':
	send_zip('192.168.1.200', '192.168.1.171')
