#!/usr/bin/env python3

# python
from sys import exit

# panda3d
from panda3d.core import WindowProperties
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *

# game
from core import N
from gui import *

TOOLBOX_WIDTH = 0.3
MENU_HEIGHT = 0.2

MENU_SPACE = 0.3
TOP_MENU_MARGIN = 0.1
LEFT_TOOL_MARGIN = 0.16
TOP_TOOL_MARGIN = 0.1
TOOL_SPACE = 0.1


class Editor(ShowBase):
    "clonium map editor"
    title = "Clonium map editor"

    def __init__(self, return_map=False):
        ShowBase.__init__(self)
        self.disableMouse()
        self.set_properties()
        self.return_map = return_map

        self.menu = DirectFrame(
            frameSize=(MIN_X, MAX_X, MAX_Z, MAX_Z - MENU_HEIGHT),
            frameColor=(1, 1, 1, 1))
        self.toolbox = DirectFrame(
            frameSize=(MIN_X, MIN_X + TOOLBOX_WIDTH,
                MIN_Z, MAX_Z - MENU_HEIGHT),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            frameColor=(0.8, 0.8, 1, 1))
        self.canvas = ...

        # menu:
        self.new_menu("File", 0, (
            ("New map", None),
            ("Open map", None),
            ("Save", None),
            ("Save as", None),
            ("Save and quit", None),
            ("Quit", None)), setter=self.accept, shortcuts=(
            'control-n', 'control-o', 'control-s', 'shift-control-s',
            'control-w', 'control-q')
        )
        self.new_menu("Edit", 1, (
            ("Extend", None),
            ("Reduce", None))
        )
        # TODO: add/remove top/bottom/leftmost/rightmost row/column -> GUI
        self.new_menu("Add", 2, (
            ("Add cells", None),)
        )
        self.new_menu("Remove", 3, (
            ("Remove all checkers", None),
            ("Remove the checkers", None),
            ("Remove the player's checkers", None),
            ("Remove the chackers of the level", None))
        )

        # tools:
        # 3 tools
        # TODO: text -> image
        z = MAX_Z - MENU_HEIGHT - TOP_TOOL_MARGIN
        tool_states = ['draw', 'erase', 'spawn']
        self.tool = ['draw']
        tools = [DirectRadioButton(
            parent=self.toolbox,
            text=tool, variable=self.tool, value=[tool],
            scale=SCALE,
            pos=(MIN_X + LEFT_TOOL_MARGIN, 0,
                z - n * TOOL_SPACE),
            command=self.set_tool) for n, tool in enumerate(tool_states)]
        for tool in tools:
            tool.setOthers(tools)
        z -= len(tool_states) * TOOL_SPACE
        # level selection
        DirectLabel(
            parent=self.toolbox,
            text="Level",
            scale=SCALE,
            pos=(MIN_X + LEFT_TOOL_MARGIN, 0, z))
        z -= TOOL_SPACE
        self.level = N
        self.levels = DirectOptionMenu(
            parent=self.toolbox,
            scale=SCALE,
            pos=(MIN_X + LEFT_TOOL_MARGIN, 0, z),
            items=list(map(str, range(1, N + 1))),
            initialitem=str(N),
            command=lambda level: self.set_level(int(level)))
        z -= TOOL_SPACE
        # player (color) selection
        DirectLabel(
            parent=self.toolbox,
            text="Player",
            scale=SCALE,
            pos=(MIN_X + LEFT_TOOL_MARGIN, 0, z))
        z -= TOOL_SPACE
        # ADD: <colors>
        # ADD: brush preview
        # self.set_brush()
        self.setup_actions()

    def set_properties(self):
        prop = WindowProperties()
        prop.setTitle(self.title)
        self.win.requestProperties(prop)

    def setup_actions(self):
        # self.accept("mouse1")
        self.accept('escape', self.quit)

    def set_title(self, title):
        prop = WindowProperties()
        prop.setTitle(self.title + " - " + title)
        self.win.requestProperties(prop)

    def set_tool(self):
        self.set_brush()

    def set_brush(self):
        self.brush = ...
        # self.brush.reparentTo(self.mouseWatcher)

    def set_level(self, level):
        self.level = level
        self.set_brush()

    def new_menu(self, text, nx, itemzip=(), setter=None, shortcuts=()):
        items, _ = zip(*itemzip)
        DirectOptionMenu(
            parent=self.menu,
            pos=(MIN_X + nx * MENU_SPACE, 0, MAX_Z - TOP_MENU_MARGIN),
            items=items,
            scale=SCALE,
            initialitem='',
            command=lambda value: (dict(itemzip)[value] or (lambda: None))(),
            text=text)
        # Menu(
        #     parent=self.menu, ...
        # )

    def quit(self):
        self.destroy()
        if self.return_map:
            self.messenger.send("return_map", self.map)
        else:
            exit()


def main():
    Editor().run()


if __name__ == '__main__':
    main()
