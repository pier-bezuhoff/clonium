from panda3d.core import Vec3, TextureStage
from direct.gui.DirectGui import *

import core
from preference import request_colors

MIN_X = -4 / 3
MAX_X = 4 / 3
MIN_Z = -1
MAX_Z = 1

SCALE = 0.07

PREVIEW_SIZE = (-0.1, 0.1, -0.1, 0.1)

DIALOG_BUTTON_PAD = (0.02, 0.02)


class BoardPreview(DirectFrame):

    def __init__(self, board=None, parent=None, size=PREVIEW_SIZE, **kwargs):
        optiondefs = (('frameSize', size, None),)
        self.defineoptions(kwargs, optiondefs)
        DirectFrame.__init__(self, parent=parent)
        self.initialiseoptions(BoardPreview)

        self.size = min(size[1] - size[0], size[3] - size[2])
        self.center = Vec3((size[0] + size[1]) / 2, 0, (size[2] + size[3]) / 2)
        self.preview = render2d.attachNewNode('board_preview')
        if board is not None:
            self.set_board(board)

    def set_board(self, board):
        print("BoardPreview.set_board\n", board)
        self.board = board
        self.cell_size = 0.5 * self.size / max(board.width, board.height)
        self.outline_size = 0.45 * self.cell_size
        self.shift = board.shift
        self.places = {}
        self.cells = {}
        self.checkers = {}
        self.load_textures()
        self.add_places()
        self.add_cells()
        self.add_checkers()

    def load_textures(self):
        self.textures = {}
        self.textures['cell'] = loader.loadTexture('textures/cell.png')
        self.textures['checker'] = {
            level:
                # loader.loadTexture('textures/checker-{}.png'.format(level))
                loader.loadTexture('textures/checker.png')
            for level in range(1, 10)
        }
        self.cell_ts = TextureStage('cell_stage')
        self.checker_ts = TextureStage('checker_stage')

    def add_place(self, pos):
        place = self.preview.attachNewNode('place-{}'.format(pos))
        place.setPos(self.pos2vector(pos))
        self.places[pos] = place

    def add_places(self):
        for pos in self.board.poss:
            self.add_place(pos)

    def add_cell(self, pos):
        cell = loader.loadModel('models/cell')
        # disable collisions
        # collision = cell.find('**/Collision')
        # collision.setIntoCollideMask(BitMask32.allOff())
        # collision.setFromCollideMask(BitMask32.allOff())

        cell.reparentTo(self.places[pos])
        cell.setScale(self.outline_size)
        cell.setTexture(self.cell_ts, self.textures['cell'])

        self.cells[pos] = cell

    def add_cells(self):
        for pos in self.board.poss:
            self.add_cell(pos)

    def add_checker(self, pos, cell):
        player, level = cell
        checker = loader.loadModel('models/checker-{}'.format(level))
        # disable collisions
        # collision = checker.find('**/Collision')
        # collision.setIntoCollideMask(BitMask32.allOff())
        # collision.setFromCollideMask(BitMask32.allOff())

        checker.reparentTo(self.cells[pos])
        checker.setScale(self.outline_size)
        # checker.setZ(self.checker_height)
        checker.setTexture(self.checker_ts, self.textures['checker'][level])
        checker.setColor(request_colors("board.colors")[player])

        self.checkers[pos] = checker

    def add_checkers(self):
        for pos, cell in self.board.nonempty_part().items():
            self.add_checker(pos, cell)

    def pos2vector(self, pos, z=0):
        x, y, z = core.pos2vector(pos=pos, cell_size=self.cell_size, z=z)
        return self.center + Vec3(x, z, y)


class Menu(DirectButton):
    "DirectButton-based option menu"

    def __init__(self, parent=None, **kwargs):
        """`items` = ["str" or 'None'] where 'None' means separator
        `commands` = [function or 'None'] where 'None' means 'lambda: None'"""
        optiondefs = (
            ("items", (), self.set_items),
            ("commands", (), None),
            ("shorcut_setter", None, self.set_shortcuts),
            ("shorcuts", (), None),
            ("vspace", 0.1, None),
        )
        kwargs['command'] = self.toggle
        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(Menu)
        self.hidden = True

    def set_items(self):
        # TODO: sizes
        self.menu_frame = DirectFrame(
            parent=self)
        self.menu_frame.hide()
        for n, text, command in enumerate(zip(self['items'], self['command'])):
            DirectButton(
                parent=self.menu_frame,
                text=text,
                frameSize=(...),
                command=command or (lambda: None),
            )

    def set_shortcuts(self):
        setter = self['shortcut_setter']
        if setter is not None and self['shortcuts']:
            for shortcut, command in zip(self['shotcuts'], self['commands']):
                if shortcut is not None and command is not None:
                    setter(shortcut, command)

    def toggle(self):
        if self.hidden:
            self.menu_frame.show()
        else:
            self.menu_frame.hide()
        self.hidden = not self.hidden


class ReactiveDialog(DirectDialog):
    "handy superclass for light dialogs"

    def __init__(self, parent=None, on_born=None, on_death=None, **kwargs):
        defaults = {
            'button_pad': DIALOG_BUTTON_PAD,
            'suppressMouse': True,
            'command': self.react
        }

        defaults.update(kwargs)
        kwargs = defaults
        optiondefs = tuple(
            [(key, value, None) for key, value in kwargs.items()])
        self.defineoptions({}, optiondefs)
        DirectDialog.__init__(self, parent=parent)
        self.initialiseoptions(self.__class__)

        # self.on_born = on_born
        if on_born is not None:
            on_born()
        # self.on_death = on_death
        if on_death is not None:
            def destroy():
                on_death()
                self.__class__.destroy(self)
            self.destroy = destroy

    def react(self, value):
        self.reactions.get(value, lambda: None)()


def frame_size(width, height):
    return (-width / 2, width / 2, -height / 2, height / 2)
