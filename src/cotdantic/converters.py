from .models import (
	EventBase,
	Event,
	Point,
	Contact,
	Group,
	Status,
	Takv,
	PrecisionLocation,
	Detail,
	Track,
	epoch2iso,
)

from pydantic_xml import BaseXmlModel
import xml.etree.ElementTree as ET
from typing import get_args

from takproto import parse_proto, xml2proto
from takproto.proto import TakMessage
from takproto.functions import format_time, msg2proto

PROTO_KNOWN_ELEMENTS = {
	'contact',
	'group',
	'precision_location',
	'status',
	'takv',
	'track',
	'raw_xml',  # do not encode
}


def is_xml(data: bytes) -> bool:
	try:
		return ET.fromstring(data.decode())
	except (ET.ParseError, UnicodeDecodeError):
		return False


def is_proto(data: bytes) -> bool:
	try:
		tak_message = parse_proto(data)
		return bool(tak_message)
	except TypeError:
		return False


def parse_cot(data):
	if is_xml(data):
		p = xml2proto(data)
		return True, parse_proto(p)

	if is_proto(data):
		return True, parse_proto(data)

	return False, None


def proto2model(cls: EventBase, proto: bytes) -> EventBase:
	proto_message = parse_proto(proto)
	proto_event = proto_message.cotEvent
	proto_detail = proto_event.detail
	proto_contact = proto_detail.contact
	proto_status = proto_detail.status
	proto_takv = proto_detail.takv
	proto_pl = proto_detail.precisionLocation

	point = Point(
		lat=proto_event.lat,
		lon=proto_event.lon,
		hae=proto_event.hae,
		le=proto_event.le,
		ce=proto_event.ce,
	)

	contact = None
	if proto_detail.HasField('contact'):
		contact = Contact(
			callsign=proto_contact.callsign or None,
			endpoint=proto_contact.endpoint or None,
		)

	status = None
	if proto_detail.HasField('status'):
		status = Status(
			battery=proto_status.battery or None,
		)

	group = None
	if proto_detail.HasField('group'):
		group = Group(
			name=proto_detail.group.name or None,
			role=proto_detail.group.role or None,
		)

	takv = None
	if proto_detail.HasField('takv'):
		takv = Takv(
			device=proto_takv.device or None,
			platform=proto_takv.platform or None,
			os=proto_takv.os or None,
			version=proto_takv.version or None,
		)

	pl = None
	if proto_detail.HasField('precisionLocation'):
		pl = PrecisionLocation(
			geopointsrc=proto_pl.geopointsrc or None,
			altsrc=proto_pl.altsrc or None,
		)

	track = None
	if proto_detail.HasField('track'):
		track = Track(
			speed=proto_detail.track.speed,
			course=proto_detail.track.course,
		)

	annotation = cls.model_fields['detail'].annotation
	types_in_union = get_args(annotation)
	custom_type = next(t for t in types_in_union if t is not None)

	raw_xml = f'<detail>{proto_detail.xmlDetail}</detail>'
	detail: Detail = custom_type.from_xml(raw_xml)
	detail.contact = detail.contact or contact
	detail.group = detail.group or group
	detail.track = track
	detail.status = status
	detail.takv = takv
	detail.precision_location = pl

	# TODO: add only xml that is not captured and add back to proto
	detail.raw_xml = raw_xml

	event = cls(
		type=proto_event.type,
		access=proto_event.access or None,
		qos=proto_event.qos or None,
		opex=proto_event.opex or None,
		uid=proto_event.uid,
		how=proto_event.how,
		time=epoch2iso(proto_event.sendTime),
		start=epoch2iso(proto_event.startTime),
		stale=epoch2iso(proto_event.staleTime),
		point=point,
		detail=detail,
	)

	return event


def model2xml2proto(model: EventBase):
	xml = model.to_xml()
	return bytes(xml2proto(xml))


def model2proto(model: EventBase) -> bytes:
	message = model2message(model)
	message.takControl.minProtoVersion = 0
	message.takControl.maxProtoVersion = 0
	message.takControl.contactUid = ''
	return bytes(msg2proto(message, None))


def model2message(model: EventBase) -> TakMessage:
	tak_message = TakMessage()

	geo_chat = 'GeoChat.' in model.uid

	if geo_chat:
		tak_message.takControl.contactUid = model.uid.split('.')[1]

	tak_event = tak_message.cotEvent
	tak_event.type = model.type
	tak_event.access = model.access or ''
	tak_event.qos = model.qos or ''
	tak_event.opex = model.opex or ''
	tak_event.uid = model.uid
	tak_event.how = model.how
	tak_event.sendTime = format_time(model.time)
	tak_event.startTime = format_time(model.start)
	tak_event.staleTime = format_time(model.stale)
	tak_event.lat = model.point.lat
	tak_event.lon = model.point.lon
	tak_event.hae = model.point.hae
	tak_event.ce = model.point.ce
	tak_event.le = model.point.le

	detail = model.detail
	if detail is None:
		return tak_message

	tak_detail = tak_event.detail

	if geo_chat:
		detail_str = detail.to_xml().decode()
		tak_detail.xmlDetail = detail_str[8:-9]

	else:
		xml_string = b''

		for name, _ in detail.model_fields.items():
			if name in PROTO_KNOWN_ELEMENTS:
				continue

			instance: BaseXmlModel = getattr(detail, name)

			if instance is None:
				continue

			xml_string += instance.to_xml()

		tak_detail.xmlDetail = xml_string.decode()

	if detail.contact is not None:
		tak_detail.contact.endpoint = detail.contact.endpoint or ''
		tak_detail.contact.callsign = detail.contact.callsign or ''

	if detail.group is not None:
		tak_detail.group.name = detail.group.name or ''
		tak_detail.group.role = detail.group.role or ''

	if detail.precision_location is not None:
		tak_detail.precisionLocation.geopointsrc = detail.precision_location.geopointsrc
		tak_detail.precisionLocation.altsrc = detail.precision_location.altsrc

	if detail.status is not None:
		tak_detail.status.battery = detail.status.battery

	if detail.takv is not None:
		tak_detail.takv.device = detail.takv.device
		tak_detail.takv.platform = detail.takv.platform
		tak_detail.takv.os = detail.takv.os
		tak_detail.takv.version = detail.takv.version

	if detail.track is not None:
		tak_detail.track.speed = detail.track.speed or 0.0
		tak_detail.track.course = detail.track.course or 0.0

	return tak_message
