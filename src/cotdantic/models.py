from pydantic_xml import BaseXmlModel, element, attr
from functools import partial
from typing import TypeVar, Generic
from typing import Optional
from uuid import uuid4
import datetime

T = TypeVar('T', bound=BaseXmlModel)


def datetime2iso(time: datetime.datetime):
	return f'{time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]}Z'


def isotime(hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
	current = datetime.datetime.now(datetime.timezone.utc)
	offset = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
	time = current + offset
	return datetime2iso(time)


def epoch2iso(epoch: int):
	time = datetime.datetime.fromtimestamp(epoch / 1000, tz=datetime.timezone.utc)
	return datetime2iso(time)


class Point(BaseXmlModel, skip_empty=True):
	lat: float = attr()
	lon: float = attr()
	hae: float = attr(default=0)
	le: float = attr(default=999999)
	ce: float = attr(default=999999)


class Contact(BaseXmlModel, skip_empty=True):
	callsign: Optional[str] = attr(default=None)
	endpoint: Optional[str] = attr(default=None)
	phone: Optional[str] = attr(default=None)


class Link(BaseXmlModel, tag='link', skip_empty=True):
	relation: Optional[str] = attr(default=None)
	parent_callsign: Optional[str] = attr(default=None)


class Status(BaseXmlModel):
	battery: Optional[int] = attr(default=None)


class Group(BaseXmlModel, tag='__group'):
	name: str = attr()
	role: str = attr()


class Takv(BaseXmlModel):
	device: Optional[str] = attr()
	platform: Optional[str] = attr()
	os: Optional[str] = attr()
	version: Optional[str] = attr()


class Track(BaseXmlModel):
	speed: Optional[float] = attr()
	course: Optional[float] = attr()


class PrecisionLocation(BaseXmlModel, tag='precisionlocation'):
	geopointsrc: Optional[str] = attr()
	altsrc: Optional[str] = attr()


class Alias(BaseXmlModel, tag='uid'):
	Droid: Optional[str] = attr(default=None)


class Image(BaseXmlModel):
	bytes: str
	size: int = attr()
	height: int = attr()
	width: int = attr()
	mine: str = attr(default='image/jpg')
	type: str = attr(default='EO')


class ConnectionEntry(BaseXmlModel, tag='ConnectionEntry'):
	protocol: str = attr()
	path: str = attr()
	address: str = attr()
	port: int = attr()
	uid: str = attr()
	alias: str = attr()
	rover_port: int = attr(name='roverPort')
	rtsp_reliable: int = attr(name='rtspReliable')
	ignore_embedded_klv: bool = attr(name='ignoreEmbeddedKLV')
	network_timout: int = attr(name='networkTimeout')
	buffer_time: int = attr(name='bufferTime')


class Video(BaseXmlModel, tag='__video'):
	connection_entry: ConnectionEntry = element()


class Detail(BaseXmlModel, tag='detail', skip_empty=True):
	contact: Optional[Contact] = element(default=None)
	takv: Optional[Takv] = element(default=None)
	group: Optional[Group] = element(default=None)
	status: Optional[Status] = element(default=None)
	track: Optional[Track] = element(default=None)
	precision_location: Optional[PrecisionLocation] = element(default=None)
	link: Optional[Link] = element(default=None)
	alias: Optional[Alias] = element(default=None)
	image: Optional[Image] = element(default=None)
	video: Optional[Video] = element(default=None)


class EventBase(BaseXmlModel, Generic[T], tag='event', skip_empty=True):
	type: str = attr()
	point: Point = element()
	version: float = attr(default=2.0)
	uid: str = attr(default_factory=lambda: str(uuid4()))
	how: Optional[str] = attr(default='m-g')
	time: str = attr(default_factory=isotime)
	start: str = attr(default_factory=isotime)
	stale: str = attr(default_factory=partial(isotime, minutes=5))
	qos: Optional[str] = attr(default=None)
	opex: Optional[str] = attr(default=None)
	access: Optional[str] = attr(default=None)
	detail: Optional[T] = element(default=None)

	def __bytes__(self) -> bytes:
		raise NotImplementedError('attached in __init__.py')

	def to_bytes(self) -> bytes:
		raise NotImplementedError('attached in __init__.py')

	@classmethod
	def from_bytes(cls, proto: bytes) -> 'EventBase':
		raise NotImplementedError('attached in __init__.py')


class Event(EventBase[Detail]):
	""""""
