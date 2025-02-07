__version__ = '2.2.5'

from cotdantic.models import *
from cotdantic.cot_types import atom
import cotdantic.converters as converters
import uuid

COTDANTIC_IOD = f'cotdantic-{uuid.getnode()}'
COTDANTIC_CALLSIGN = 'cotdantic'
