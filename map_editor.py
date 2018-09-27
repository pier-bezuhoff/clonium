import pygame
from sys import exit as sys_exit

import pgu_gui as gui

from widgets import FileDialog, Preview, ImageWidget, NewMapDialog, add_event_handler, enter_pressed
import preference
import core
request = preference.request

td_style = request("core.style")


class MapEditor(gui.Desktop):

    items = core.load_items()
    items = core.transformed_items(items, cell_size=request("map_editor.cell_size"))
    theme = gui.Theme(preference.theme())

    def __init__(self, board=None, **params):
        pygame.display.set_mode((request("map_editor.width"), request("map_editor.height")))
        gui.Desktop.__init__(self, theme=self.theme, **params)
        self.connect(gui.QUIT, self.quit)
        self.board = board
        container = gui.Container(width=request("map_editor.width"), height=request("map_editor.height"))

        spacer = request("map_editor.space_size")

        self.new_dialog = NewMapDialog()
        self.new_dialog.connect(gui.CHANGE, self.action_new)
        self.open_dialog = FileDialog("Choose map", "Choose",
            path=request("paths.map_folder"),
            preview=Preview(display_players=False),
            exts=['map', 'state', 'history'])
        self.open_dialog.connect(gui.CHANGE, self.new_map)
        self.save_dialog = FileDialog("Enter filename to save with", "Choose",
            path=request("paths.map_folder"),
            exts=['map'],
            save=True)
        self.save_dialog.connect(gui.CHANGE, self.action_saveas)

        # self.help_dialog = HelpDialog()
        # QUESTION: may be put it into json: {"<menu>": "<method name>", ...}
        self.menus = menus = gui.Menus([
            ('File/New', self.new_dialog.open, None),
            ('File/Open', self.open_dialog.open, None),
            ('File/Save', self.action_save, None),
            ('File/Save As', self.save_as, None),
            ('File/Exit', self.quit, None),
            ('Add/Extend', self.extend, None),
            ('Add/Add top row', self.add_top_row, None),
            ('Add/Add bottom row', self.add_bottom_row, None),
            ('Add/Add left column', self.add_left_column, None),
            ('Add/Add right column', self.add_right_column, None),
            ('Add/Add cells', self.add_cells, None),
            ('Remove/Reduce', self.reduce, None),
            ('Remove/Remove top row', self.remove_top_row, None),
            ('Remove/Remove bottom row', self.remove_bottom_row, None),
            ('Remove/Remove left column', self.remove_left_column, None),
            ('Remove/Remove right column', self.remove_right_column, None),
            ('Remove/Remove the same clips', self.remove_same_clips, None),
            ('Remove/Remove clips with the same player', self.remove_same_player_clips, None),
            ('Remove/Remove clips with the same amount', self.remove_same_amount_clips, None),
            ('Remove/Remove all clips', self.remove_clips, None),
            ('Remove/Remove cells', self.remove_cells, None),
            ('Edit/Permute cells', self.permute_cells, None),
            ('Edit/Permute players', self.permute_players, None),
            ('Edit/Permute clips', self.permute_clips, None)
            # ('Help/Help', self.help_dialog.open)
            ])
        container.add(self.menus, 0, 0)
        self.menus.rect.w, self.menus.rect.h = menus.resize()
        self.filename_input = gui.Input("")
        container.add(self.filename_input, self.menus.rect.w + spacer, 0)

        # # new ::
        # self.mode = mode = gui.Group(name="brushes", value='player')
        # cell_tool = gui.Tool(self.mode, "Cell", 'cell')
        # empty_tool = gui.Tool(self.mode, "Empty", 'none')
        # player_tool = gui.Tool(self.mode, "Player", 'player')
        # # :: new
        self.mode = mode = gui.Toolbox([
            ('Cell', 'cell'),
            ('Empty', 'none'),
            ('Player', 'player')
            ], cols=1, value='player') # NOTE: DEPERECATED
        self.mode.connect(gui.CHANGE, self.set_brush)
        self.player = request("map_editor.player")
        self.amount = request("map_editor.amount")
        container.add(mode, 0, self.menus.rect.bottom + spacer)
        # # new ::
        # container.add(cell_tool, 0, self.menus.rect.bottom + spacer)
        # container.add(empty_tool, 0, cell_tool.rect.bottom + spacer)
        # container.add(cell_tool, 0, empty_tool.rect.bottom + spacer)
        # # :: new
        mode.rect.x, mode.rect.y = mode.style.x, mode.style.y
        mode.rect.w, mode.rect.h = mode.resize()

        self.player_table = gui.Table()
        self.player_table.td(gui.Label("Holes"))
        self.player_table.tr()
        self.selector = gui.Select(value=request("map_editor.amount"))
        for i in sorted(self.items.keys()):
            self.selector.add(str(i), i)
        self.selector.connect(gui.CHANGE, self.new_amount)
        self.player_table.td(self.selector, style=td_style)
        self.player_table.tr()
        self.player_table.tr()
        self.player_button = gui.Button('Player')
        self.player_table.td(self.player_button, style=td_style)
        self.player_button.connect(gui.CLICK, self.choose_player)
        self.player_table.tr()
        self.player_input = gui.Input(str(self.player), size=5)
        add_event_handler(self.player_input, enter_pressed, lambda e: self.new_player())
        self.player_table.td(self.player_input, style=td_style)
        self.player_table.tr()
        self.clip = ImageWidget(image=self.items[self.amount][self.player], width=request("map_editor.view_width"), height=request("map_editor.view_height"))
        self.player_table.td(self.clip, style=td_style)
        self.player_table.tr()
        # self.color = gui.Color("#000000", width=mode.rect.w, height=mode.rect.w)
        # self.color.connect(gui.CLICK, self.choose_player)
        # self.player_table.td(self.color, style=td_style)
        container.add(self.player_table, 0, mode.rect.bottom + spacer)

        self.painter = Painter(width=container.rect.w - mode.rect.w-spacer*2,
            height=container.rect.h - self.menus.rect.h - spacer*2, style={'border': 1})
        container.add(self.painter, mode.rect.w + spacer, self.menus.rect.h + spacer)
        if board:
            self.painter.set_map(board)
        self.painter.rect.w, self.painter.rect.h = self.painter.resize()

        self.widget = container

    def extend(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.extend())

    def reduce(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.reduce())

    def add_top_row(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.add_top_row())

    def add_bottom_row(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.add_bottom_row())

    def add_left_column(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.add_left_column())

    def add_right_column(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.add_right_column())

    def remove_top_row(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.remove_top_row())

    def remove_bottom_row(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.remove_bottom_row())

    def remove_left_column(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.remove_left_column())

    def remove_right_column(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.remove_right_column())

    def remove_same_clips(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.empty_cells(condition=lambda cell: cell == (self.player, self.amount)))

    def remove_same_player_clips(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.empty_cells(condition=lambda cell: cell[0] == self.player))

    def remove_same_amount_clips(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.empty_cells(condition=lambda cell: cell[1] == self.amount))

    def remove_clips(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.empty_cells())

    def remove_cells(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.remove_all_cells())

    def add_cells(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.fill_cells())

    def permute_players(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.permute_players())

    def permute_clips(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.permute_checkers())

    def permute_cells(self, *pargs):
        if self.painter.board is not None:
            self.painter.set_map(self.painter.board.permute_cells())

    def choose_player(self):
        if self.painter.board is not None:
            title = gui.Label("Choose player")
            table = gui.Table()
            players = list(sorted(self.painter.board.players))
            radios = gui.Group(value=self.player_input.value)
            for player in players:
                table.td(gui.Radio(radios, value=str(player)), style=td_style)
            table.tr()
            for player in players:
                table.td(ImageWidget(image=self.items[self.amount][player], style=td_style,
                    width=request("map_editor.view_width"), height=request("map_editor.view_height")))
            button = gui.Button("  Apply  ")
            table.tr()
            table.td(button, style=td_style)
            dialog = gui.Dialog(title, table)
            def on_click():
                dialog.value = int(radios.value)
                dialog.send(gui.CHANGE)
                dialog.close()
            button.connect(gui.CLICK, on_click)
            dialog.connect(gui.CHANGE, lambda: self.new_player(dialog.value))
            dialog.open()

    def parse_player(self):
        s = self.player_input.value
        if s.isdigit():
            return int(s)
        else:
            print("WARNING: Wrong `player`: '{}', `player` must be an integer".format(s))

    def new_player(self, player=None):
        if player is None: player = self.parse_player()
        if player in range(len(self.items[1])):
            self.player = player
            self.player_input.value = str(self.player)
            self.clip.new_image(self.items[self.amount][self.player])
            if self.painter.board is not None:
                self.set_brush()
        else:
            print("WARNING: Wrong `player`: '{}', applicable players: {}".format(player, list(range(len(self.items[1])))))

    def new_amount(self):
        if self.selector.value in self.items.keys():
            self.amount = self.selector.value
            self.clip.new_image(self.items[self.amount][self.player])
            self.set_brush()
        else:
            print("WARNING: Wrong amount: {}, applicable amounts: {}".format(self.selector.value, list(self.items.keys())))

    def set_brush(self):
        self.painter.set_brush(brush=self.mode.value, player=self.player, amount=self.amount)

    def action_new(self):
        self.new_dialog.close()
        self.filename = self.new_dialog.filename
        self.filename_input.value = self.filename.split('/')[-1]
        board = self.new_dialog.value
        self.painter.set_map(board)
        self.set_brush()

    def action_save(self, *pargs):
        if self.painter.board is not None:
            core.save_map(self.painter.board, self.filename, full=True)
        else:
            print("WARNING: Nothing done, nothing to save")

    def quit(self, *pargs):
        # ask save
        sys_exit()

    def save_as(self, *pargs):
        if self.painter.board is not None:
            self.save_dialog.new_filename(self.filename_input.value)
            self.save_dialog.open()
        else:
            print("WARNING: Nothing done, nothing to save")

    def action_saveas(self):
        self.save_dialog.close()
        self.filename = self.save_dialog.value
        self.filename_input.value = self.filename.split('/')[-1]
        core.save_map(self.painter.board, self.filename, full=True)

    def new_map(self):
        self.open_dialog.close()
        self.filename = self.open_dialog.value
        loader = self.open_dialog.format.loader
        self.painter.set_map(board=loader(self.filename))
        self.set_brush()
        name, ext = self.filename.rsplit('.', 1)
        self.filename = request("map_editor.autosave_pattern").format(name=name, ext=ext)
        self.filename_input.value = self.filename.split('/')[-1]


class Painter(gui.Widget):

    items = core.load_items()
    cell_image = pygame.image.load(preference.cell_brush_filename())
    none_image = pygame.image.load(preference.none_brush_filename())

    def __init__(self, width, height, **params):
        gui.Widget.__init__(self, width=width, height=height, **params)
        self.board = None
        self.shift = None
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
        self.overlay = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        self.brush = None
        self.player = None
        self.amount = None
        self.state = 0 # 1 = draw with self.brush
        self.shown_brush = request("map_editor.show_brush")
        self.background_color = request("map_editor.background_color")
        self.cell_color = request("board.cell_color")
        self.overlay_color = request("map_editor.overlay_color")
        self.surface.fill(self.background_color)
        self.overlay.fill(self.overlay_color)
        self.repaint()

    def set_map(self, board):
        self.board = board
        self.cell_size = core.calculate_cell_size(min_size=min(self.width, self.height), board=board)
        self.items = core.transformed_items(items=Painter.items, cell_size=self.cell_size)
        self.cell_image = pygame.transform.smoothscale(Painter.cell_image, (self.cell_size, self.cell_size))
        self.none_image = pygame.transform.smoothscale(Painter.none_image, (self.cell_size, self.cell_size))
        self.shift = board.shift
        self.repaint()

    def set_brush(self, brush, player, amount):
        self.brush = brush
        self.player = player
        self.amount = amount

    def event(self, e):
        if self.board and self.brush:
            if e.type == gui.MOUSEBUTTONDOWN:
                self.state = 1
                self.draw_brush(e.pos)
            if e.type == gui.MOUSEMOTION:
                if self.state == 1:
                    self.draw_brush(e.pos)
                    if self.shown_brush:
                        self.show_brush(e.pos)
            if e.type == gui.MOUSEBUTTONUP:
                self.state = 0
                self.overlay.fill(self.overlay_color)
                self.repaint()

    def paint(self, surface):
        if self.board is not None:
            self.draw_map()
        surface.blit(self.surface, (0, 0))
        surface.blit(self.overlay, (0, 0))

    def draw_brush(self, pos):
        self.overlay.fill(self.overlay_color)
        cell_pos = core.reduce2(cell_size=self.cell_size, pos=pos)
        cell_pos = (cell_pos[0] - self.shift[0], cell_pos[1] - self.shift[1])
        if self.brush == 'cell':
            self.draw_cell(cell_pos)
        elif self.brush == 'none':
            self.draw_none(cell_pos)
        elif self.brush == 'player':
            self.draw_player(cell_pos)
        self.repaint()

    def show_brush(self, pos):
        if self.brush == 'cell':
            self.overlay.blit(self.cell_image, (pos[0] - int(self.cell_size//2), pos[1] - int(self.cell_size//2)))
        elif self.brush == 'none':
            self.overlay.blit(self.none_image, (pos[0] - int(self.cell_size//2), pos[1] - int(self.cell_size//2)))
        elif self.brush == 'player':
            self.overlay.blit(self.items[self.amount][self.player], (pos[0] - int(self.cell_size//2), pos[1] - int(self.cell_size//2)))

    def draw_cell(self, cell_pos):
        self.board[cell_pos] = (0, 0)

    def draw_none(self, cell_pos):
        if cell_pos in self.board:
            del self.board[cell_pos]

    def draw_player(self, cell_pos):
        if cell_pos in self.board:
            self.board[cell_pos] = (self.player, self.amount)

    def draw_map(self):
        self.draw_background()
        self.draw_items()

    def draw_background(self):
        self.surface.fill(self.background_color)
        for pos in self.board:
            pygame.draw.rect(self.surface, self.cell_color, self.expand4(pos, self.shift, margin=1))

    def draw_items(self):
        core.draw_items(self.surface, self.board, self.items, self.cell_size, self.shift)

    def expand4(self, pos, shift=(0, 0), margin=0):
        return core.expand4(self.cell_size, pos, shift, margin=margin)

    def expand2(self, pos, shift=(0, 0), margin=0):
        return core.expand2(self.cell_size, pos, shift, margin=margin)


def main():
    MapEditor().run()


if __name__ == '__main__':
    main()
