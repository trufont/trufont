# file:  class_decorator.py
import functools
import logging
import types

# from typing import Callable

# constants
CALLABLES = (types.FunctionType, types.BuiltinFunctionType, types.MethodType,\
             types.BuiltinMethodType)
LOGGER = "logger"

# def append_action(operation: str, name_obj_to_save: str):

#     def decorate(fn):
    
#         def params(*args, **kwargs)
#             logging.debug("{} {} ({})".format(fn.__name__, operation, (",").join(str(arg for arg in args))))
#             return fn(*args, **kwargs) 

#         return params  

#     return decorate


tab = 0
def decorator_classfunc(*excluded_method_names, **kwargs):
    """ Decorator used by class """
    if LOGGER in kwargs:
        logger = kwargs[LOGGER]
    else:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
    # logger.debug("DECO4CLASS init......")

    def method_decorator(fn, class_name):
        """ Example of a method decorator """

        @functools.wraps(fn)       
        def decorator(*args, **kwargs):
            global tab
            try:
                tab += 1
                logger.debug("{}Inside {}.{}(nb args:{})".format('\t'*tab, class_name, fn.__name__, len(args)))
                return fn(*args, **kwargs)
            finally:
                logger.debug("{}Outside {}.{}".format('\t'*tab, class_name, fn.__name__))
                tab -= 1
		
        return decorator
    
    
    def class_rebuilder(cls):
        """ The class decorator function useful to redefined a new child
        class from cls  """
        
#        @functools.wraps(cls)       
        class NewClass(cls):
            """ This is the overwritten class """
            _origin = cls.__name__
            __name__ = cls.__name__
            
            def __getattribute__(self, attr_name):
                obj = super().__getattribute__(attr_name)
                if isinstance(obj, CALLABLES) and attr_name not in excluded_method_names:
#                    return method_decorator(obj, cls.__name__)
                    return method_decorator(obj, NewClass._origin)
                return obj

        return NewClass
    
    return class_rebuilder

