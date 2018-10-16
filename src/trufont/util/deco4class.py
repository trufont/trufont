# file:  class_decorator.py

import logging
import types

# from typing import Callable

# constants
STR_FMT = '%(asctime)s - %(levelname)s : %(message)s'
DATE_FMT = '%d/%m/%Y %H:%M:%S'

#logging.basicConfig(level=logging.INFO, format=STR_FMT, datefmt=DATE_FMT)
logger = logging.getLogger()

CALLABLES = (types.FunctionType, types.BuiltinFunctionType, types.MethodType,\
             types.BuiltinMethodType)
LOGGER = "logger"

tab = 0
def decorator_classfunc(*excluded_method_names, **kwargs):
    """ Decorator used by class """
    if LOGGER in kwargs:
        logger = kwargs[LOGGER]
    else:
        logger = logging.getLogger()
    # logger = logging.getLogger()
    
    def method_decorator(fn, class_name):
        """ Example of a method decorator """
       
        def decorator(*args, **kwargs):
            global tab
            try:
                tab += 1
                logger.debug("{}Inside {}.{}({})".format('\t'*tab, class_name, fn.__name__, args))
                return fn(*args, **kwargs)
            finally:
                logger.debug("{}Outside {}.{}".format('\t'*tab, class_name, fn.__name__))
                tab -= 1
		
        return decorator
    
    
    def class_rebuilder(cls):
        """ The class decorator function useful to redefined a new child
        class from cls  """
        
        class NewClass(cls):
            """ This is the overwritten class """
            _origin = cls.__name__
            
            def __getattribute__(self, attr_name):
                obj = super().__getattribute__(attr_name)
                if isinstance(obj, CALLABLES) and attr_name not in excluded_method_names:
                    return method_decorator(obj, cls.__name__)
                return obj

        return NewClass
    
    return class_rebuilder

