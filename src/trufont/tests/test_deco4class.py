# file:  class_decorator.py

import sys
import logging

import trufont.util.deco4class as deco4class
import trufont.util.loggingstuff as logstuff

logger = logstuff.create_stream_logger(logstuff.LOGGER_CLASSFUNCS)
logger.setLevel(logging.DEBUG)


@deco4class.decorator_classfunc()
class MySecondClass(object):
    """
    This class is decorated
    """
    def __init__(self, keepit):
        logger.debug("\t\tthis is a the MySecondClass.__init__")
    
    def __repr__(self):
        if hasattr(self,'_origin'):
            return "<{}-{}>".format(self._origin, id(self))
        return "<{}-{}>".format(self.__class__.__name__, id(self))
    
    
    def first_method(self, *args, **kwargs):
        logger.debug("\t\tthis is a the MySecondClass.first_method")


    def second_method(self, *args, **kwargs):
        logger.debug("\t\tthis is the MySecondClass.second_method")


@deco4class.decorator_classfunc('second_m')
class MyThirdClass(object):
    """
    This class is decorated
    """    
    def __init__(self):
        """ init just instanciate Inner """
        self.i = Inner()
    
    
    def first_m(self, *args, **kwargs):
        self.i.method_inner()
        logger.debug("\t\tthis is a the MyThirdClass.first_m")


    def second_m(self, *args, **kwargs):
        logger.debug("\t\tthis is the MyThirdClass.second_m")


@deco4class.decorator_classfunc()
class Inner(object):
    """ inner class to see the \t sequence """
    
    def method_inner(self, val: int=10, isbig: bool=True):
        pass


def test_decoclass(logger: logging.Logger=logstuff.create_stream_logger(logstuff.LOGGER_CLASSFUNCS)):
    """ tests the deco on 3 class """
    logger.info(sys.version)
    logger.info(":Test a decorated for class")
    
    # second class
    z = MySecondClass(True)
    logger.info("Z is {}".format(z))
    z.first_method()
    z.second_method()

    # third class
    x = MyThirdClass()
    x.first_m()
    # here no output 
    x.second_m()


if __name__ == "__main__":
    """ main fomr python launcher .... """    
    test_decoclass(logger)