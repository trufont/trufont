"""  Class and  """
import logging
import functools

import trufont.util.deco4class as deco4class
import trufont.util.loggingstuff as logstuff

from typing import Optional, Any, Union, Tuple, Callable
import dataclasses
# constants

#@deco4class.decorator_classfunc('len_undo', 'len_redo', 'show_undo', 'show_redo')


class Action(object):
    def __init__(self, operation: str="", callback_undo: Callable=None, callback_redo: Callable=None):
        self.operation = operation
        self.callback_undo = callback_undo
        self.callback_redo = callback_redo


class UndoRedoMgr(object):
    """ Manage memory and event abour undo/redo/append 
    actions """

    __slots__ = ("_logger", "_name", "_undo", "_redo", "_group",  
                "callback_on_activated", "callback_after_undo", "callback_after_redo", 
                "callback_after_append")

    def __init__(self, name: str, logger: logging.Logger=logstuff.create_stream_logger(logstuff.LOGGER_UNDOREDO)):
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
	
