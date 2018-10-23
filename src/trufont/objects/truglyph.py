""" Class TruGlyph only to see waht's happen with Glyph data are modified """
from tfont.objects import Glyph
import trufont.objects.undoredomgr as undoredomgr
from typing import Any, Tuple, List
import logging


class TruGlyph(Glyph):
	""" class from tfontGlyph to intercep """
	def __init__(self, name: str, unicodes: List, logger: logging.Logger=logging.getLogger(), 
				*args: Tuple):
		""" init """
		super().__init__(name, unicodes, *args)
		self._logger = logger
		self._undoredo = None


	@property
	def logger(self):
		return self._logger


	def get_undoredo(self):
		if not self._undoredo:
			self._undoredo = undoredomgr.UndoRedoMgr(self.name, self._logger)
		return self._undoredo


#	def __setattr__(self, key: str, value: Any):
#		logger.info("TRUGLYPH: modifiy attr '{}'".format(key))
#		super().__setattr__(key, value)
#
# 		if not key.startswith('_') and key != "selected":
# 			old_value = super().lastModified()
# 			old_value = getattr(self, 'lastModified')
# 			super().__setattr__(key, value)
# 			new_value = self.lastModified()
# 			if old_value != new_value:
# 				self.undoredomgr.action_append((key, value))

# 		else:
# 			super().__setattr__(key, value)



