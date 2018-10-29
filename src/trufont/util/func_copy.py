from tfont.objects import Path, Point, Layer

from typing import List
import copy

def copypathsfromlayer(layer: Layer) -> List[Path]:
    """ manual deep copy of paths of layer """
    lpaths = []
    for path in layer._paths:
        new_path = Path()
        # copy bounds
        new_path._bounds = copy.copy(path._bounds)

        # copy points
        new_path._points = [copy.copy(pt) for pt in path._points]

        # parents etc ...
        new_path._parent = path._parent 
        new_path._id = path._id
        new_path._graphicsPath = path._graphicsPath

        # keep it
        lpaths.append(new_path)

    return lpaths


def undoredo_fromcopy(layer: Layer, old_paths: Path, old_operation:str):
    """ restore data paths from an undo or redo actions """
#    logging.debug("ALIGN: undoredo_align_fromcopy.....")

    #set old values
    layer.paths[:] = old_paths
    layer.paths.applyChange()
