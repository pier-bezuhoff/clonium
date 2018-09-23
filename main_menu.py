#!/usr/bin/env python3

from tkinter import ttk
# panfa3d
from direct.showbase.DirectObject import DirectObject
from panda3d.core import TextNode
from direct.gui.DirectGui import *

# game
from gui import * 
import core
from preference import request

TEXTS = (
    "New game", "Load game",
    "Create board",
    "Preference", "Quit"
)

WIDTH = request('menu.width')
HEIGHT = request('menu.height')
TOP_MARGIN = request('menu.top_margin')
BOTTOM_MARGIN = request('menu.bottom_margin')

SCALE = 0.07
DIALOG_BUTTON_PAD = (0.02, 0.02)

NEW_GAME_DIALOG_POS = (0, 0.1, 0.5)
CONSTRUCT_BOARD_DIALOG_POS = (0, 0.1, -0.3)


class MainMenu(ttk.Frame):

    def __init__(self, app):
        master = app.tkRoot
        self.app = app
        ttk.Frame.__init__(self, master)
        self.bind('Escape', self.quit)
        self.bind('Return', self.new_game)
        table = (
            ("New game", self.new_game),
            ("Load game", self.load_game),
            ("Create board", self.create_board),
            ("Preference", self.preference),
            ("Quit", self.quit)
        )
        self.buttons = {}
        for i, (name, callback) in enumerate(table, 1):
            self.buttons[name] = button = ttk.Button(self, text=name, command=callback)
            button.grid(row=i)
        style = ttk.Style(self)
        style.theme_use("classic")
        style.configure(
            "TButton",
            padding=6,
            relief="flat",
            font="Ubuntu 16")

    def new_game(self, event=None):
        self.new_default_game()

    def start_game(self, board, bots=None, order=None):
        self.destroy()
        self.app.startGame(board=board, bots=bots, order=order)

    # tmp
    def new_default_game(self):
        board = core.Board.new_rounded_rectangle(6, 6, 0)
        board.spawn2(padding=1)
        bots = {1: 'levels-2'}
        order = None
        self.start_game(board, bots, order)

    def load_game(self, event=None):
        print("MainMenu.load_game")

    def create_board(self, event=None):
        print("MainMenu.create_board")

    def preference(self, event=None):
        print("MainMenu.preference")

    def quit(self, event=None):
        self.destroy()
        messenger.send('quit')

class NewGameDialog:
    pass

class _MainMenu(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.frame = DirectFrame(
            frameSize=frame_size(request('menu.width'), request('menu.height')),
            relief=DGG.RIDGE,
            borderWidth=(0.1, 0.1),
            frameColor=(1, 0.8, 1, 1),
            # image="<filename>"
        )
        for n, text in enumerate(TEXTS):
            self.new_menu_button(
                parent=self.frame,
                text=text,
                n=n)
        self.setup_actions()

    def setup_actions(self):
        self.accept_keys()
        self.accept('quit', self.quit)
        self.accept('show_main_menu', self.show)
        self.accept('hide_main_menu', self.hide)
        self.accept('show_results', ResultsDialog)
        self.accept('new_game', self.new_game)
        self.accept('load_game', self.new_default_game)

    # tmp
    def new_default_game(self):
        board = core.Board.new_rounded_rectangle(6, 6, 0)
        board.spawn2(padding=1)
        bots = {1: 'levels-2'}
        order = None
        messenger.send('hide_main_menu')
        messenger.send('start_game', [board, bots, order])

    def new_menu_button(self, parent, text, n):
        return DirectButton(
            parent=parent,
            text=text,
            # frameColor=(0, 0, 0, 1),
            text_fg=(0.2, 0.2, 1, 1),
            # text_bg=(0, 0, 0, 1),
            pos=(0, 0, HEIGHT / 2 - TOP_MARGIN - n *
                (HEIGHT - TOP_MARGIN - BOTTOM_MARGIN) / (len(TEXTS) - 1)),
            scale=SCALE,
            relief=DGG.RAISED,
            borderWidth=(0.1, 0.1),
            pad=(0.2, 0.2),
            command=self.button_sender(text))

    def button_sender(self, text):
        "-> `text` sender"
        event = text.replace(' ', '_').lower()

        def send():
            messenger.send(event)
        return send

    def new_game(self):
        "show NewGameDialog"
        NewGameDialog(on_born=self.accept_keys)

    def accept_keys(self):
        self.accept('escape', lambda: messenger.send('quit'))
        self.accept('enter', self.new_game)

    def ignore_keys(self):
        self.ignore('escape')
        self.ignore('enter')

    def show(self):
        "show & 'escape' -> quit"
        self.accept_keys()
        self.frame.show()

    def hide(self):
        "hide & ignore 'escape'"
        self.ignore_keys()
        self.frame.hide()

    def quit(self):
        self.frame.destroy()


class _NewGameDialog(ReactiveDialog):

    def __init__(self, **kwargs):
        ReactiveDialog.__init__(
            self,
            text="First choose board",
            pos=NEW_GAME_DIALOG_POS,
            buttonTextList=["Browse", "Quickly construct", "Create"],
            buttonValueList=['browse', 'construct', 'create'],
            **kwargs)
        self.reactions = {
            'browse': lambda: print('browse...'),
            'construct': self.construct_board,
            'create': lambda: print('create...')
        }
        self.start_button = DirectButton(
            parent=self,
            text="Start",
            state=DGG.DISABLED,
            scale=SCALE,
            pos=(-0.2, 0, -0.35),
            pad=DIALOG_BUTTON_PAD,
            command=self.return_game)
        self.cancel_button = DirectButton(
            parent=self,
            text="Cancel",
            scale=SCALE,
            pos=(0.2, 0, -0.35),
            pad=DIALOG_BUTTON_PAD,
            command=self.cancel)

        self.board = self.bots = self.order = None

        self.accept_keys()
        self.accept('set_board', self.set_board)

    def accept_keys(self):
        self.accept('escape', self.cancel)
        self.accept('enter', self.return_game)

    def ignore_keys(self):
        self.ignore('escape')
        self.ignore('enter')

    def construct_board(self):
        ConstuctBoardDialog(
            parent=self,
            on_born=self.ignore_keys,
            on_death=self.accept_keys)

    def set_board(self, board):
        print("NewGameDialog.set_board")
        self.board = board
        r, l, b, t = self['frameSize']
        # TODO: calc from preview size
        self['frameSize'] = r, l, -0.9, t
        self.start_button['state'] = DGG.NORMAL
        self.start_button.setPos(-0.2, 0, -0.7)
        self.cancel_button.setPos(0.2, 0, -0.7)
        self.configureDialog()

    def return_game(self):
        if self.start_button['state'] == DGG.NORMAL:
            if self.bots is None:
                self.bots = {2: 'levels-1'}  # tmp
            self.destroy()
            messenger.send('hide_main_menu')
            messenger.send('start_game', [self.board, self.bots, self.order])

    def cancel(self):
        self.destroy()


class ConstuctBoardDialog(ReactiveDialog):

    def __init__(self, **kwargs):
        ReactiveDialog.__init__(
            self,
            pos=CONSTRUCT_BOARD_DIALOG_POS,
            topPad=0.7,
            sidePad=0.5,
            buttonTextList=['Done', 'Cancel'],
            buttonValueList=['done', 'cancel'], **kwargs)
        self.reactions = {
            'cancel': self.cancel,
            'done': self.done
        }

        self.board = None

        wh_height = 0.7
        min_x = -0.3
        self.width_entry = self.new_entry(
            (min_x, 0, wh_height), '5')
        self.new_label(
            (min_x + 0.1, 0, wh_height), " x ")
        self.height_entry = self.new_entry((min_x + 0.2, 0, wh_height), '5')
        self.new_label(
            (min_x, 0, wh_height - 0.2), "Rounded rectangle radius:")
        self.radius_entry = self.new_entry(
            (min_x + 0.2, 0, wh_height - 0.3), '0')
        self.new_label(
            (min_x, 0, wh_height - 0.5), "Players' padding:")
        self.padding_entry = self.new_entry(
            (min_x + 0.2, 0, wh_height - 0.6), '1')

        self.preview = BoardPreview(
            parent=self,
            pos=(0, 0, 0))

        self.accept('escape', self.cancel)
        self.accept('enter', self.done)

    def new_entry(self, pos, initialText, **kwargs):
        return DirectEntry(
            parent=self,
            scale=SCALE,
            width=2,
            pos=pos,
            initialText=initialText,
            command=self.update_preview, **kwargs)

    def new_label(self, pos, text=""):
        return DirectLabel(
            parent=self,
            text=text,
            pos=pos,
            scale=SCALE)

    def update_preview(self, *pargs):
        width_text = self.width_entry.get(plain=False)
        height_text = self.height_entry.get()
        radius_text = self.radius_entry.get()
        padding_text = self.padding_entry.get()
        if width_text.isnumeric() and height_text.isnumeric():
            width = int(width_text)
            height = int(height_text)
            if (radius_text.isnumeric() and
                    int(radius_text) < min(width, height)):
                radius = int(radius_text)
                self.board = core.Board.new_rounded_rectangle(
                    width, height, radius)
            else:
                self.board = core.Board.new_rectplain=Falseangle(width, height)
            if padding_text.isnumeric():
                padding = int(padding_text)
                self.board.spawn4(padding)
            self.preview.set_board(self.board)

    def done(self):
        self.update_preview()
        if self.board is not None:
            messenger.send('set_board', [self.board])
            self.destroy()

    def cancel(self):
        self.destroy()


class ResultsDialog(ReactiveDialog):

    def __init__(self, board, order, loosers, bots, **kwargs):
        FRAME_COLOR = (0.7, 0.7, 0.7, 0.7)
        DIALOG_POS = (0, 0.1, 0)
        LABEL_POS = (-0.5, 0.1, 0.7)
        ReactiveDialog.__init__(
            self,
            frameColor=FRAME_COLOR,
            pos=DIALOG_POS,
            topPad=0.7,
            sidePad=0.1,
            buttonTextList=["Resume", "Restart", "Exit"],
            buttonValueList=['resume', 'restart', 'exit'], **kwargs)

        self.reactions = {
            'resume': self.resume,
            'restart': self.restart,
            'exit': self.exit
        }

        # TODO:
        # results_frame = DirectScrolledFrame(
        #     parent=self,
        #     canvasSize=(-0.5, 0.5, 0, 0.5))

        def player_str(player):
            return ("human" if player not in bots
                else "bot '{}'".format(bots[player]))

        def winner_str(winner):
            return "1) {}: {}/{}".format(
                player_str(winner),
                board.player_population(winner),
                board.player_level(winner))

        def looser_str(ilooser):
            i, looser = ilooser
            return "{}) {}".format(i, player_str(looser))

        header = "\n**Results**"
        winners = "*Winners*\n" + '\n'.join(map(winner_str, order))
        loosers = "*Loosers*\n" + '\n'.join(
            map(looser_str, enumerate(reversed(loosers), 2)))
        ending = ":Game Over:\n"
        # TODO: add timing
        delimiter = '\n' + '~' * 30 + '\n'
        text = '\n' + delimiter.join((header, winners, loosers, ending)) + '\n'
        self.results = DirectLabel(
            parent=self,
            pos=LABEL_POS,
            text=text,
            frameColor=(0, 0, 0, 0),
            scale=SCALE,
            text_align=TextNode.ALeft)

        self.accept('escape', self.resume)
        self.accept('enter', self.exit)

    def resume(self):
        messenger.send('resume_game')
        self.destroy()

    def restart(self):
        messenger.send('restart_game')
        self.destroy()

    def exit(self):
        messenger.send('end_game')
        messenger.send('show_main_menu')
        self.destroy()
