import os
import fnmatch
import pygame
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT, K_RETURN

import pgu_gui as gui

from preference import request
from core import formats
import core
import preference

td_style = request("core.style")
enter_pressed = lambda e: e.type == gui.KEYDOWN and e.key == K_RETURN

class FileDialog(gui.Dialog):
    """All-purpose file dialog class, partially borrowed from pgu/gui"""
    LIST_WIDTH = request("dialog.file_dialog.list_width")
    LIST_HEIGHT = request("dialog.file_dialog.list_height")
    
    def __init__(self, title_text="File Browser", button_text="Okay", cls="dialog", path=None, preview=None, exts=['any'], save=False):
        """
            title_text -- title
            button_text -- button text
            path -- initial path
            preview -- instance of Preview class or None
            load_condition -- lambda filename: True/False
            ext -- initial format name
            exts -- [Format(...), ...]
            save -- check filename on existance (default: False)
        """
        if exts is None:
            exts = ['any']
        if 'any' not in exts:
            exts.append('any')
        self.formats = {name: formats[name] for name in exts}
        self.formats['any'] = formats['any']
        self.ext = exts[0]
        self.exts = exts
        self.save = save
        cls1 = "filedialog"
        if not path:
            self.curdir = os.getcwd()
        else: self.curdir = path
        self.dir_img = gui.Image(
            gui.pguglobals.app.theme.get(cls1 + ".folder", "", 'image'))
        self.title = gui.Label(title_text, cls=cls + ".title.label")
        self.body = gui.Table()
        self.list = gui.List(width=self.LIST_WIDTH, height=self.LIST_HEIGHT)
        self.input_dir = gui.Input()
        self.input_file = gui.Input()
        self.selector = gui.Select(value=self.ext)
        for name in self.exts:
            self.selector.add(formats[name].description, name)
        self.selector.connect(gui.CHANGE, self._new_ext)
        self._list_dir()
        self.button_ok = gui.Button(button_text)
        self.body.tr()
        self.body.td(gui.Label("Folder"), style=td_style, align=-1)
        self.body.td(self.input_dir, style=td_style)
        add_event_handler(self.input_dir, enter_pressed, self._dir_enter)
        self.body.tr()
        self.body.td(self.list, colspan=3, style=td_style)
        self.list.connect(gui.CHANGE, self._new_item)
        self.button_ok.connect(gui.CLICK, self._button_okay_clicked)
        self.preview = preview
        if preview is not None:
            self.body.td(self.preview, style=td_style)
        self.body.tr()
        self.body.td(gui.Label("File"), style=td_style, align=-1)
        add_event_handler(self.input_file, enter_pressed, self._file_enter)
        # self.input_file.event = _extended_event_handler(self.input_file, enter_pressed, self._file_enter)
        self.body.td(self.input_file, style=td_style)
        self.body.td(self.selector, style=td_style)
        self.body.td(self.button_ok, style=td_style)
        self.value = None
        gui.Dialog.__init__(self, self.title, self.body)
        arrow_pressed = lambda e: e.type == gui.KEYDOWN and e.key in (K_UP, K_DOWN, K_LEFT, K_RIGHT)
        add_event_handler(self, arrow_pressed, self._on_arrow_pressed)
        
    def _list_dir(self):
        self.list.clear()
        ext_filter = formats[self.selector.value].filter
        self.input_dir.value = self.curdir
        self.input_dir.pos = len(self.curdir)
        self.input_dir.vpos = 0
        dirs = []
        files = []
        try:
            for i in os.listdir(self.curdir):
                if os.path.isdir(os.path.join(self.curdir, i)):
                    dirs.append(i)
                elif fnmatch.fnmatch(i, ext_filter):
                    files.append(i)
        except:
            self.input_file.value = "NO ACCESS"
        #if '..' not in dirs: dirs.append('..')
        dirs.sort()
        dirs = ['..'] + dirs
        
        files.sort()
        for i in dirs:
            #item = ListItem(image=self.dir_img, text=i, value=i)
            self.list.add(i, image=self.dir_img, value=i)
        for i in files:
            #item = ListItem(image=None, text=i, value=i)
            self.list.add(i, value=i)
        #self.list.resize()
        self.list.set_vertical_scroll(0)
        #self.list.repaintall()     
        
    def _new_item(self):
        self.input_file.value = self.list.value
        filename = os.path.abspath(os.path.join(self.curdir, self.input_file.value))
        if os.path.isdir(filename):
            self.input_file.value = ""
            self.curdir = filename
            self._list_dir()
            if self.preview is not None:
                self.preview.clear()
        elif self.preview is not None and os.path.isfile(filename):
            f = formats[self.selector.value]
            if f.map_loader is not None and f.check(filename):
                self.preview.set_map(f.map_loader(filename))
            elif f.map_loader is None:
                fs = [formats[name] for name in self.exts if formats[name].map_loader is not None and formats[name].check(filename)]
                if fs:
                    self.preview.set_map(fs[0].map_loader(filename))
                else:
                    self.preview.clear()
            else:
                self.preview.clear()

    def _new_ext(self):
        self.ext = self.selector.value
        f = formats[self.ext]
        if self.preview is not None:
            filename = os.path.abspath(os.path.join(self.curdir, self.input_file.value))
            if f.map_loader is not None and f.check(filename):
                self.preview.set_map(f.map_loader(filename))
            elif f.map_loader is None:
                fs = [formats[name] for name in self.exts if formats[name].map_loader is not None and formats[name].check(filename)]
                if fs:
                    self.preview.set_map(fs[0].map_loader(filename))
                else:
                    self.preview.clear()
            else:
                self.preview.clear()
        self._list_dir()

    def new_filename(self, filename):
        self.input_file.value = filename

    def _dir_enter(self, event):
        if os.path.isdir(self.input_dir.value) and os.path.abspath(self.input_dir.value) != os.path.abspath(self.curdir):
            self.input_file.value = ""
            self.curdir = os.path.abspath(self.input_dir.value)
            self.list.clear()
            self._list_dir()
            if self.preview is not None:
                self.preview.clear()

    def _on_arrow_pressed(self, e):
        # BUG: arrows selection does not cancel previously selected items
        # but they deselected when mouse hover on them
        widgets = self.list.group.widgets
        value = self.list.value
        apt_widgets = [w for w in widgets if w.value == value]
        if widgets and apt_widgets:
            widget = [w for w in widgets if w.value == value][0]
            i = widgets.index(widget)
            if e.key == K_UP and i > 0:
                next_value = widgets[i - 1].value
                if formats[self.ext].check(next_value):
                    self.list.group.value = next_value
            elif e.key == K_DOWN and i < len(widgets) - 1:
                next_value = widgets[i + 1].value
                if formats[self.ext].check(next_value):
                    self.list.group.value = next_value
        if e.key == K_LEFT:
            self.input_dir.value = self.input_dir.value.rsplit('/', 1)[0]
            self._dir_enter(None)

    def _file_enter(self, event):
        self._button_okay_clicked()

    def _button_okay_clicked(self):
        filename = os.path.join(self.curdir, self.input_file.value)
        if self.save:
            if formats[self.ext].check(filename):
                self.value = filename
                self.format = formats[self.selector.value]
                self.send(gui.CHANGE)
                self.close()
            else:
                self.input_file.value = "WRONG FORMAT"
        else:           
            if formats[self.ext].loader != None:
                if os.path.isfile(filename) and formats[self.ext].check(filename):
                    self.value = filename
                    self.format = formats[self.selector.value]
                    self.send(gui.CHANGE)
                    self.close()
                else:
                    self.input_file.value = "WRONG FORMAT"
            else:
                fs = [formats[name] for name in self.exts if formats[name].loader is not None and formats[name].check(filename)]
                if fs:
                    self.selector.value = fs[0].name
                    self.selector.send(gui.CHANGE)
                else:
                    self.input_file.value = "WRONG FORMAT"

class ShowTextDialog(gui.Dialog):

    def __init__(self, title, width=400, height=200):
        self.title = gui.Label(title)
        self.document = gui.Document(width=width)
        self.space = self.title.style.font.size(" ")
        # self.add_block(align=0, text=text)
        # gui.Dialog.__init__(self, title, gui.ScrollArea(self.document, width, height))

    def add_block(self, align, text, space=None, br=None):
        if space is None: space = self.space
        add_block(document=self.document, align=align, text=text, space=space, br=br)

class RulesDialog(ShowTextDialog):

    def __init__(self, title='Rules', width=400, height=200):
        ShowTextDialog.__init__(self, title, width, height)
        self.add_block(align=0, text="Rules of Clonium")
        self.add_block(align=-1, text="* Click on clip and it will grow.")
        self.add_block(align=-1, text="* When a clip grows more than 4 it explode on 4 free neighboring cells and its owner capture them.")
        self.add_block(align=-1, text="* To win you should capture all clips.")
        gui.Dialog.__init__(self, self.title, gui.ScrollArea(self.document, width, height))

class NewGameDialog(gui.Dialog):

    def __init__(self, **params):
        self.title = gui.Label("New game")
        self.value = gui.Form()
        self.table = gui.Table()
        init_td_style(self.table, style=td_style)
        self.table.tr()
        self.table.td(gui.Label("Map"), align=-1, style=td_style)
        self.map_path = gui.Input(request("paths.map_folder"))
        self.table.td(self.map_path, style=td_style)
        self.browse_button = gui.Button("Browse...")
        self.browse_button.connect(gui.CLICK, self.open_map)
        self.table.td(self.browse_button, style=td_style, align=-1)
        self.edit_button = gui.Button("Edit...", align=0)
        # self.edit_button.connect(gui.CLICK, ...) # to map editor: edit: choose if not chosen yet
        self.table.td(self.edit_button, style=td_style)
        self.create_button = gui.Button("Create...", align=0)
        # self.create_button.connect(gui.CLICK, ...) # to map editor: create
        self.table.td(self.create_button, style=td_style)
        self.table.tr()
        self.preview = None
        self.players_table = None
        gui.Dialog.__init__(self, self.title, self.table)
        self.connect(gui.QUIT, self.send, gui.CHANGE)

    def open_map(self):
        fd = FileDialog("Choose map", "Choose",
            path=request("paths.map_folder"),
            preview=Preview(display_players=False),
            exts=['map']
            )
        fd.connect(gui.CHANGE, self.load_map, fd)
        fd.open()

    def show_players_preference(self):
        self.players = core.map_players(self.map)
        self.bots = {}
        self.bot_buttons = {}
        if self.preview is None:
            self.preview = Preview()
            self.table.td(self.preview, style=td_style)
        self.preview.set_map(self.map)
        if self.players_table:
            self.table.remove(self.players_table)
        self.players_table = gui.Table()
        init_td_style(self.players_table, style=td_style)
        self.players_table.td(gui.Label("Players:"), style=td_style)
        self.players_table.tr()
        self.strategy_labels = {}
        for i in sorted(self.players):
            self.players_table.td(gui.Label("Player #{}:".format(i)), style=td_style)
            self.players_table.td(gui.Label("Bot"), style=td_style)
            self.bot_buttons[i] = gui.Switch(False)
            self.bot_buttons[i].connect(gui.CHANGE, self.tune_bot, i)
            self.players_table.td(self.bot_buttons[i], style=td_style)
            self.preference_button = gui.Button("Settings")
            self.preference_button.connect(gui.CLICK, self.show_player_preference, i)
            self.players_table.td(self.preference_button, style=td_style)
            self.strategy_labels[i] = gui.Input('', size=10)
            self.players_table.td(self.strategy_labels[i], style=td_style)
            self.players_table.tr()
        self.table.td(self.players_table, style=td_style)
        self.save_name_input = gui.Input(request("paths.autosave_name"))
        self.save_name_input.connect(gui.CHANGE, self.new_name)
        self.new_name()
        self.players_table.td(self.save_name_input)
        self.players_table.tr()
        self.start_button = gui.Button("  Start  ")
        self.start_button.connect(gui.CLICK, self.send, gui.CHANGE)
        self.players_table.td(self.start_button, style=td_style)

    def new_name(self):
        self.filename = preference.save_filename(self.save_name_input.value)

    def tune_bot(self, i):
        if self.bot_buttons[i].value:
            self.bots[i] = self.strategy_labels[i].value = request("core.bot")
        else:
            del self.bots[i]
            self.strategy_labels[i].value = ''

    def restrategy(self):
        for l in self.strategy_labels.values():
            l.value = l.value

    def deep_bot(self, i):
        if self.bot_switcher.value:
            self.bot_buttons[i].value = True
            self.bots[i] = self.strategy_labels[i].value = self.selector.value
        else:
            self.bot_buttons[i].value = False
            if i in self.bots:
                del self.bots[i]
            self.strategy_labels[i].value = ''
        self.preference_dialog.close()

    def show_player_preference(self, i):
        self.preference_title = gui.Label("Player #{} preference".format(i))
        self.preference_form = gui.Form()
        self.preference_table = gui.Table()
        self.preference_table.td(gui.Label("Bot"), style=td_style)
        self.bot_switcher = gui.Switch(self.bot_buttons[i].value)
        self.preference_table.td(self.bot_switcher, style=td_style)
        self.preference_table.tr()
        self.preference_table.td(gui.Label("Strategy"), style=td_style)
        self.preference_table.tr()
        self.selector = gui.Select(value=self.bots.get(i, None) or request("core.bot"))
        for name, value in sorted(request("core.bots").items()):
            self.selector.add(name, value)
        self.preference_table.td(self.selector, style=td_style)
        self.preference_table.tr()
        self.apply_button = gui.Button("  Apply  ")
        self.apply_button.connect(gui.CLICK, self.deep_bot, i)
        self.preference_table.td(self.apply_button, style=td_style, align=0)

        self.preference_dialog = gui.Dialog(self.preference_title, self.preference_table)
        self.preference_dialog.open()

    def load_map(self, fd):
        filename = fd.value
        if filename:
            self.map_path.value = filename
            loader = fd.format.map_loader
            self.map = loader(filename)
            self.show_players_preference()

class Preview(gui.Widget):

    width = request("preview.width")
    height = request("preview.height")
    color = request("preview.background_color")
    items = core.load_items()

    def __init__(self, display_players=True, **params):
        gui.Widget.__init__(self, width=self.width, height=self.height, **params)
        self.display_players = display_players
        self.surface = pygame.Surface((self.width, self.height))
        self.shift = (0, 0)
        self.surface.fill(self.color)
        self.repaint()

    def clear(self):
        self.surface.fill(self.color)
        self.repaint()

    def set_map(self, board):
        self.surface.fill(self.color)
        self.font = core.load_font(request("preview.font.name"), request("preview.font.size"))
        self.cell_size = core.calculate_cell_size(min_size=min(self.width, self.height), board=board)
        self.items = core.transformed_items(items=Preview.items, cell_size=self.cell_size)
        self.shift = core.shift(board)
        # bg
        for pos in board:
            pygame.draw.rect(self.surface, request("board.cell_color"), self.expand4(pos, self.shift, margin=1))
        # clips
        for pos, pair in board.items():
            if pair[1] != 0:
                self.surface.blit(self.items[pair[1]][pair[0]], self.expand2(pos, self.shift))
        if self.display_players:
            # players
            for pos, pair in board.items():
                if pair[1] != 0:
                    text = self.font.render(str(pair[0]), True, request("preview.font.color"))
                    self.surface.blit(text, self.expand2(pos, self.shift))
        self.repaint()

    def paint(self, surface):
        surface.blit(self.surface, (0, 0))

    def expand4(self, pos, shift=(0, 0), margin=0):
        return core.expand4(self.cell_size, pos, shift, margin=margin)

    def expand2(self, pos, shift=(0, 0), margin=0):
        return core.expand2(self.cell_size, pos, shift, margin=margin)

def add_block(document, align, text, space, br=None):
    if br is None: br = space[1]
    document.block(align=align)
    for word in text.split(' '):
        document.add(gui.Label(word))
        document.space(space)
    document.br(br)

def add_event_handler(instance, condition, action):
    instance.event = _extended_event_handler(instance, condition, action)

def _extended_event_handler(instance, condition, action):
    def event_handler(e):
        instance.__class__.event(instance, e)
        if condition(e):
            action(e)
    return event_handler

def new_event_handler(instance, condition, action):
    instance.event = _new_event_handler(instance, condition, action)

def _new_event_handler(instance, condition, action):
    def event_handler(e):
        if condition(e):
            action(e)
    return event_handler

def init_td_style(instance, style=td_style):
    """set default style for x.td(..., style=...)"""
    def new_td(*pargs, **kwargs):
        new_style = kwargs.pop('style', style)
        instance.__class__.td(instance, *pargs, style=new_style, **kwargs)
    instance.td = new_td

class NewMapDialog(gui.Dialog):

    def __init__(self, filename=request("dialog.new_map_dialog.filename")):
        self.filename = filename
        title = gui.Label("New map")
        self.table = table = gui.Table()
        table.tr()
        table.td(gui.Label("Width"), style=td_style)
        table.td(gui.Label("Height"), style=td_style)
        table.tr()
        self.width_input = gui.Input(str(request("dialog.new_map_dialog.board_width")), size=5)
        table.td(self.width_input, style=td_style)
        self.height_input = gui.Input(request("dialog.new_map_dialog.board_height"), size=5)
        table.td(self.height_input, style=td_style)
        add_event_handler(self.width_input, enter_pressed, lambda e: self.new_size())
        add_event_handler(self.height_input, enter_pressed, lambda e: self.new_size())
        table.tr()
        show_button = gui.Button('Show')
        show_button.connect(gui.CLICK, self.new_size)
        table.td(show_button, style=td_style)
        self.board = core.rectangle_board(request("dialog.new_map_dialog.board_width"), request("dialog.new_map_dialog.board_height"))
        self.preview = Preview()
        table.tr()
        table.td(self.preview, style=td_style)
        self.preview.set_map(self.board)
        table.tr()
        self.filename_input = gui.Input(self.filename)
        table.td(self.filename_input)
        table.tr()
        button = gui.Button('  Ok  ')
        table.td(button, style=td_style)
        button.connect(gui.CLICK, self.ok_clicked)
        gui.Dialog.__init__(self, title, table)

    def new_size(self):
        self.board = core.rectangle_board(int(self.width_input.value), int(self.height_input.value))
        self.preview.set_map(self.board)

    def ok_clicked(self):
        self.value = core.rectangle_board(int(self.width_input.value), int(self.height_input.value))
        self.filename = preference.map_filename(self.filename_input.value)
        self.send(gui.CHANGE)

class ImageWidget(gui.Widget):

    def __init__(self, image, image_place=(0, 0), **params):
        self.image = image
        self.image_place = image_place
        gui.Widget.__init__(self, **params)

    def paint(self, surface):
        surface.fill(request("preview.background_color"))
        surface.blit(self.image, self.image_place)

    def new_image(self, image, image_place=(0, 0)):
        self.image = image
        self.repaint()
