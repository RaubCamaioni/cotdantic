from .models import (
    Point,
    Contact,
    Link,
    EventBase,
    Event,
    Detail,
    Status,
    Group,
    Takv,
    Track,
    PrecisionLocation,
    Alias,
)

from . import converters
from pydantic_xml import BaseXmlModel


def __event_to_bytes(self: "Event") -> bytes:
    return converters.model2proto(self)


@classmethod
def __event_from_bytes(cls: Event, proto: bytes) -> Event:
    return converters.proto2model(cls, proto)


EventBase.__bytes__ = __event_to_bytes
EventBase.to_bytes = __event_to_bytes
EventBase.from_bytes = __event_from_bytes
