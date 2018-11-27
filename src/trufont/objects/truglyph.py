""" Class TruGlyph only to see waht's happen with Glyph data are modified """
from tfont.objects import Glyph, Layer
import trufont.objects.undoredomgr as undoredomgr
from typing import Any, Tuple, List
import functools
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
    
    def get_undoredo(self):
        if not self._undoredo:
            self._undoredo = undoredomgr.UndoRedoMgr(self.name, self._logger)
        if self._frame and self._undoredo.callback_after_append is None:
            self._undoredo.set_callback_after_append(self._frame.OnUpdateUndoRedoMenu, self._undoredo)
        return self._undoredo

    def load_from_undoredo(self, layer: Layer):
        logging.debug("TRUGLYPH: ---------------- enter load debug is {} and layer {}".format(self._debug, layer))
        if self._debug:
            if True:
                all_actions = self.get_undoredo().load()
               	logging.debug("TRUGLYPH: load from pickle file from undo -> {} items".format(len(all_actions)))
                dredo = None
                for op, (dundo, dredo) in all_actions: 
                    # logging.debug("TRUGLYPH: load from pickle file on {}".format(op))
                   	logging.debug("TRUGLYPH: load from pickle file dundo->{}".format(id(dundo)))
                   	logging.debug("TRUGLYPH: load from pickle file dredo->{}".format(id(dredo)))
                   	logging.debug("TRUGLYPH: +++++++++++++++++++++++++++++++++++++++++++++++ ")
                   	# lambda: layer.setToSnapshot(dundo) -- DOES NOT WORK ?? WHY ???
                   	f_undo = functools.partial(layer.setToSnapshot, dundo) 
                   	f_redo = functools.partial(layer.setToSnapshot, dredo) 
                   	self.get_undoredo().append_action(undoredomgr.Action(op, f_undo, f_redo, (dundo, dredo)))

               	if dredo:
                   	logging.debug("TRUGLYPH: load from pickles layer init-> {}".format(self.get_undoredo().all_actions_undo()[0]))
                   	logging.debug("TRUGLYPH: load from pickles layer last-> {}".format(self.get_undoredo().all_actions_undo()[-1]))
                   	layer.setToSnapshot(dredo)
       	logging.debug("TRUGLYPH: ---------------- exit load")


    def save_from_undoredo(self):
        if self._debug:
            all_actions = [(action.operation, *action.args) for action in self.get_undoredo().all_actions_undo()]
            self.get_undoredo().save(all_actions)
