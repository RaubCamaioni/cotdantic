from pydantic_xml import BaseXmlModel, element, attr
from takproto import parse_proto, xml2proto
from functools import partial
from typing import Optional
from uuid import uuid4
import datetime


def datetime2iso(time: datetime.datetime):
    return f'{time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]}Z'


def cot_time(hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
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


class Link(BaseXmlModel, skip_empty=True):
    relation: Optional[str] = attr(default=None)
    parent_callsign: Optional[str] = attr(default=None)


class Status(BaseXmlModel):
    battery: Optional[int] = attr(default=None)


class Group(BaseXmlModel):
    name: str = element()
    role: str = element()


class Takv(BaseXmlModel):
    device: Optional[str] = attr()
    platform: Optional[str] = attr()
    os: Optional[str] = attr()
    version: Optional[str] = attr()


class Track(BaseXmlModel):
    speed: Optional[float] = attr()
    course: Optional[float] = attr()


class PrecisionLocation(BaseXmlModel):
    geopointsrc: Optional[str] = attr()
    altsrc: Optional[str] = attr()


class Alias(BaseXmlModel):
    Droid: Optional[str] = attr(default=None)


class Detail(BaseXmlModel, tag="detail", skip_empty=True):
    contact: Optional[Contact] = element(default=None)
    takv: Optional[Takv] = element(default=None)
    group: Optional[Group] = element(default=None)
    status: Optional[Status] = element(default=None)
    precisionlocation: Optional[PrecisionLocation] = element(default=None)
    link: Optional[Link] = element(default=None)
    uid: Optional[Alias] = element(default=None)


class Event(BaseXmlModel, tag="event", skip_empty=True):
    version: float = attr(default=2.0)
    type: str = attr()
    uid: str = attr(default_factory=uuid4)
    how: Optional[str] = attr(default="m-g")
    time: str = attr(default_factory=cot_time)
    start: str = attr(default_factory=cot_time)
    stale: str = attr(default_factory=partial(cot_time, minutes=5))
    point: Point = element()
    detail: Optional[Detail] = element(default=None)


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

    detail = Detail.from_xml(f"<detail>{proto_detail.xmlDetail}</detail>")
    if detail.contact is None:
        detail.contact = contact
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


def generate_cot():
    point = Point(lat=38.696644, lon=-77.140433)
    contact = Contact(callsign="DogMan", endpoint="172.16.0.128:4242:tcp")
    detail = Detail(
        contact=contact,
        uid=Alias(Droid="SpecialBoy"),
    )
    event = Event(
        type="a-f-G-U-C-I",
        point=point,
        detail=detail,
    )
    event.type = "a-f-A-M-H-Q-r"

    xml = event.to_xml()

    xml_reconstruct = Event.from_xml(xml)

    return xml_reconstruct, xml


if __name__ == "__main__":

    event, xml = generate_cot()
    proto = model2proto(event)
    recon = proto2model(proto)

    print("Original Model")
    print(event, "\n")
    print("Reconstructed Model")
    print(recon, "\n")
    print("Original XML")
    print(xml, "\n")
    print("Reconstructed XML")
    print(recon.to_xml(), "\n")
    print("Proto from Takproto")
    print(proto, "\n")
