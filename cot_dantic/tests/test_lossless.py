from cotdantic import *
from cotdantic import converters
from takproto.functions import msg2proto
import takproto
import lxml.etree as ET

# monkey patch XML encoder
takproto.functions.ET = ET


def default_cot():

    point = Point(lat=38.711, lon=-77.147, hae=10, ce=5.0, le=10.0)
    contact = Contact(
        callsign="Delta1",
        endpoint="192.168.0.100:4242:tcp",
        phone="+12223334444",
    )
    takv = Takv(
        device="virtual",
        platform="virtual",
        os="linux",
        version="1.0.0",
    )
    group = Group(name="squad_1", role="SquadLeader")
    status = Status(battery=50)
    precisionLocation = PrecisionLocation(altsrc="gps", geopointsrc="m-g")
    link = Link(parent_callsign="DeltaPlatoon", relation="p-l")
    alias = Alias(Droid="special_system")
    track = Track(speed=1, course=0)
    detail = Detail(
        contact=contact,
        takv=takv,
        group=group,
        status=status,
        precisionlocation=precisionLocation,
        link=link,
        alias=alias,
        track=track,
    )
    event = Event(
        type="a-f-G-U-C-I",
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


def test_proto_lossless():
    event_src = default_cot()
    # takproto does not support contact.phone
    event_src.detail.contact.phone = None
    proto = bytes(event_src)
    event_dst = Event.from_bytes(proto)
    assert event_src == event_dst


def test_message_custom():
    event_src = default_cot()
    proto = event_src.to_bytes()
    message = converters.model2message(event_src)
    proto_custom = bytes(msg2proto(message))
    assert proto == proto_custom


def test_custom_detail():

    from pydantic_xml import attr, element, BaseXmlModel
    from typing import Optional

    event_src = default_cot()
    event_src.detail.contact.phone = None

    class CustomElement(BaseXmlModel, tag="target_description"):
        hair_color: str = attr()
        eye_color: str = attr()

    class CustomDetail(Detail):
        description: Optional[CustomElement] = element(default=None)

    class CustomEvent(EventBase[CustomDetail]):
        pass

    description = CustomElement(
        hair_color="brown",
        eye_color="blue",
    )

    customn_detail = CustomDetail(
        contact=event_src.detail.contact,
        takv=event_src.detail.takv,
        group=event_src.detail.group,
        status=event_src.detail.status,
        precisionlocation=event_src.detail.precisionlocation,
        link=event_src.detail.link,
        alias=event_src.detail.alias,
        track=event_src.detail.track,
        description=description,
    )

    custom_event = CustomEvent(
        type="a-f-G-U-C-I",
        point=event_src.point,
        detail=customn_detail,
    )

    proto = custom_event.to_bytes()
    model = CustomEvent.from_bytes(proto)

    assert model == custom_event


if __name__ == "__main__":
    # test_xml_lossless()
    # test_model_lossless()
    # test_proto_lossless()
    # test_message_custom()
    test_custom_detail()