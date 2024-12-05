from .models import (
	PrecisionLocation,
	TakControl,
	epoch2iso,
	EventBase,
	iso2epoch,
	Contact,
	CotBase,
	Status,
	Detail,
	Track,
	Event,
	Point,
	Group,
	Takv,
)

import xml.etree.ElementTree as ET
from typing import get_args

from takproto import parse_proto, xml2proto
from takproto.functions import msg2proto
from takproto.proto import TakMessage

PROTO_KNOWN_ELEMENTS = {
	# 'contact', # check non-standard values
	# 'status', # check non-standard values
	'precision_location',  # sometime in details
	'raw_xml',
	'group',
	'track',
	'takv',
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
	tak_control = proto_message.takControl

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

	precision_location = None
	if proto_detail.HasField('precisionLocation'):
		precision_location = PrecisionLocation(
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
	custom_type = types_in_union[0]

	raw_xml = f'<detail>{proto_detail.xmlDetail}</detail>'
	detail: Detail = custom_type.from_xml(raw_xml)

	detail.precision_location = detail.precision_location or precision_location
	detail.contact = detail.contact or contact
	detail.status = detail.status or status
	detail.group = detail.group or group
	detail.track = track
	detail.takv = takv

	root = ET.fromstring(raw_xml)
	tags = {child.tag for child in root} - set(detail.tags())
	tags = [ET.tostring(root.find(tag), encoding='utf-8') for tag in tags]
	detail.raw_xml = b''.join(tags)

	control = TakControl(
		minProtoVersion=tak_control.minProtoVersion,
		maxProtoVersion=tak_control.maxProtoVersion,
		contactUid=tak_control.contactUid,
	)

	event = cls(
		tak_control=control,
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
	return bytes(msg2proto(message, None))


def model2message(model: EventBase) -> TakMessage:
	tak_message = TakMessage()

	tak_message.takControl.minProtoVersion = model.tak_control.minProtoVersion
	tak_message.takControl.maxProtoVersion = model.tak_control.maxProtoVersion
	tak_message.takControl.contactUid = model.tak_control.contactUid

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
	tak_event.sendTime = iso2epoch(model.time)
	tak_event.startTime = iso2epoch(model.start)
	tak_event.staleTime = iso2epoch(model.stale)
	tak_event.lat = model.point.lat
	tak_event.lon = model.point.lon
	tak_event.hae = model.point.hae
	tak_event.ce = model.point.ce
	tak_event.le = model.point.le

	detail: Detail = model.detail
	if detail is None:
		return tak_message

	tak_detail = tak_event.detail

	encode_contact = True
	encode_status = True

	if geo_chat:
		detail_str = detail.to_xml().decode()
		tak_detail.xmlDetail = detail_str[8:-9]

	else:
		xml_string = b''

		for name, _ in detail.model_fields.items():
			if name in PROTO_KNOWN_ELEMENTS:
				continue

			instance: CotBase = getattr(detail, name)

			if instance is None:
				continue

			if name == 'contact':
				if instance.phone is None:
					continue
				else:
					encode_contact = False

			if name == 'status':
				if instance.readiness is None:
					continue
				else:
					encode_status = False

			if isinstance(instance, list):
				for item in instance:
					xml_string += item.to_xml()
			else:
				xml_string += instance.to_xml()

		xml_string += detail.raw_xml
		tak_detail.xmlDetail = xml_string.decode()

	if encode_contact and detail.contact is not None:
		tak_detail.contact.endpoint = detail.contact.endpoint or ''
		tak_detail.contact.callsign = detail.contact.callsign or ''

	if detail.group is not None:
		tak_detail.group.name = detail.group.name or ''
		tak_detail.group.role = detail.group.role or ''

	if detail.precision_location is not None:
		tak_detail.precisionLocation.geopointsrc = detail.precision_location.geopointsrc or ''
		tak_detail.precisionLocation.altsrc = detail.precision_location.altsrc or ''

	if encode_status and detail.status is not None:
		tak_detail.status.battery = detail.status.battery or 0

	if detail.takv is not None:
		tak_detail.takv.device = detail.takv.device
		tak_detail.takv.platform = detail.takv.platform
		tak_detail.takv.os = detail.takv.os
		tak_detail.takv.version = detail.takv.version

	if detail.track is not None:
		tak_detail.track.speed = detail.track.speed or 0.0
		tak_detail.track.course = detail.track.course or 0.0

	return tak_message
