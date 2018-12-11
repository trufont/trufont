""" Class UNDOREDOGLYPH only to see waht's happen with Glyph data are modified """
from tfont.objects import Glyph, Layer
import trufont.objects.undoredomgr as undoredomgr
from typing import Any, Tuple, List
import functools
import trufont
import logging

# DISABLED_UNDERDO = trufont.TruFont._internal["disable_undoredo"]

class UndoRedoGlyph(Glyph):
    __slots__ = ("_logger", "_undoredo", "_frame", "_debug", "_disable_undoredo" )


    """ class from tfontGlyph to intercep """
    def __init__(self, name: str, unicodes: List, logger: logging.Logger=logging.getLogger(), 
                    *args: Tuple):
        """ init """
        super().__init__(name, unicodes, *args)
        self._logger = logger
        self._undoredo = None
        self._frame = None
        self._debug = False
        self._disable_undoredo = False

    def __del__(self):
        if self._debug:
            self.save_from_undoredo()

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
 
    @property
    def disable_undoredo(self):
        return self._disable_undoredo

    @disable_undoredo.setter
    def disable_undoredo(self, disable_undoredo: bool):
        self._disable_undoredo = disable_undoredo

    def get_undoredo(self):
        if not self._undoredo:
            self._undoredo = undoredomgr.UndoRedoMgr(self.name, self._logger)
        if self._frame and self._undoredo.callback_after_append is None:
            self._undoredo.set_callback_after_append(self._frame.OnUpdateUndoRedoMenu, self._undoredo)
        return self._undoredo

    def load_from_undoredo(self, layer: Layer):
        logging.debug("UNDOREDOGLYPH: disable_undoredo -> {}".format(self._disable_undoredo))
        if not self._disable_undoredo and self._debug:
            all_actions = self.get_undoredo().load()
            logging.debug("UNDOREDOGLYPH: load from pickle file from undo -> {} items".format(len(all_actions)))
            dredo = None
            for op, (dundo, dredo) in all_actions: 
                # logging.debug("UNDOREDOGLYPH: load from pickle file on {}".format(op))
                logging.debug("UNDOREDOGLYPH: load from pickle file dundo -> {}".format(id(dundo)))
               	logging.debug("UNDOREDOGLYPH: load from pickle file dredo -> {}".format(id(dredo)))
               	logging.debug("UNDOREDOGLYPH: +++++++++++++++++++++++++++++++++++++++++++++++ ")
               	# lambda: layer.setToSnapshot(dundo) -- DOES NOT WORK ?? WHY ???
               	f_undo = functools.partial(layer.setToSnapshot, dundo) 
               	f_redo = functools.partial(layer.setToSnapshot, dredo) 
               	self.get_undoredo().append_action(undoredomgr.Action(op, f_undo, f_redo, (dundo, dredo)))

            if dredo:
               	logging.debug("UNDOREDOGLYPH: load from pickles layer init-> {}".format(self.get_undoredo().all_actions_undo()[0]))
               	logging.debug("UNDOREDOGLYPH: load from pickles layer last-> {}".format(self.get_undoredo().all_actions_undo()[-1]))
               	layer.setToSnapshot(dredo)
       	logging.debug("UNDOREDOGLYPH: ---------------- exit load")


    def save_from_undoredo(self):
        logging.debug("UNDOREDOGLYPH: disable_undoredo -> {}".format(self._disable_undoredo))
        if not self._disable_undoredo and self._debug:
            # all_actions = [(action.operation, *action.args) for action in self.get_undoredo().all_actions_undo()]
            all_actions = [action.datas_only() for action in self.get_undoredo().all_actions_undo()]
            self.get_undoredo().save(all_actions)
