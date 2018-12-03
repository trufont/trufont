import sys
import os
import trufont
from trufont.objects import factories
from trufont.objects.application import Application
import wx
import click
from typing import Optional
import logging

@click.command(help='font name to pass') 
@click.argument('font_name', required=False, nargs=-1)
@click.option('--cwd', default=os.getcwd(), help='Set the current working directory - cwd is default')
@click.option('--debug', is_flag=True, help='Enable debug mode in log')
@click.option('--log_screen', is_flag=True, help='Enable log to screen')
@click.option('--log_rotating', is_flag=True, help='Enable log in file')
@click.option('--disable_undoredo', is_flag=True, help='Disable undo/redo system')
def main(font_name: Optional[str], cwd: str, debug: bool, log_screen: bool, log_rotating: bool, disable_undoredo: bool):
    """ """
    app = wx.App()
    app.SetAppDisplayName("TruFont")
    app.fileHistory = wx.FileHistory()
    factories.registerAllFactories()
    # could just create the object in __init__ and set app
    # here, this would avoid the trufont.TruFont.xxx all over the place

    # check sys.argv
    # _rotate = False
    # _debug = False
    # _log = False
    # for arg in sys.argv[1:]:
    #     if "debug" in arg.lower():
    #         _debug = True
    #     elif "loggingrotate" in arg.lower():
    #         _log = True 
    dict_args = { 
                "cwd":cwd, 
                "debug":debug, 
                "log_screen":log_screen, 
                "log_rotating":log_rotating, 
                "disable_undoredo":disable_undoredo
                }
    
    trufont.TruFont = TruFont = Application(app, **dict_args) 
    logging.info("MAIN: {}".format(dict_args))
    TruFont.newFont()
    sys.exit(app.MainLoop())

if __name__ == "__main__":
    main()
