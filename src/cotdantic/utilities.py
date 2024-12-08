from typing import Callable
from .cot_types import atom
from .models import *
import time


def throttle(rate: float):
	last_call = 0

	def decorator(func: Callable):
		def wrapper(*args, **kwargs):
			nonlocal last_call
			now = time.time()
			if now - last_call > rate and rate != -1:
				last_call = now
				return func(*args, **kwargs)
			else:
				return None

		return wrapper

	return decorator
