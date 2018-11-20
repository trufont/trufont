""" Class TruGlyph only to see waht's happen with Glyph data are modified """
from tfont.objects import Glyph
import trufont.objects.undoredomgr as undoredomgr
from typing import Any, Tuple, List

import logging

class TruGlyph(Glyph):
	__slots__ = ("_logger", "_undoredo", "_frame", "_debug" )
	""" class from tfontGlyph to intercep """
	def __init__(self, name: str, unicodes: List, logger: logging.Logger=logging.getLogger(), 
				*args: Tuple):
		""" init """
		super().__init__(name, unicodes, *args)
		self._logger = logger
		self._undoredo = None
		self._frame = None
		self._debug = False

	@property
	def logger(self):
		return self._logger

	@property
	def frame(self):
		return self._frame
	
	@frame.setter
	def frame(self, frame):
		self._frame = frame

	@property
	def debug(self):
		return self._debug

	@debug.setter
	def debug(self, debug: bool):
		self._debug = debug
		self.get_undoredo().debug = debug

	def get_undoredo(self):
		if not self._undoredo:
			self._undoredo = undoredomgr.UndoRedoMgr(self.name, self._logger)
		if self._frame and self._undoredo.callback_after_append is None:
			self._undoredo.set_callback_after_append(self._frame.OnUpdateUndoRedoMenu, self._undoredo)
		return self._undoredo
