from .models import (
    Point,
    Contact,
    Link,
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

from .listener import cot_listener


def __event_to_bytes(self: "Event") -> bytes:
    return converters.model2proto(self)


@classmethod
def __event_from_bytes(cls: Event, proto: bytes) -> Event:
    return converters.proto2model(proto)


Event.__bytes__ = __event_to_bytes
Event.from_bytes = __event_from_bytes
