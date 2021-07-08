import os
import sys
from maya import cmds

from avalon import api as avalon
from avalon.vendor.Qt import QtCore
from pyblish import api as pyblish

from anvil.utils.maya import events, interactive, tools

PARENT_DIR = os.path.dirname(__file__)
PACKAGE_DIR = os.path.dirname(PARENT_DIR)
PLUGINS_DIR = os.path.join(PACKAGE_DIR, "plugins")

PUBLISH_PATH = os.path.join(PLUGINS_DIR, "maya", "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "maya", "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "maya", "create")

self = sys.modules[__name__]
self._menu = avalon.Session["AVALON_LABEL"] + "menu"

def install():
    pyblish.register_plugin_path(PUBLISH_PATH)
    avalon.register_plugin_path(avalon.Loader, LOAD_PATH)
    avalon.register_plugin_path(avalon.Creator, CREATE_PATH)

    _menu_install()

    avalon.on("init", events.on_init)
    avalon.on("new", events.on_new)
    avalon.on("save", events.on_save)
    avalon.before("save", events.before_save)


def uninstall():
    pyblish.deregister_plugin_path(PUBLISH_PATH)
    avalon.deregister_plugin_path(avalon.Loader, LOAD_PATH)
    avalon.deregister_plugin_path(avalon.Creator, CREATE_PATH)

    _menu_uninstall()


def _menu_install():
    def deferred():
        # Append to Avalon's menu
        cmds.menuItem(divider=True)

        # Modeling sub-menu
        cmds.menuItem("Modeling",
                      label="Modeling",
                      tearOff=True,
                      subMenu=True,
                      parent=self._menu)

        cmds.menuItem("Combine", command=interactive.combine)

        # Rigging sub-menu
        cmds.menuItem("Rigging",
                      label="Rigging",
                      tearOff=True,
                      subMenu=True,
                      parent=self._menu)

        cmds.menuItem("Auto Connect", command=interactive.auto_connect)
        cmds.menuItem("Clone (Local)", command=interactive.clone_localspace)
        cmds.menuItem("Clone (World)", command=interactive.clone_worldspace)
        cmds.menuItem("Clone (Special)", command=interactive.clone_special)
        cmds.menuItem("Create Follicle", command=interactive.follicle)

        # Animation sub-menu
        cmds.menuItem("Animation",
                      label="Animation",
                      tearOff=True,
                      subMenu=True,
                      parent=self._menu)

        cmds.menuItem("Set Defaults", command=interactive.set_defaults)

        # Rendering sub-menu
        cmds.menuItem("Rendering",
                      label="Rendering",
                      tearOff=True,
                      subMenu=True,
                      parent=self._menu)

        cmds.menuItem("Edit Render Globals",
                      command=tools.render_globals_editor)

        cmds.setParent("..", menu=True)

        cmds.menuItem(divider=True)

        cmds.menuItem("Auto Connect", command=interactive.auto_connect_assets)

    # Allow time for uninstallation to finish.
    QtCore.QTimer.singleShot(200, deferred)


def _menu_uninstall():
    pass
