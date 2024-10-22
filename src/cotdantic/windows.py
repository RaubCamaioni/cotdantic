from collections import deque
from itertools import islice
import textwrap
import platform
import curses


class Pad:
	def __init__(self, height, width, title=None):
		self.title = title or ''
		self.pad = curses.newpad(height, width)
		self.max_x = width - 2
		self.max_y = height - 2
		self._text = deque(maxlen=1000)
		self.selected = False
		self.paused = False
		self.print_offset = 0

	def toggle_pause(self):
		self.paused = not self.paused

	def border(self):
		self.pad.border()
		self.pad.move(0, 5)
		attr = 1 if self.selected else 0
		attr = 2 if self.paused else attr
		self.pad.addnstr(self.title, self.max_x, curses.color_pair(attr))

	def clear(self):
		self.pad.clear()

	def erase(self):
		self.pad.erase()

	def refresh(self, x1, y1, x2, y2, x3, y3):
		self.pad.refresh(x1, y1, x2, y2, x3, y3)

	def print(self, text: str):
		split_newline = text.split('\n')
		for newline in split_newline:
			if newline == '':
				if self.print_offset != 0:
					self._up_scroll(1)
				self._text.append('')
				continue
			split_wrapped = textwrap.wrap(newline, width=self.max_x)
			for line in split_wrapped:
				if self.print_offset != 0:
					self._up_scroll(1)
				self._text.append(line)

	def update(self, key: int):
		if not self.selected:
			return

		if key == curses.KEY_UP:
			self._up_scroll(2)
		elif key == curses.KEY_DOWN:
			self._down_scroll(2)
		elif key == curses.KEY_BACKSPACE:
			self.print_offset = 0

	def _up_scroll(self, lines: int):
		self.print_offset = min(self.print_offset + lines, len(self._text) - self.max_y)

	def _down_scroll(self, lines: int):
		self.print_offset = max(self.print_offset - lines, 0)

	def render(self):
		length = len(self._text)
		index = max(length - self.print_offset - self.max_y, 0)
		array = islice(self._text, index, index + self.max_y)
		for i, line in enumerate(array, 1):
			self.pad.move(i, 1)
			self.pad.addnstr(line, self.max_x)


class PadHandler:
	def __init__(self, stdscr: curses.window):
		curses.use_default_colors()
		curses.curs_set(0)
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
		curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)

		self.stdscr = stdscr
		self.stdscr.clear()
		self.h, self.w = stdscr.getmaxyx()

		if platform.system() == 'Windows':
			self.h = self.h - 1
			self.w = self.w - 1

		self.ht = self.h - self.h // 3
		self.hb = self.h - self.ht
		self.wl = self.w // 3
		self.wr = self.w - self.wl

		self.topa = Pad(self.ht, self.w, 'Situational Awareness')
		self.botl = Pad(self.hb, self.wl, 'Contacts')
		self.botr = Pad(self.hb, self.wr - 1, 'Chat')

		self.selected = 0
		self.update_selected()

	def next_select(self, next: int = 1):
		self.selected = (self.selected + next) % 3
		self.update_selected()

	def update_selected(self):
		self.topa.selected = bool(0 == self.selected)
		self.botl.selected = bool(1 == self.selected)
		self.botr.selected = bool(2 == self.selected)

	def update(self, key: int):
		self.topa.update(key)
		self.botl.update(key)
		self.botr.update(key)

	def refresh(self):
		self.topa.erase()
		self.botl.erase()
		self.botr.erase()

		self.topa.border()
		self.botl.border()
		self.botr.border()

		self.topa.render()
		self.botl.render()
		self.botr.render()

		self.topa.refresh(0, 0, 0, 0, self.ht, self.w)
		self.botl.refresh(0, 0, self.ht, 0, self.h, self.wl)
		self.botr.refresh(0, 0, self.ht, self.wl + 1, self.h, self.w)
