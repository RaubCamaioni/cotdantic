from contextlib import suppress
from collections import deque
from itertools import islice, cycle
from typing import List, Any, Tuple
import textwrap
import platform
import curses


class Pad:
	def __init__(self, nlines, ncols, title=None):
		self.title = title or ''
		self.pad = curses.newpad(nlines, ncols)
		self.max_y = nlines - 2
		self.max_x = ncols - 2
		self._text: List[Tuple[str, int]] = deque(maxlen=1000)
		self.selected = False
		self.paused = False
		self.index = 0
		self.over_scroll_max = 10

	def toggle_pause(self):
		self.paused = not self.paused

	def border(self):
		self.pad.border()
		self.pad.move(0, 5)
		attr = 1 if self.selected else 0
		attr = 2 if self.paused else attr
		self.pad.addnstr(self.title, self.max_x, curses.color_pair(attr))

	def resize(self, nlines, ncols):
		self.max_y = nlines - 2
		self.max_x = ncols - 2
		self.pad.resize(nlines, ncols)

	def clear(self):
		self.pad.clear()

	def erase(self):
		self.pad.erase()

	def refresh(self, x1, y1, x2, y2, x3, y3):
		self.pad.refresh(x1, y1, x2, y2, x3, y3)

	def print(self, text: Any, color: int = 0):
		text: str = str(text)
		new_text = text.split('\n')
		length = len(self._text)
		scroll_end = self.index >= length - self.max_y
		over_scroll = max(self.index + self.max_y - length, 0)
		self._text.extend([(line, color) for line in new_text])
		if scroll_end:
			self._scroll_end(over_scroll=over_scroll)

	def wrap_line(self, line: str):
		if line == '':
			return [line]
		return textwrap.wrap(line, width=self.max_x)

	def update(self, key: int):
		if not self.selected:
			return

		if key == curses.KEY_UP:
			self._up_scroll(1)
		elif key == curses.KEY_DOWN:
			self._down_scroll(1)
		elif key == curses.KEY_ENTER:
			self._scroll_end()

	def _scroll_end(self, over_scroll: int = 0):
		length = len(self._text)
		if length > self.max_y:
			self.index = length - self.max_y + over_scroll
		else:
			self.index = 0

	def _up_scroll(self, lines: int):
		self.index = max(self.index - lines, 0)

	def _down_scroll(self, lines: int):
		if len(self._text) < self.max_y:
			self.index = 0
		elif len(self._text) > self.max_y - self.over_scroll_max:
			self.index = min(self.index + lines, len(self._text) - self.max_y + self.over_scroll_max)
		else:
			self.index = 0

	def render(self):
		text_color = islice(self._text, self.index, self.index + self.max_y)
		display_index = 0
		for text, color in text_color:
			for wrapped_text in self.wrap_line(text):
				if display_index > self.max_y - 1:
					return
				display_index += 1
				self.pad.move(display_index, 1)
				self.pad.addnstr(wrapped_text, self.max_x, curses.color_pair(color))


class PadHandler:
	def __init__(self, stdscr: curses.window):
		curses.use_default_colors()
		curses.curs_set(0)
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
		curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
		curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED)

		self.running = True
		self.stdscr = stdscr
		self.stdscr.nodelay(True)
		self.stdscr.clear()
		self.h, self.w = self.stdscr.getmaxyx()

		self.h = self.h
		self.w = self.w

		self.ht = self.h - self.h // 4
		self.hb = self.h - self.ht
		self.wl = self.w // 3
		self.wr = self.w - self.wl

		self.topa = Pad(self.ht, self.w, 'Situational Awareness')
		self.botl = Pad(self.hb, self.wl, 'Contacts')
		self.botr = Pad(self.hb, self.wr, 'Chat')

		self.selected = 0
		self.update_selected()

	def too_small(self):
		self.h, self.w = self.stdscr.getmaxyx()
		return self.w < 10 or self.h < 10

	def handle_resize(self):
		if self.too_small():
			return

		self.h, self.w = self.stdscr.getmaxyx()

		if platform.system() == 'Windows':
			self.h = self.h - 1
			self.w = self.w - 1

		self.ht = self.h - self.h // 4
		self.hb = self.h - self.ht
		self.wl = self.w // 3
		self.wr = self.w - self.wl

		self.topa.resize(self.ht, self.w)
		self.botl.resize(self.hb, self.wl)
		self.botr.resize(self.hb, self.wr)

	def next_select(self, next: int = 1):
		self.selected = (self.selected + next) % 3
		self.update_selected()

	def update_selected(self):
		self.topa.selected = bool(0 == self.selected)
		self.botl.selected = bool(1 == self.selected)
		self.botr.selected = bool(2 == self.selected)

	def update(self):
		key = self.stdscr.getch()

		if key == ord('q'):
			self.running = False
			return
		elif key == curses.KEY_RIGHT:
			self.next_select()
		elif key == curses.KEY_LEFT:
			self.next_select(next=-1)
		elif key == curses.KEY_RESIZE:
			self.handle_resize()

		self.topa.update(key)
		self.botl.update(key)
		self.botr.update(key)

	def too_small_splash(self):
		self.stdscr.erase()
		self.h, self.w = self.stdscr.getmaxyx()

		splash = cycle('CONSOLE-TOO-SMALL-')
		list(islice(splash, self.w))
		for i in range(self.h - 1):
			self.stdscr.addstr(i, 0, ''.join(islice(splash, self.w)))

		with suppress(curses.error):
			self.stdscr.refresh()

	def refresh(self):
		if self.too_small():
			self.too_small_splash()
			return

		self.topa.erase()
		self.botl.erase()
		self.botr.erase()

		self.topa.border()
		self.botl.border()
		self.botr.border()

		self.topa.render()
		self.botl.render()
		self.botr.render()

		with suppress(curses.error):
			self.topa.refresh(0, 0, 0, 0, self.ht, self.w - 1)
			self.botl.refresh(0, 0, self.ht, 0, self.h - 1, self.wl - 1)
			self.botr.refresh(0, 0, self.ht, self.wl, self.h - 1, self.w - 1)
