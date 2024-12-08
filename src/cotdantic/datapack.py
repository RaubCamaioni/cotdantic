from dataclasses import dataclass, field
from pydantic_xml import element, attr
from typing import Optional, List
from cotdantic.models import *
from pathlib import Path
import http.server
import socketserver
import threading
import zipfile
import hashlib
import uuid
import os


def sha256_file(path: Path):
	hasher = hashlib.sha256()
	with open(path, 'rb') as f:
		for byte_block in iter(lambda: f.read(4096), b''):
			hasher.update(byte_block)
		return hasher.hexdigest()


class FileServer(threading.Thread):
	def __init__(self, port=8000, directory='.'):
		super().__init__()
		self.port = port
		self.directory = directory
		self.daemon = True
		self.httpd = None
		self.download_event = threading.Event()
		socketserver.TCPServer.allow_reuse_address = True

	def run(self):
		Handler = self.get_handler()
		os.chdir(self.directory)

		with socketserver.TCPServer(('0.0.0.0', self.port), Handler) as httpd:
			self.httpd = httpd
			httpd.serve_forever()

	def get_handler(self):
		download_event = self.download_event

		class CustomHandler(http.server.SimpleHTTPRequestHandler):
			def do_GET(self):
				super().do_GET()
				download_event.set()

		return CustomHandler

	def serve_until_download(self):
		self.download_event.wait()
		self.stop()

	def stop(self):
		if self.httpd:
			self.httpd.shutdown()
			self.httpd.server_close()

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.stop()


class Parameter(CotBase, tag='Parameter'):
	name: Optional[str] = attr(default=None)
	value: Optional[str] = attr(default=None)


class Configuration(CotBase, tag='Configuration'):
	parameters: List[Parameter] = element(default=[])


class Content(CotBase, tag='Content'):
	zip_entry: Optional[str] = attr(name='zipEntry', default=None)
	ignore: Optional[bool] = attr(default=None)
	parameters: List[Parameter] = element(default=[])


class Contents(CotBase, tag='Contents'):
	contents: List[Content] = element(default=[])


class MissionPackageManifest(CotBase, tag='MissionPackageManifest'):
	version: int = attr(default=2)
	configuration: Optional[Configuration] = element(default=None)
	contents: Optional[Contents] = element(default=None)


@dataclass
class Attachment:
	uid: str
	file: Path
	temp_uid: str = field(default_factory=lambda: str(uuid.uuid4()))

	def __post_init__(self):
		self.file = Path(self.file)


class DataPack:
	def __init__(self):
		self.events: List[Event] = []
		self.attachments: List[Attachment] = []

	def zip(self, file: str):
		file: Path = Path(file)

		configuration = Configuration()
		configuration.parameters.append(Parameter(name='name', value=file.stem))
		configuration.parameters.append(Parameter(name='uid', value=str(uuid.uuid4())))
		contents = Contents()
		mission_pack = MissionPackageManifest(
			configuration=configuration,
			contents=contents,
		)

		with zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED) as zip:
			for e in self.events:
				zip_path = f'{e.uid}/{e.uid}.cot'
				zip.writestr(zip_path, e.to_xml(pretty_print=True))
				content = Content(
					zip_entry=zip_path,
					ignore='false',
					parameters=[Parameter(name='uid', value=e.uid)],
				)
				contents.contents.append(content)

			for a in self.attachments:
				zip_path = f'{a.temp_uid}/{a.file.name}'
				zip.write(a.file, zip_path)
				content = Content(
					zip_entry=zip_path,
					ignore='false',
					parameters=[Parameter(name='uid', value=a.uid)],
				)
				contents.contents.append(content)

			zip.writestr('MANIFEST/manifest.xml', mission_pack.to_xml(pretty_print=True))

	@classmethod
	def unzip(cls, file: str):
		"""TODO: function is not implimented"""
		pass


def create_file_share(
	path: Path,
	url: str,
	sender_uid: str,
	sender_callsign: str,
):
	file_share = FileShare(
		filename=str(path.name),
		sender_url=url,
		size_in_bytes=path.lstat().st_size,
		sha256=sha256_file(path),
		sender_callsign=sender_callsign,
		sender_uid=sender_uid,
		name=path.stem,
		peer_hosted=True,
	)

	detail = Detail(
		file_share=file_share,
		ack_request=AckRequest(
			uid=str(uuid.uuid4()),
			tag=path.stem,
			ack_requested=True,
		),
	)

	event = Event(
		type='b-f-t-r',
		how='h-e',
		point=Point(lat=0, lon=0, hae=0),
		detail=detail,
	)

	return event
