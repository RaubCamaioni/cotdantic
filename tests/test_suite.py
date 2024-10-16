from takproto.functions import msg2proto
from cotdantic import converters
from cotdantic import *
import lxml.etree as ET
import takproto
import pytest

# monkey patch XML encoder
takproto.functions.ET = ET


def default_cot():
	point = Point(lat=38.711, lon=-77.147, hae=10, ce=5.0, le=10.0)
	contact = Contact(
		callsign='Delta1',
		endpoint='192.168.0.100:4242:tcp',
		phone='+12223334444',
	)
	takv = Takv(
		device='virtual',
		platform='virtual',
		os='linux',
		version='1.0.0',
	)
	group = Group(name='squad_1', role='SquadLeader')
	status = Status(battery=50)
	precision_location = PrecisionLocation(altsrc='gps', geopointsrc='m-g')
	link = Link(parent_callsign='DeltaPlatoon', relation='p-l')
	alias = Alias(Droid='special_system')
	track = Track(speed=1, course=0)
	detail = Detail(
		contact=contact,
		takv=takv,
		group=group,
		status=status,
		precision_location=precision_location,
		link=link,
		alias=alias,
		track=track,
	)

	event = Event(
		type='a-f-G-U-C-I',
		point=point,
		detail=detail,
	)

	return event


def test_xml_lossless():
	xml_src = default_cot().to_xml()
	event = Event.from_xml(xml_src)
	xml_dst = event.to_xml()
	assert xml_src == xml_dst


def test_model_lossless():
	event_src = default_cot()
	xml = event_src.to_xml()
	event_dst = Event.from_xml(xml)
	assert event_src == event_dst


@pytest.mark.skip(reason='takproto does not copy takcontrol to proto')
def test_proto_lossless():
	event_src = default_cot()
	# takproto does not support contact.phone
	event_src.detail.contact.phone = None
	proto = bytes(event_src)
	event_dst = Event.from_bytes(proto)
	# don't compair raw_xml
	event_src.detail.raw_xml = ''
	event_dst.detail.raw_xml = ''
	assert event_src == event_dst


@pytest.mark.skip(reason='takproto does not copy takcontrol to proto')
def test_message_custom():
	from takproto.constants import TAKProtoVer

	event_src = default_cot()
	event_src.detail.contact.phone = None

	# direct method
	direct_proto = event_src.to_bytes()

	# xml method
	xml = event_src.to_xml()
	xml_proto = bytes(converters.xml2proto(xml, TAKProtoVer.MESH))

	assert direct_proto == xml_proto


@pytest.mark.skip(reason='takproto does not copy takcontrol to proto')
def test_custom_detail():
	from pydantic_xml import attr, element, BaseXmlModel
	from typing import Optional

	event_src = default_cot()
	event_src.detail.contact.phone = None

	class CustomElement(BaseXmlModel, tag='target_description'):
		hair_color: str = attr()
		eye_color: str = attr()

	class CustomDetail(Detail):
		description: Optional[CustomElement] = element(default=None)

	class CustomEvent(EventBase[CustomDetail]):
		pass

	description = CustomElement(
		hair_color='brown',
		eye_color='blue',
	)

	customn_detail = CustomDetail(
		contact=event_src.detail.contact,
		takv=event_src.detail.takv,
		group=event_src.detail.group,
		status=event_src.detail.status,
		precision_location=event_src.detail.precision_location,
		link=event_src.detail.link,
		alias=event_src.detail.alias,
		track=event_src.detail.track,
		description=description,
	)

	custom_event = CustomEvent(
		type='a-f-G-U-C-I',
		point=event_src.point,
		detail=customn_detail,
	)

	proto = custom_event.to_bytes()
	model = CustomEvent.from_bytes(proto)

	model.detail.raw_xml = ''
	custom_event.detail.raw_xml = ''

	assert model == custom_event


def test_cot_types():
	assert str(atom.hostile.ground.civilian) == 'a-h-G-C'
