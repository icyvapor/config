import sys
from maya import cmds

from avalon import api
from avalon.vendor.Qt import QtCore

self = sys.modules[__name__]
self._menu = api.Session["AVALON_LABEL"] + "menu"


