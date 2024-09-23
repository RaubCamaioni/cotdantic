from .models import (
    Event,
    Point,
    Contact,
    Group,
    Status,
    Takv,
    PrecisionLocation,
    Detail,
    epoch2iso,
)
from takproto import parse_proto, xml2proto
from pydantic_xml import BaseXmlModel
import xml.etree.ElementTree as ET


def is_xml(data: bytes) -> bool:
    try:
        return ET.fromstring(data.decode())
    except ET.ParseError:
        return None
    except UnicodeDecodeError:
        return None


def is_proto(data: bytes) -> bool:
    try:
        tak_message = parse_proto(data)
        return bool(tak_message)
    except Exception as e:
        return False


def parse_cot(data):

    if is_xml(data):
        p = xml2proto(data)
        return True, parse_proto(p)

    if is_proto(data):
        return True, parse_proto(data)

    return False, None


def proto2model(proto: bytes) -> Event:
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

    contact = Contact(
        callsign=proto_contact.callsign,
        endpoint=proto_contact.endpoint,
    )
    contact = contact if any(contact.model_dump().values()) else None

    status = Status(
        battery=proto_status.battery or None,
    )
    status = status if any(status.model_dump().values()) else None

    takv = Takv(
        device=proto_takv.device or None,
        platform=proto_takv.platform or None,
        os=proto_takv.os or None,
        version=proto_takv.version or None,
    )
    takv = takv if any(takv.model_dump().values()) else None

    pl = PrecisionLocation(
        geopointsrc=proto_pl.geopointsrc or None,
        altsrc=proto_pl.altsrc or None,
    )
    pl = pl if any(pl.model_dump().values()) else None

    group = Group(
        name=proto_detail.group.name,
        role=proto_detail.group.role,
    )

    detail = Detail.from_xml(f"<detail>{proto_detail.xmlDetail}</detail>")

    if detail.contact is None:
        detail.contact = contact

    if detail.group is None:
        detail.group = group

    detail.status = status
    detail.takv = takv
    detail.precisionlocation = pl

    event = Event(
        type=proto_event.type,
        uid=proto_event.uid,
        how=proto_event.how,
        time=epoch2iso(proto_event.sendTime),
        start=epoch2iso(proto_event.startTime),
        stale=epoch2iso(proto_event.staleTime),
        point=point,
        detail=detail,
    )

    return event


def model2proto(model: BaseXmlModel):
    xml = model.to_xml()
    return xml2proto(xml)
