"""  Class and  """
import logging
import functools

import trufont.util.deco4class as deco4class
import trufont.util.loggingstuff as logstuff

from typing import Optional, Any, Union, Tuple, Callable, Dict
import functools
import inspect

#import dataclasses
# constants

def sample_copypathsfromlayer(layer: "Layer"):
    pass

def sample_undoredo_align_fromcopy(layer: "Layer", old_paths: "Path", old_operation:str):
    pass

<<<<<<< HEAD
params_undoredo = { 
                  'default':{'copy': (sample_copypathsfromlayer, 'layer'),
                                'undo': (sample_undoredo_align_fromcopy, 'layer', 'old_datas', 'operation'), 
=======
params_undoredo = {
                  '_alignDefault':{'copy': (sample_copypathsfromlayer, 'layer'),
                                'undo': (sample_undoredo_align_fromcopy, 'layer', 'old_datas', 'operation'),
>>>>>>> fe195648ca3c81d4d6882cd70c865bbd277a93cb
                                'redo': (sample_undoredo_align_fromcopy, 'layer', 'new_datas', 'operation')
                                },
                  'transform':{'copy': (sample_copypathsfromlayer, 'layer'),
                                 'undo': (sample_undoredo_align_fromcopy, 'layer', 'old_datas', 'operation'),
                                 'redo': (sample_undoredo_align_fromcopy, 'layer', 'new_datas', 'operation')
                                 }
                 }

DEFAULT_KEY="default"
def decorate_undoredo(params_deco: Dict, func_expand_params: Callable):
    """  decorate functions that modify a glyph:
    1. make a save of a glyph (or a part) before the function call
    2. call the function
    3. make a save of glyph (or a part) after the function call
    4. append an action - the modification -- to the undoredo manager of the glyph
    params_deco is a dict where:
        key is the function name
        values is a dict with 3 entries as tuple where first item is:
            copy function to make the save
            undo function calling when undo
            redo function calling when redo
        NOTE: The end of the tuple (as 'layer','old_datas', etc ...) is not useful for the moment

    func_expand_params is a function that decompose from *args and **kwargs of the decorated function
    to expand to the param need by the copy, undo and redo functions -
    Actually func_expand_params returns 3 values: Layer, UndoRedoMgr and an a sring (name of current operation)

    WARNING: It is the same format for all decorated function, at this time -  HAVE TO CHANGE SOON
    Note here that the Action class, the callback function give to undoredo mgr are partial function.
    So on undo or redo, you have just to call these 2 partials
    """

    def decorate_fn(fn):
        """ func decorate"""
        # logging.debug("DECORATE_UNDOREDO: on func: {}".format(fn.__name__))

        @functools.wraps(fn)
        def decorate_args(*args, **kwargs):
            """ """
            # if logger:
            #     del logger
            #     logger = None
            ret = None
            try:
                sig = inspect.signature(fn)
                logging.debug("DECORATE_UNDOREDO: signature{}".format(sig))

                #functions from dict
                key = None
                if fn.__name__ in params_deco:
                    key = fn.__name__
                elif DEFAULT_KEY in params_deco:
                    key = DEFAULT_KEY

                logging.debug("DECORATE_UNDOREDO: key is {}".format(key))

                if key:
                    params = params_deco[key]
                    func_copy = params['copy'][0]
                    func_undo = params['undo'][0]
                    func_redo = params['redo'][0]

                    logging.debug("DECORATE_UNDOREDO: func copy:{}".format(func_copy.__name__))
                    logging.debug("DECORATE_UNDOREDO: func undo:{}".format(func_undo.__name__))
                    logging.debug("DECORATE_UNDOREDO: func redo:{}".format(func_redo.__name__))
                    logging.debug("DECORATE_UNDOREDO: func expand:{}".format(func_expand_params.__name__))

                    # expand params as layer, undoredomgr and operation
<<<<<<< HEAD
                    logging.debug("DECORATE_UNDOREDO: expand params") 
                    obj, undoredo, operation = func_expand_params(*args)
                    logging.debug("DECORATE_UNDOREDO: operation is {} ob {}".format(operation, obj.__class__.__name__)) 

                    #save datas before function call
                    logging.debug("DECORATE_UNDOREDO: copy before func") 
                    old_obj = func_copy(obj)
=======
                    logging.debug("DECORATE_UNDOREDO: expand params")
                    layer, undoredo, operation = func_expand_params(*args)
                    logging.debug("DECORATE_UNDOREDO: operation is {}".format(operation))

                    #save datas before function call
                    logging.debug("DECORATE_UNDOREDO: copy before func")
                    old_datas = func_copy(layer)
>>>>>>> fe195648ca3c81d4d6882cd70c865bbd277a93cb

                    # call func
                    logging.debug("DECORATE_UNDOREDO: call func")
                    ret = fn(*args, **kwargs)

                    #save datas after function call
<<<<<<< HEAD
                    logging.debug("DECORATE_UNDOREDO: copy after func") 
                    new_obj = func_copy(obj)

                    # append action to undoredomgr
                    logging.debug("DECORATE_UNDOREDO: create action") 
                    action = Action(operation, 
                                    functools.partial(func_undo, obj, old_obj, operation), 
                                    functools.partial(func_redo, obj, new_obj, operation))
                    logging.debug("DECORATE_UNDOREDO: append action") 
=======
                    logging.debug("DECORATE_UNDOREDO: copy after func")
                    new_datas = func_copy(layer)

                    # append action to undoredomgr
                    logging.debug("DECORATE_UNDOREDO: create action")
                    action = Action(operation,
                                    functools.partial(func_undo, layer, old_datas, operation),
                                    functools.partial(func_redo, layer, new_datas, operation))
                    logging.debug("DECORATE_UNDOREDO: append action")
>>>>>>> fe195648ca3c81d4d6882cd70c865bbd277a93cb
                    undoredo.append_action(action)

                else:
                    # decorated but params not found !!!
                    ret = fn(*args, **kwargs)

            except Exception as e:
                logging.error("DECORATE_UNDOREDO exception {}".format(str(e)))

            finally:
                return ret

        return decorate_args

    return decorate_fn



class Action(object):
    def __init__(self, operation: str="", callback_undo: Callable=None, callback_redo: Callable=None):
        self.operation = operation
        self.callback_undo = callback_undo
        self.callback_redo = callback_redo


# @deco4class.decorator_classfunc('len_undo', 'len_redo', 'show_undo', 'show_redo')
class UndoRedoMgr(object):
    """ Manage memory and event abour undo/redo/append
    actions """

    __slots__ = ("_logger", "_name", "_undo", "_redo", "_group",
                "callback_on_activated", "callback_after_undo", "callback_after_redo",
                "callback_after_append")

    def __init__(self, name: str, logger: logging.Logger=None):
        """ init for mgr: logger for messages
        actions store in base system: stack """

        self._logger = logger
        self._name = name
        self._undo = []
        self._redo = []
        self._group = None
        self.callback_on_activated = None
        self.callback_after_undo = None
        self.callback_after_redo = None
        self.callback_after_append = None
		
		
    def set_callback_on_activated(self, callback, *args, **kwargs):
        if isinstance(callback, Callable):
           self.callback_on_activated = functools.partial(callback, *args, *kwargs)


    def set_callback_after_undo(self, callback, *args, **kwargs):
        if isinstance(callback, Callable):
           self.callback_after_undo = functools.partial(callback, *args, *kwargs)

		
    def set_callback_after_redo(self, callback, *args, **kwargs):
        if isinstance(callback, Callable):
	        self.callback_after_redo = functools.partial(callback, *args, *kwargs)


    def set_callback_after_append(self, callback, *args, **kwargs):
        if isinstance(callback, Callable):
        	self.callback_after_append = functools.partial(callback, *args, *kwargs)

    def str_state(self) -> str:
        """ show state of mgr """
        return  "{} - undo[{}]/redo[{}]".format(self._name, self.len_undo(), self.len_redo())

    def append_action(self, action: Action):
        """ append action to the undo stack """
        self._undo.append(action)
        if self._redo:
            self._redo = []
        self._after_append_action()

    def undo(self) -> Action:
        """ play undo, if undo stack is empty raises an exception (indexError)"""
        last_action = self._undo.pop()
        self._redo.append(last_action)
        self._after_undo()
        return last_action

    def prepare_undo(self, name: str) -> bool:
        """ set a marker string to play later a group of undo """
        pass

    def perform_undo(self, to_name):
        """ run undo from group of undo"""
        pass    	

    def redo(self) -> Action:
        """ play redo, if redo stack is empty raises an exception (indexError)"""
        last_action  = self._redo.pop()
        self._undo.append(last_action)
        self._after_append_action()
        self._after_redo()
        return last_action

    def can_undo(self) -> bool:
        return self._undo

    def len_undo(self) -> int:
        """ show len of stack undo """
        return len(self._undo)
			

    def can_redo(self) -> bool:
        return self._redo


    def len_redo(self) -> int:
        """ show len of redo stack """
        return len(self._redo)
			

    def show_undo(self) -> str:
        """ show undo contents """
        return "{} -> {}".format(self._name, str(self._undo))

		
    def show_redo(self) -> str:
        """ show redo contents """
        return "{} -> {}".format(self._name, str(self._redo))


    def on_activated(self):
        if self.callback_on_activated:
            self.callback_on_activated()
		

    def _after_append_action(self):
        """ play this partial function after append action"""
        if self.callback_after_append:
            self.callback_after_append()

			
    def _after_undo(self):
        """ play this partial function after an undo """    	
        if self.callback_after_undo:
            self.callback_after_undo()


    def _after_redo(self):
        """ play this partial function after a redo"""
        if self.callback_after_redo:
            self.callback_after_redo()
	