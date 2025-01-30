__version__ = '2.1.5'

from .models import *

from . import converters
from .cot_types import atom
import uuid

UID = f'cotdantic-{uuid.getnode()}'
CALLSIGN = 'cotdantic'


def __event_to_bytes(self: EventBase) -> bytes:
	return converters.model2proto(self)


@classmethod
def __event_from_bytes(cls: EventBase, proto: bytes) -> EventBase:
	return converters.proto2model(cls, proto)


@classmethod
def __event_from_cot(cls: EventBase, data: bytes) -> EventBase:
	return converters.parse_cot(data)


EventBase.__bytes__ = __event_to_bytes
EventBase.to_bytes = __event_to_bytes
EventBase.from_bytes = __event_from_bytes
EventBase.from_cot = __event_from_cot
