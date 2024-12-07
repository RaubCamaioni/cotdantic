from typing import Optional, List
from pydantic_xml import element, attr
from cotdantic.models import CotBase, Event
from pathlib import Path
import http.server
import socketserver
import threading
import os
from dataclasses import dataclass, field
import zipfile
import socket
import uuid


class FileServer(threading.Thread):
	def __init__(self, port=8000, directory='.'):
		super().__init__()
		self.port = port
		self.directory = directory
		self.daemon = True
		self.httpd = None
		socketserver.TCPServer.allow_reuse_address = True

	def run(self):
		Handler = http.server.SimpleHTTPRequestHandler
		os.chdir(self.directory)

		with socketserver.TCPServer(('0.0.0.0', self.port), Handler) as httpd:
			self.httpd = httpd
			httpd.serve_forever()

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
