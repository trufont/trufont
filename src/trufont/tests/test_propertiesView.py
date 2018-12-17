# file:  test_loggingWindows.py
import sys
import logging
import os
import copy

import wx
import trufont.util.loggingstuff as logstuff
import random 

from typing import Union, Tuple, Any

LAYER_EXCLUDED_ITEMS = ('__weakref__','_parent', '_closedGraphicsPath', '_openGraphicsPath')
PATH_EXCLUDED_ITEMS =('__weakref__','_parent', '_graphicsPath')
POINT_EXCLUDED_ITEMS =('__weakref__','_parent')


logger = logstuff.create_stream_logger("")

def get_items(obj: Any) -> Tuple[str]:
    """ get items of objects """
    #Does it contain other object 
    if hasattr(obj, '__slots__'):
        return obj.__slots__
    
    if hasattr(obj, '__dict__'): 
        return obj.__dict__

    # implicit but ....
    return None

def deepcopyitems(fromobj: Any, copyobj: Any, *excluded_items) -> Any:
    """ deep copy of all items except excluded items """


    # simple copy of object
    if type(fromobj) != type(copyobj):
        msg = "DEEPCOPYITEMS: Type source {} is not equal to dest source {}".format(type(fromobj), type(copyobj))
        logging.debug(msg)
        raise TypeError(msg)
    
    # get items lists
    items = get_items(fromobj)
    logging.debug("DEEPCOPYITEMS: Items are: {}".format(items))

    if items:
        logging.debug("DEEPCOPYITEMS: excluded items are: {}".format(excluded_items))
        for item in items:
            logging.debug("DEEPCOPYITEMS: Item is : {}".format(item))
            if item in excluded_items:
                logging.debug("DEEPCOPYITEMS: Item excluded : {}".format(item))
                setattr(copyobj, item, getattr(fromobj, item))
            else:
                logging.debug("DEEPCOPYITEMS: Item included : {}".format(item))
                setattr(copyobj, item, copy.deepcopy(getattr(fromobj, item))) #, { id(getattr(fromobj,'_parent')):1 } ))
    else:
        copyobj = copy.deepcopy(fromobj)            
    return copyobj


# def deepcopypathsfromlayer(layer: Layer) -> List[Path]:
#     """ deep copy of paths of layer """
#     lpaths = []
#     for path in layer._paths:  
#         lpaths.append(deepcopyitems(path, path.__class__(), *PATH_EXCLUDED_ITEMS))

#     return lpaths


def mydeepcopy(fromobj: Any, deep_again: int, *excluded_class) -> Any:
    """ deep copy only tfont object """
#    logging.debug("MYDEEPCOPY: Start deep_again from {}".format(deep_again))
    excluded_items = ('__weakref__','_parent', '_closedGraphicsPath', '_openGraphicsPath')

    # simple copy of object
    copyobj = copy.copy(fromobj)

    # get items lists
    items = get_items(copyobj)
        
    if not items:
        # look up data if collection type
        return copy.deepcopy(fromobj)

    # create and copy items of an object 
#    logging.debug("MYDEEPCOPY: items -> {}".format(items))
    for item in items:
        if item not in excluded_items:
            try: 
                value = copy.copy(getattr(fromobj, item))
            except:
                value = getattr(fromobj, item)
                
#            logging.debug("MYDEEPCOPY: Item:'{}' class<{}> -> Value:'{}'".format(item, value.__class__.__name__, value))
            # isinstance(value, excluded_class): 
            # class of object to excluded ?
#            logging.debug("MYDEEPCOPY: {} vs {} is {}".format(value.__class__, excluded_class, issubclass(value.__class__, excluded_class)))

            if deep_again == 1:
#                logging.debug("MYDEEPCOPY: Stop deep_again to {}".format(deep_again-1))
                setattr(copyobj, item, value)
            elif not excluded_class:
                setattr(copyobj, item, mydeepcopy(getattr(fromobj, item), deep_again-1, *excluded_class))
            elif not issubclass(value.__class__, excluded_class) or not isinstance(value, excluded_class):
                setattr(copyobj, item, mydeepcopy(getattr(fromobj, item), deep_again-1, *excluded_class))
            else:
                setattr(copyobj, item, value)
        else:
            logging.debug("DEEPCOPY: item {} excluded !!".format(item))
    return copyobj



class Point(object):
    """ clas point etc .... """
    def __init__(self, parent: Union["Path", Any], x: Union[int, float], y:Union[int, float], *args: Tuple):
        self._parent = parent
        self.x = x
        self.y = y
        self.str = "("+str(x)+","+str(y)+")"
        
    def __repr__(self):
        return "<Point-0x{:08X}>".format(id(self)) + self.str


class Path(object):
    """ List of Point """
    def __init__(self, parent: "Layer", nbp:int):
        self._points = [Point(self, random.randint(-300,300), random.randint(0,800)) for _ in range(nbp)]
        self._parent = parent
                            
    def __repr__(self):
        return "<Path-0x{:08X}>".format(id(self)) + ",".join(str(x) for x in self._points)


class Bound(object):
    id = 1
    def __init__(self, parent: Path, x: int, y: int, cx: int, cy: int):
        self._parent = parent
        self.bd = (x, y, cx, cy)
        self.id = Bound.id
        Bound.id += 1
        
    def __repr__(self):
        return "<Bound-0x{:08X}>".format(id(self)) + "({},{},{},{})".format(*self.bd)
                
        
class Layer(object):
    """ simulate Layer form Trufont """
    def __init__(self, parent: Any, nb_path: int, nb_bounds: int):
        self._parent = parent
        self._paths = [Path(self, i + random.randint(1,4)) for i in range(nb_path)]
        self._bounds = Bound(self, nb_bounds+10, nb_bounds-10, 300, 200)
        self._selected = False
        self._name = str(nb_path*1000+nb_bounds)
    
    def __repr__(self):
        return "<Layer-0x{:08X}>".format(id(self)) + "-".join(str(p) for p in self._paths) + str(self._bounds)
        
def test_mydeepcopy2(log: logging.Logger=logger):
    """ test a deepcopy with a TruGlyph """
    log.info(sys.version)
    layer = Layer(None, 2,1)
    log.info("layer -> {}".format(layer))
    log.info("-"*30)
    lay1 = mydeepcopy(layer, 5)
    log.info("lay1 -> {}".format(lay1))
    
    lay2 = deepcopyitems(layer, Layer(None, 0,0), '_name')
    log.info("lay1 -> {}".format(lay2))


if __name__ == "__main__":
    # constants
    # test_mydeepcopy(logger)
    test_mydeepcopy2(logger)

class MySecondClass(object):
    """
    This class is decorated
    """
    def __init__(self, keepit):
        logger.debug("\t\tthis is a the MySecondClass.__init__")
        self._paths = []
        self.a = 10
        self.b = [1, True, "nnn", { 1:"1", 2:("2", "deux", "II")} , 4.14]
        self.c = MyThirdClass(2, 5, (2.3), "tt")
    
    def __repr__(self):
        if hasattr(self,'_origin'):
            return "<O{}-0x{:X}>".format(self._origin, id(self))
        return "<C{}-0x{:X}>".format(self.__class__.__name__, id(self))
       
    def first_method(self, *args, **kwargs):
        logger.debug("\t\tthis is a the MySecondClass.first_method")


    def second_method(self, *args, **kwargs):
        logger.debug("\t\tthis is the MySecondClass.second_method")


class MyThirdClass(object):
    """
    This class is decorated
    """    
    def __init__(self, *args):
        """ init just instanciate Inner """
        self.i = Inner()
        self.args = args
        self.mi=[]
        self.mi.extend([self.i]*3)
       
    def first_m(self, *args, **kwargs):
        self.i.method_inner()
        logger.debug("\t\tthis is a the MyThirdClass.first_m")


    def second_m(self, *args, **kwargs):
        logger.debug("\t\tthis is the MyThirdClass.second_m")


class Inner(object):
    """ inner class to see the \t sequence """
    def __init__(self, *args):
        self.str = 'toto'
        self.args = args


    def method_inner(self, val: int=10, isbig: bool=True):
        pass

def test_mydeepcopy(log: logging.Logger=logger):
    """ test a deepcopy with a multiple object indise """
    log.info(sys.version)
    obj = MySecondClass(True)
    obj1 = mydeepcopy(obj, 3)
    log.info("Obj:len of {}  -> {}".format(sys.getsizeof(obj), obj.__dict__))
    log.info("obj1:len of {}  -> {}".format(sys.getsizeof(obj1), obj1.__dict__))
    log.info("obj == obj1 -> {}".format(obj == obj1))

    obj2 = mydeepcopy(obj, 3, Inner)
    log.info("obj2:len of {} ->  {}".format(sys.getsizeof(obj2), obj2.__dict__))
    log.info("obj == obj2 -> {}".format(obj == obj2))
    log.info("This is the end")
