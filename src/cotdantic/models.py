from typing import TypeVar, Generic, Optional, Union, Any, List, get_args
from pydantic_xml import element, attr, xml_field_serializer
from pydantic_xml.element import XmlElementWriter
from pydantic_xml.model import XmlEntityInfo
from functools import partial, lru_cache
import xml.etree.ElementTree as ET
from pydantic import Field
from uuid import uuid4
import pydantic_xml
import datetime


class CotBase(pydantic_xml.BaseXmlModel, search_mode='unordered'):
	def to_xml(
		self,
		*,
		skip_empty: bool = False,
		exclude_none: bool = True,
		exclude_unset: bool = False,
		**kwargs: Any,
	) -> Union[str, bytes]:
		return super().to_xml(
			skip_empty=skip_empty,
			exclude_none=exclude_none,
			exclude_unset=exclude_unset,
			**kwargs,
		)


T = TypeVar('T', bound=CotBase)


def datetime2iso(time: datetime.datetime):
	# return f'{time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]}Z'
	return f'{time.strftime("%Y-%m-%dT%H:%M:%S.%f")}Z'


def epoch2iso(epoch: int):
	time = datetime.datetime.fromtimestamp(epoch / 1000, tz=datetime.timezone.utc)
	return datetime2iso(time)


def iso2epoch(iso: str) -> int:
	time = datetime.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)
	return int(time.timestamp() * 1000)


def isotime(hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
	current = datetime.datetime.now(datetime.timezone.utc)
	offset = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
	time = current + offset
	return datetime2iso(time)


class Point(CotBase, tag='point'):
	lat: float = attr()
	lon: float = attr()
	hae: float = attr(default=999999)
	le: float = attr(default=999999)
	ce: float = attr(default=999999)


class Contact(CotBase, tag='contact'):
	endpoint: Optional[str] = attr(default=None)
	phone: Optional[str] = attr(default=None)
	callsign: Optional[str] = attr(default=None)


class Link(CotBase, tag='link'):
	type: Optional[str] = attr(default=None)
	uid: Optional[str] = attr(default=None)
	parent_callsign: Optional[str] = attr(default=None)
	relation: Optional[str] = attr(default=None)
	remarks: Optional[str] = attr(default=None)
	production_time: Optional[str] = attr(default=None)
	point: Optional[str] = attr(default=None)
	callsign: Optional[str] = attr(default=None)


class Status(CotBase, tag='status'):
	readiness: Optional[bool] = attr(default=None)
	battery: Optional[int] = attr(default=None)


class Group(CotBase, tag='__group'):
	name: Optional[str] = attr()
	role: Optional[str] = attr()


class Takv(CotBase, tag='takv'):
	device: Optional[str] = attr()
	platform: Optional[str] = attr()
	os: Optional[str] = attr()
	version: Optional[str] = attr()


class Track(CotBase, tag='track'):
	speed: Optional[float] = attr()
	course: Optional[float] = attr()


class PrecisionLocation(CotBase, tag='precisionlocation'):
	geopointsrc: Optional[str] = attr(default=None)
	altsrc: Optional[str] = attr(default=None)


class Alias(CotBase, tag='uid'):
	Droid: Optional[str] = attr(default=None)


class Image(CotBase, tag='image'):
	bytes: str
	size: int = attr()
	height: int = attr()
	width: int = attr()
	mine: str = attr(default='image/jpg')
	type: str = attr(default='EO')


class Attachment(CotBase, tag='attachment'):
	type: Optional[str] = attr(default=None)
	xml: Optional[str] = attr(default=None)


class SendData(CotBase, tag='sendData'):
	sent: Optional[int] = attr(default=None)


class Archive(CotBase, tag='archive'):
	pass


class Usericon(CotBase, tag='usericon'):
	iconsetpath: Optional[str] = attr(default=None)


class HeightUnit(CotBase, tag='height_unit'):
	unit: int


class ConnectionEntry(CotBase, tag='ConnectionEntry'):
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


class Video(CotBase, tag='__video'):
	connection_entry: ConnectionEntry = element()


class Remarks(CotBase, tag='remarks'):
	text: Optional[str] = None
	source: Optional[str] = attr(default=None)
	source_id: Optional[str] = attr(name='sourceID', default=None)
	to: Optional[str] = attr(default=None)
	time: Optional[str] = attr(default_factory=isotime)


class ServerDestination(CotBase, tag='__serverdestination'):
	destinations: Optional[str] = attr(default=None)


class ChatGroup(CotBase, tag='chatgrp'):
	id: Optional[str] = attr(default=None)
	uid0: Optional[str] = attr(default=None)
	uid1: Optional[str] = attr(default=None)


class Chat(CotBase, tag='__chat'):
	id: Optional[str] = attr(default=None)
	chatroom: Optional[str] = attr(default=None)
	sender_callsign: Optional[str] = attr(name='senderCallsign', default=None)
	group_owner: Optional[bool] = attr(name='groupOwner', default=None)
	message_id: Optional[str] = attr(name='messageId', default=None)
	parent: Optional[str] = attr(default=None)
	chatgrp: Optional[ChatGroup] = element(default=None)


class Hud(CotBase, tag='hud'):
	role: Optional[str] = attr(default=None)


class Planning(CotBase, tag='planning'):
	session_id: Optional[str] = attr(name='sessionId', default=None)


class TakDataPackage(CotBase, tag='takDataPackage'):
	name: Optional[str] = attr(default=None)


class VMF(CotBase, tag='vmf'):
	pass


class Color(CotBase, tag='color'):
	argb: Optional[int] = attr(default=None)


class UniqueID(CotBase, tag='uid'):
	droid: Optional[str] = attr(default=None, name='Droid')

class Navcues(CotBase, tag="__navcues"):
	pass

class RouteInfo(CotBase, tag="__routeinfo"):
	navcues: Optional[Navcues] = element(default=None)

class Detail(CotBase, tag='detail'):
	raw_xml: bytes = Field(exclude=False, default=b'')
	contact: Optional[Contact] = element(default=None)
	chat: Optional[Chat] = element(default=None)
	link: List[Link] = element(default=[])
	takv: Optional[Takv] = element(default=None)
	group: Optional[Group] = element(default=None)
	status: Optional[Status] = element(default=None)
	track: Optional[Track] = element(default=None)
	precision_location: Optional[PrecisionLocation] = element(default=None)
	alias: Optional[Alias] = element(default=None)
	vmf: Optional[VMF] = element(default=None)
	image: Optional[Image] = element(default=None)
	video: Optional[Video] = element(default=None)
	archive: Optional[Archive] = element(default=None)
	usericon: Optional[Usericon] = element(default=None)
	height_unit: Optional[HeightUnit] = element(default=None)
	server_destination: Optional[ServerDestination] = element(default=None)
	attachemnt: Optional[Attachment] = element(default=None)
	send_data: Optional[SendData] = element(default=None)
	tak_data_package: Optional[TakDataPackage] = element(default=None)
	hud: Optional[Hud] = element(default=None)
	planning: Optional[Planning] = element(default=None)
	remarks: Optional[Remarks] = element(default=None)
	color: Optional[Color] = element(default=None)
	uid: Optional[UniqueID] = element(default=None)

	@classmethod
	@lru_cache
	def tags(cls) -> List[str]:
		detail_tags = []
		for _, info in cls.model_fields.items():
			if not isinstance(info, XmlEntityInfo):
				continue
			types_in_union = get_args(info.annotation)
			custom_type = types_in_union[0]
			detail_tags.append(custom_type.__xml_tag__)
		return detail_tags

	@xml_field_serializer('raw_xml')
	def serialize_detail_with_string(self, element: XmlElementWriter, value: bytes, field_name: str) -> None:
		if len(value) == 0:
			return

		for child in ET.fromstring(f'<_raw>{value.decode()}</_raw>'):
			child_element = element.make_element(tag=child.tag, nsmap=None)

			for key, val in child.attrib.items():
				child_element.set_attribute(key, val)

			child_element.set_text(child.text)
			element.append_element(child_element)


class TakControl(CotBase):
	minProtoVersion: int = 0
	maxProtoVersion: int = 0
	contactUid: str = ''


class EventBase(CotBase, Generic[T], tag='event'):
	tak_control: TakControl = Field(exclude=True, default_factory=lambda: TakControl())
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
	def from_bytes(cls, proto: bytes) -> 'EventBase[T]':
		raise NotImplementedError('attached in __init__.py')


class Event(EventBase[Detail]):
	""""""
