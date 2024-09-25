from .models import (
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

from takproto import parse_proto, xml2proto
from pydantic_xml import BaseXmlModel
import xml.etree.ElementTree as ET
from typing import get_args

from takproto.proto import TakMessage
from takproto.functions import format_time


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


def proto2model(cls, proto: bytes) -> Event:
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

    track = Track(
        speed=proto_detail.track.speed,
        course=proto_detail.track.course,
    )

    annotation = cls.model_fields["detail"].annotation
    types_in_union = get_args(annotation)
    custom_type = next(t for t in types_in_union if t is not None)

    detail = custom_type.from_xml(f"<detail>{proto_detail.xmlDetail}</detail>")

    if detail.contact is None:
        detail.contact = contact

    if detail.group is None:
        detail.group = group

    detail.track = track
    detail.status = status
    detail.takv = takv
    detail.precisionlocation = pl

    event = cls(
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


def model2proto(model: BaseXmlModel) -> bytes:
    xml = model.to_xml()
    return bytes(xml2proto(xml))


def model2message(model: Event) -> TakMessage:

    tak_message = TakMessage()

    geo_chat = "GeoChat." in model.uid

    if geo_chat:
        tak_message.takControl.contactUid = model.uid.split(".")[1]

    tak_event = tak_message.cotEvent
    tak_event.type = model.type
    tak_event.access = model.access or ""
    tak_event.qos = model.qos or ""
    tak_event.opex = model.opex or ""
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
        xml_string = b""
        for name, info in detail.model_fields.items():
            if "known" in info.metadata:
                continue
            instance: BaseXmlModel = getattr(detail, name)
            if instance is None:
                continue
            xml_string += instance.to_xml()
        tak_detail.xmlDetail = xml_string.decode()

    if detail.contact is not None:
        tak_detail.contact.endpoint = detail.contact.endpoint
        tak_detail.contact.callsign = detail.contact.callsign

    if detail.group is not None:
        tak_detail.group.name = detail.group.name
        tak_detail.group.role = detail.group.role

    if detail.precisionlocation is not None:
        tak_detail.precisionLocation.geopointsrc = detail.precisionlocation.geopointsrc
        tak_detail.precisionLocation.altsrc = detail.precisionlocation.altsrc

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
