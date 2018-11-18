"""  Class and  """
import logging
import sys
import functools
import itertools
import os
import pickle

from tfont.objects import Layer
# import trufont.util.deco4class as deco4class

from typing import Optional, Any, Union, Tuple, Callable, Dict
import functools
import inspect

#import dataclasses
# constants

from numbers import Number
from collections import Set, Mapping, deque

def prepare_layer_decorate_undoredo(func_get_layer: Callable, name: str, \
    operation="None", paths=True, anchors=True, components=True, guidelines=True):
    """ work with the methods of layer as below 
    layer.beginUndoGroup -> make a first sanpshot via layer.snaphot before a call to a decorated function 
    this snapshot is stored in a dict in layer object associated with key=name
    """ 
    def decorate_fn(fn):
        """ func decorate"""
        # logging.debug("DECORATE_UNDOREDO: on func: {}".format(fn.__name__))

        @functools.wraps(fn)
        def decorate_args(*args, **kwargs):
            """ """
            ret = None 
            try:
                logging.debug("PREPARE_LAYER_DECORATE_UNDOREDO: decorated on {}{}".format(fn.__name__, inspect.signature(fn)))

                # get layer obj 
                logging.debug("PREPARE_LAYER_DECORATE_UNDOREDO:  name is {}".format(name)) 
                params = func_get_layer(*args, **kwargs)
                logging.debug("PREPARE_LAYER_DECORATE_UNDOREDO: ->{}".format(params)) 
                if isinstance(params, Tuple):
                    layer = params[0]
                    op = params[-1]
                else:
                    layer = params
                    op = operation
                undoredo = layer._parent.get_undoredo()

                logging.debug("PREPARE_LAYER_DECORATE_UNDOREDO: decorated on {}".format(op))

                logging.debug("PREPARE_LAYER_DECORATE_UNDOREDO: copy before func on name {}".format(name))
                layer.beginUndoGroup(name, paths, anchors, components, guidelines)

                # call func
                logging.debug("PREPARE_LAYER_DECORATE_UNDOREDO: call func")
                ret = fn(*args, **kwargs)

            except Exception as e:
                logging.error("PREPARE_LAYER_DECORATE_UNDOREDO exception {}".format(str(e)))
                if ret is None:
                    ret = fn(*args, **kwargs)
            finally:
                return ret

        return decorate_args

    return decorate_fn

def perform_layer_decorate_undoredo(func_get_layer: Callable, name: str, \
    operation="None", paths=True, anchors=True, components=True, guidelines=True):
    """ work with the methods of layer as below 
    layer.endUndoGroup -> make a new snapshot after the call to a decorated function
                        -> retrieve the original snapshot in the dict of layer with the key=name
                        -> and get two lambda functions (from endGroupUndo) used as undo and redo function (call on undo/redo)  
    """ 
    def decorate_fn(fn):
        """ func decorate"""
        # logging.debug("DECORATE_UNDOREDO: on func: {}".format(fn.__name__))

        @functools.wraps(fn)
        def decorate_args(*args, **kwargs):
            """ """
            ret = None 
            try:
                logging.debug("PERFORM_LAYER_DECORATE_UNDOREDO: decorated on {}{}".format(fn.__name__, inspect.signature(fn)))

                # get layer obj 
                logging.debug("PERFORM_LAYER_DECORATE_UNDOREDO: name is {}".format(name)) 
                pPERFORM = func_get_layer(*args, **kwargs)
                logging.debug("PERFORM_LAYER_DECORATE_UNDOREDO: {}->{}".format(params)) 
                if isinstance(params, Tuple):
                    layer = params[0]
                    op = params[-1]
                else:
                    layer = params
                    op = operation

                undoredo = layer._parent.get_undoredo()
                # call PERFORM                
                logging.debug("PERFORM_LAYER_DECORATE_UNDOREDO: call func")
                ret = fn(*args, **kwargs)

                #save datas after function call
                logging.debug("LAYER_DECORATE_UNDOREDO: copy after func on name {}".format(name)) 
                undo, redo = layer.endUndoGroup(name_group=name)

                # append action to undoredomgr
                logging.debug("LAYER_DECORATE_UNDOREDO: create and append action on {}".format(op)) 
                undoredo.append_action(Action(op, undo, redo))

            except Exception as e:
                logging.error("START_LAYER_DECORATE_UNDOREDO exception {}".format(str(e)))
                if ret is None:
                    ret = fn(*args, **kwargs)
            finally:
                return ret

        return decorate_args

    return decorate_fn

NONAME='noname'

def layer_decorate_undoredo(func_get_layer: Callable,\
	operation="None", paths=True, anchors=True, components=True, guidelines=True):
    """ work with the methods of layer as below 
    layer.snapshot      -> make a copy of the layer (partial or not)
    layer.setToSnapshot -> restore the copy of layer (partial or not)
    layer.beginUndoGroup -> make a first sanpshot via layer.snaphot before a call to a decorated function 
    layer.endUndoGroup -> make a new snapshot after the call to a decorated function
                        -> and create two lambda functions used as undo and redo functions (call on undo/redo)  
    """ 
    def decorate_fn(fn):
        """ func decorate"""
        # logging.debug("DECORATE_UNDOREDO: on func: {}".format(fn.__name__))

        @functools.wraps(fn)
        def decorate_args(*args, **kwargs):
            """ """
            ret = None 
            try:
                logging.debug("LAYER_DECORATE_UNDOREDO: decorated on {}{}".format(fn.__name__, inspect.signature(fn)))

                # get layer obj 
                logging.debug("LAYER_DECORATE_UNDOREDO: get params") 
                params = func_get_layer(*args, **kwargs)
                logging.debug("LAYER_DECORATE_UNDOREDO: ->{}".format(params)) 
                if isinstance(params, Tuple):
                    layer = params[0]
                    op = params[-1]
                else:
                    layer = params
                    op = operation
                undoredo = layer._parent.get_undoredo()

                logging.debug("LAYER_DECORATE_UNDOREDO: decorated on {}".format(op))

                logging.debug("LAYER_DECORATE_UNDOREDO: copy before func") 
                layer.beginUndoGroup(NONAME, paths, anchors, components, guidelines)

                # call func
                logging.debug("LAYER_DECORATE_UNDOREDO: call func")
                ret = fn(*args, **kwargs)

                #save datas after function call
                logging.debug("LAYER_DECORATE_UNDOREDO: copy after func") 
                undo_redo_and_the_rest = layer.endUndoGroup(NONAME)

                # append action to undoredomgr
                logging.debug("LAYER_DECORATE_UNDOREDO: create and append action on {}".format(op)) 
                undoredo.append_action(Action(op, *undo_redo_and_the_rest))

            except Exception as e:
                logging.error("LAYER_DECORATE_UNDOREDO exception {}".format(str(e)))
                if ret is None:
                    ret = fn(*args, **kwargs)
            finally:
                return ret

        return decorate_args

    return decorate_fn


class Action(object):
    def __init__(self, operation: str="", callback_undo: Callable=None, callback_redo: Callable=None, *args):
        self.operation = operation
        self.callback_undo = callback_undo
        self.callback_redo = callback_redo
        self.args = args


ZERO_DEPTH_BASES = (str, bytes, Number, range, bytearray)
ITERITEMS = 'items'

def _getsize(obj_0):
    """Recursively iterate to sum size of object & members."""
    _seen_ids = set()
    def inner(obj):
        obj_id = id(obj)
        if obj_id in _seen_ids:
            return 0
        _seen_ids.add(obj_id)
        size = sys.getsizeof(obj)
        if isinstance(obj, ZERO_DEPTH_BASES):
            pass # bypass remaining control flow and return
        elif isinstance(obj, (tuple, list, Set, deque)):
            size += sum(inner(i) for i in obj)
        elif isinstance(obj, Mapping) or hasattr(obj, ITERITEMS):
            size += sum(inner(k) + inner(v) for k, v in getattr(obj, ITERITEMS)())
        # Check for custom object instances - may subclass above too
        if hasattr(obj, '__dict__'):
            size += inner(vars(obj))
        if hasattr(obj, '__slots__'): # can have __slots__ with __dict__
            size += sum(inner(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s))
        return size
    return inner(obj_0)


# @deco4class.decorator_classfunc('len_undo', 'len_redo', 'show_undo', 'show_redo')
class UndoRedoMgr(object):
    """ Manage memory and event abour undo/redo/append
    actions """

    __slots__ = ("_logger", "_name", "_undo", "_redo", "_size",
                "callback_on_activated", 
				"callback_after_undo", "callback_after_redo",
                "callback_after_append")

    def __init__(self, name: str, logger: logging.Logger=None):
        """ init for mgr: logger for messages
        actions store in base system: stack """

        self._logger = logger
        self._name = name
        self._undo = []
        self._redo = []
        self._size = 0
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
        return  "{}-size: {:.02f} Kb - UNDO[{}] - REDO[{}]".format(self._name, self._size/1024, 
                                                                   self.len_undo(), 
                                                                   self.len_redo())
    def append_action(self, action: Action):
        """ append action to the undo stack """
        self._undo.append(action)
        if self._redo:
            self._redo = []
        self._size = _getsize(self)
        self._after_append_action()
        self.save()

    def undo(self) -> Action:
        """ play undo, if undo stack is empty raises an exception (indexError)"""
        last_action = self._undo.pop()
        self._redo.append(last_action)
        self._after_undo()
        return last_action

    # def prepare_undo(self, name: str) -> bool:
    #     """ set a marker string to play later a group of undo """
    #     pass

    # def perform_undo(self, to_name):
    #     """ run undo from group of undo"""
    #     pass    	

    def redo(self) -> Action:
        """ play redo, if redo stack is empty raises an exception (indexError)"""
        last_action  = self._redo.pop()
        self._undo.append(last_action)
        self._after_append_action()
        self._after_redo()
        return last_action

    def can_undo(self) -> bool:
        return self.len_undo() > 0

    def len_undo(self) -> int:
        """ show len of stack undo """
        return len(self._undo)
			
    def undo_next(self) -> str:
        return self._undo[-1].operation 			

    def can_redo(self) -> bool:
        return self.len_redo() > 0

    def len_redo(self) -> int:
        """ show len of redo stack """
        return len(self._redo)

    def redo_next(self) -> str:
        return self._redo[-1].operation 
		

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
	
    def save(self):
        """ save to play again later """
        all_actions = [(x.operation, inspect.signature(x.callback_undo), inspect.signature(x.callback_redo)) \
                        for x in itertools.chain(self._undo, self._redo)]
        self._save_as_pickle(all_actions, os.getcwd(), "undoredo-{}".format(self._name))

    def _save_as_pickle(self, tag:Any, path:str, name_pickle: str=None):
        """
        """
        if name_pickle is None:
            name_pickle = type(tag).__name__ +'.pickle'
        name = os.path.join(path, name_pickle)
        try:
            with open(name, 'wb') as fp:
                pickle.dump(tag, fp)
        except Exception as e:
            logging.error("UNDOREDO: pickle write error -> {}".format(str(e)))       
        return name 
    

    def load(self):
        """ load to play now """
        pass

    def read_from_pickle(self, tag: Any, path: str, name_pickle: str):
        """
        """
        name = os.path.join(path, name_pickle)
        if os.path.isfile(name):
            try:
                with open(name, 'rb') as fp:
                    tag = pickle.load(fp)
            except Exception as e:
                logging.error("UNDOREDO: pickle read error -> {}".format(str(e)))       
        return tag 

