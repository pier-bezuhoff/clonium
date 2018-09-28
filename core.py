from random import shuffle, choice, sample
from math import cos, ceil, inf
from itertools import product, chain, tee
from functools import reduce, partial
from collections import deque
from operator import itemgetter
from time import time
import pickle
import pygame

import preference
request = preference.request

BOARD_BACKGROUND_COLOR = request("board.background_color")
BOARD_CELL_COLOR = request("board.cell_color")
BOARD_NEW_TURN_COLOR = request("board.new_turn_color")
BOARD_SELECTION_COLOR = request("board.selection_color")
BOARD_STAT_COLOR = request("board.stat_color")
BOARD_STAT_CENTER = request("board.stat_center")
CORE_COLORS = request("core.colors")
CORE_FONT_NAME = request("core.font.name")
CORE_FONT_SIZE = request("core.font.size")
GAME_FPS = request("game.fps")
GAME_TPS = request("game.tps")
GAME_BLAST_TIME = request("game.blast_time")
SAVE_EXTENSION = request("formats.save.extension")
MAP_EXTENSION = request("formats.map.extension")
MAP_STR_NONE = request("map_str.none")
MAP_STR_EMPTY = request("map_str.empty")
MAP_STR_FILL = request("map_str.fill")
N = 3

loaders = {}
conditions = {}
strategies = {}
animations = {}
items = None



# # ordering functions
def next_player(player, order, shift=1):
    "-> next `shift`-th player in the order, no check"
    return order[(order.index(player) + shift) % len(order)]


def shift_player(player, order, board, shift=1):
    """-> next `shift`-th player in the order;
    there should be **at least one** 'alive' player"""
    player = next_player(player, order, shift)
    order = order.copy()
    while not board.player_alive(player) and order:
        player = next_player(player, order, shift)
        order.remove(player)
    return player


def updated_order(order, board):
    "update `order` with `board`"
    players = board.players
    # there could not be used sets because _order_ does matter
    return [player for player in order if player in players]


# # is-tests
def is_empty_cell(cell):
    "-> whether the `cell` is empty"
    return cell[1] == 0


def is_not_empty_cell(cell):
    "-> whether the `cell` is not empty"
    return cell[1] > 0


# # is-factories
def cell_player_is(player):
    "-> function: (player, level) |-> player == `player`"
    return lambda cell: cell[0] == player


def cell_level_is(level):
    "-> function: (player, level) |-> level == `level`"
    return lambda cell: cell[0] == level


class Board(dict):
    """board ::= {<pos>: <cell>, ...} where
    <pos> ::= (<x>, <y>)
    <cell> ::= (<player>, <level>)"""

    def __repr__(self):
        return board2str(self)

    # creation
    @staticmethod
    def new_rectangle(width, height):
        "-> empty `width` x `height` board"
        d = {pos: (0, 0) for pos in product(range(width), range(height))}
        return Board(d)

    @staticmethod
    def new_rounded_rectangle(width, height, radius=1):
        """-> board with the `radius` of corners,
        `radius` < `width` and `radius` < `height`"""
        radiuses = range(radius)
        excess = product(
            set(chain(radiuses, map(lambda i: width - 1 - i, radiuses))),
            set(chain(radiuses, map(lambda i: height - 1 - i, radiuses))))
        return Board.new_rectangle(width, height) - excess

    def __sub__(self, poss):
        poss = frozenset(poss)
        return self.filter_pos(lambda pos: pos not in poss)

    def copy(self):
        return Board(dict.copy(self))

    # is-predicates
    def is_empty_pos(self, pos):
        "-> whether the `pos` is empty"
        return self[pos][1] == 0

    # is-factories
    def pos_player_is(self, player):
        "-> function 'wherher the `player` owns the `pos`'"
        return lambda pos: self[pos][0] == player

    def pos_level_is(self, level):
        "-> function 'whether the `pos` level is `level`'"
        return lambda pos: self[pos][1] == level

    # filters
    def filter_pos(self, fpos):
        "-> sub-board if `fpos`(pos)"
        return Board({pos: cell for pos, cell in self.items() if fpos(pos)})

    def filter_cell(self, fcell):
        "-> sub-board if `fcell`(cell)"
        return Board({pos: cell for pos, cell in self.items() if fcell(cell)})

    # board parts (subboards)
    def empty_part(self):
        "-> sub-board with empty cells"
        return self.filter_cell(is_empty_cell)

    def nonempty_part(self):
        "-> sub-board with non-empty cells"
        return self.filter_cell(is_not_empty_cell)

    def player_part(self, player):
        "-> sub-board | cell owned by the `player`"
        return self.filter_cell(cell_player_is(player))

    def overflowed_part(self):
        "-> sub-board | cell level > 'N'"
        return self.filter_cell(lambda cell: cell[1] > N)

    def xlevel_part(self, level):
        "-> sub-board | cell level == `level`"
        return self.filter_cell(cell_level_is(level))

    # spawning
    def spawn(self, population):
        "spawn board-like dict `population` on the board (in place)"
        self.update(population)

    def spawn2(self, padding=1, level=N):
        "spawn 2 players on the board corners (in place)"
        max_x, min_x, max_y, min_y = self.corners
        poss = [
            (min_x + padding, min_y + padding),
            (max_x - padding, max_y - padding)
        ]
        population = {
            pos: (player, level) for player, pos in enumerate(poss, 1)}
        self.spawn(population)

    def spawn4(self, padding=1, level=N):
        "spawn 4 players on the board corners (in place)"
        max_x, min_x, max_y, min_y = self.corners
        max_x, min_x, max_y, min_y = (
            max_x - padding, min_x + padding,
            max_y - padding, min_y + padding
        )
        poss = product((max_x, min_x), (max_y, min_y))
        population = {
            pos: (player, level) for player, pos in enumerate(poss, 1)}
        self.spawn(population)

    # content properties
    @property
    def poss(self):
        "-> iterator of poss"
        return self.keys()

    @property
    def cells(self):
        "-> iterator of cells"
        return self.values()

    @property
    def players(self):
        "-> set of players"
        return set(map(itemgetter(0), filter(is_not_empty_cell, self.cells)))

    # player-related
    def player_alive(self, player):
        "-> whether the player have a cell (is 'alive')"
        return any(map(cell_player_is(player), self.cells))

    def player_poss(self, player):
        "-> iterator of player's positions"
        return filter(self.pos_player_is(player), self.poss)

    def player_population(self, player):
        "-> number of all player's cells"
        return len(self.player_part(player))

    def player_level(self, player):
        "-> summary level of all player's cells"
        return sum(map(itemgetter(1), self.player_part(player).cells))

    # poss
    @property
    def overflowed_poss(self):
        return self.overflowed_part().poss

    # size properties
    @property
    def max_x(self):
        return max(map(itemgetter(0), self))

    @property
    def min_x(self):
        return min(map(itemgetter(0), self))

    @property
    def max_y(self):
        return max(map(itemgetter(1), self))

    @property
    def min_y(self):
        return min(map(itemgetter(1), self))

    @property
    def corners(self):
        "-> max_x, min_x, max_y, min_y of board"
        max_x = max(map(itemgetter(0), self))
        min_x = min(map(itemgetter(0), self))
        max_y = max(map(itemgetter(1), self))
        min_y = min(map(itemgetter(1), self))
        return max_x, min_x, max_y, min_y

    @property
    def shift(self):
        "-> position of board _top-left_ relative to (0, 0)"
        return (-self.min_x, -self.min_y)

    @property
    def width(self):
        return self.max_x - self.min_x + 1

    @property
    def height(self):
        return self.max_y - self.min_y + 1

    @property
    def size(self):
        "-> (width, height) of the board"
        return (self.width, self.height)

    def left_top_shift(self, cell_size):
        """-> board centering Vec3 v:
        v + pos2vector(pos, cell_size) -- cell point;
        board center at (0, 0, z)"""
        max_x, min_x, max_y, min_y = self.corners
        left_top = pos2vector((max_x - min_x, max_y - min_y), cell_size)
        return -left_top / 2 + pos2vector((min_x, min_y), cell_size)

    # # board editing
    # board resizing
    def extend(self):
        "-> `board` with added top and bottom rows and left and right columns"
        board = self.copy()
        max_x, min_x, max_y, min_y = board.corners
        for x in range(min_x - 1, max_x + 2):
            board[(x, min_y - 1)] = (0, 0)
            board[(x, max_y + 1)] = (0, 0)
        for y in range(min_y, max_y + 1):
            board[(min_x - 1, y)] = (0, 0)
            board[(max_x + 1, y)] = (0, 0)
        return board

    def zero_row(self, y):
        "-> `board` with zeroed `y`-th row"
        board = self.copy()
        max_x, min_x, max_y, min_y = board.corners
        for x in range(min_x, max_x + 1):
            board[(x, y)] = (0, 0)
        return board

    def zero_column(self, x):
        "-> `board` with zeroed `x`-th column"
        board = self.copy()
        max_x, min_x, max_y, min_y = board.corners
        for y in range(min_y, max_y + 1):
            board[(x, y)] = (0, 0)
        return board

    def remove_row(self, y):
        "-> `board` without `y`-th row"
        board = self.copy()
        for pos in self.poss:
            if pos[1] == y:
                del board[pos]
        return board

    def remove_column(self, x):
        "-> `board` without `x`-th column"
        board = self.copy()
        for pos in self.poss:
            if pos[0] == x:
                del board[pos]
        return board

    def add_top_row(self):
        "-> `board` with added top zero-row"
        return self.zero_row(self.min_y - 1)

    def add_bottom_row(self):
        "-> `board` with added bottom zero-row"
        return self.zero_row(self.max_y + 1)

    def add_left_column(self):
        "-> `board` with added leftmost zero-column"
        return self.zero_column(self.min_x - 1)

    def add_right_column(self):
        "-> `board` with added rightmost zero-column"
        return self.zero_column(self.max_x + 1)

    def remove_top_row(self):
        "-> `board` without top row"
        return self.remove_row(self.min_y)

    def remove_bottom_row(self):
        "-> `board` without bottom row"
        return self.remove_row(self.max_y)

    def remove_left_column(self):
        "-> `board` without leftmost column"
        return self.remove_column(self.min_x)

    def remove_right_column(self):
        "-> `board` without rightmost column"
        return self.remove_column(self.max_x)

    def reduce(self):
        "-> `board` without top and bottom rows and left and right columns"
        board = self.copy()
        max_x, min_x, max_y, min_y = board.corners
        for pos, cell in self.items():
            if not (max_x > pos[0] > min_x) or not (max_y > pos[1] > min_y):
                del board[pos]
        return board

    # board content editing
    def increase_level(self, pos, amount=1, player=None):
        "add `amount` to the cell at the `pos`"
        p, level = self[pos]
        player = player or p
        self[pos] = (player, level + amount)

    def decrease_level(self, pos, amount=1):
        "subtract `amount` from the cell at the `pos`"
        p, level = self[pos]
        if level <= amount:
            self[pos] = (0, 0)
        else:
            self[pos] = (p, level - amount)

    def empty_cells(self, condition=lambda cell: True):
        "-> `board` with emptied every cell if `condition`(cell)"
        board = self.copy()
        for pos, cell in self.items():
            if condition(cell):
                board[pos] = (0, 0)
        return board

    def remove_all_cells(self):
        "-> {(0, 0), (0, 0)}"
        return Board({(0, 0): (0, 0)})

    def fill_cells(self):
        "-> `board` with filled all inner holes with empty cells"
        board = self.copy()
        max_x, min_x, max_y, min_y = board.corners
        for pos in product(range(min_x, max_x + 1), range(min_y, max_y + 1)):
            if pos not in board:
                board[pos] = (0, 0)
        return board

    def permute_players(self):
        "-> permuted `board` (keep cells, move players (colors only))"
        subboard = self.nonempty_part()
        players = list(subboard.players)
        new_players = players.copy()
        shuffle(new_players)
        players_table = dict(zip(players, new_players))
        board = self.copy()
        for pos, (player, level) in subboard.items():
            board[pos] = (players_table[player], level)
        return board

    def permute_checkers(self):
        "-> permuted `board` (keep cells, move checkers)"
        poss, cells = list(self.poss), list(self.cells)
        shuffle(poss)
        return Board({pos: cell for pos, cell in zip(poss, cells)})

    def permute_cells(self):
        "-> permuted `board` (move cells (with checkers))"
        cells = list(self.cells)
        n = len(self)
        max_x, min_x, max_y, min_y = self.corners
        all_poss = list(
            product(range(min_x, max_x + 1), range(min_y, max_y + 1)))
        poss = sample(all_poss, n)
        return Board({pos: cell for pos, cell in zip(poss, cells)})

    # strategy-related
    def chain_poss(self, pos):
        "-> set of pos in 'chain' (sequence of `N`-level checkers)"
        ch = set()
        if self[pos][1] < N:
            return ch
        else:
            ch.add(pos)
            cross = {
                p for p in safe_cross(self, pos)
                if self[p][1] == N and p not in ch}
            while cross:
                ch.update(cross)
                cross = set().union(*(
                    {
                        p for p in safe_cross(self, p0)
                        if self[p][1] == N and p not in ch}
                    for p0 in cross))
            return ch

    @property
    def chains(self):
        "-> set of frozenset 'chains' (sequence of `N`-level checkers)"
        chained = set()
        chains = set()
        for pos in self.xlevel_part(N):
            if pos not in chained:
                ch = frozenset(self.chain_poss(pos))
                chains.add(ch)
                chained.update(ch)
        return chains


# updating loosers
def collect_loosers(initial_board, board):
    "-> set of loosers: {<looser>, ...}"
    return initial_board.players - board.players


# board evolution
def make_turn(board, turn, player):
    "-> board after the `turn` of the `player`"
    board = board.copy()
    assert board[turn][0] == player, (
        "impossible turn {} on cell {}\n{}".format(
            turn, board[turn], repr(board)))
    board.increase_level(turn, player=player)
    overflowed = list(board.overflowed_poss)
    while len(overflowed) > 0:
        _board = board.copy()  # tmp, for right order
        for blast_pos in overflowed:  # level > N
            for pos in safe_cross(board, blast_pos):
                _board.increase_level(pos, player=player)
            _board.decrease_level(blast_pos, 4)
        board = _board  # update
        overflowed = list(board.overflowed_poss)
    return board


def make_turns(board, history):
    """initial_board, history -> final_board,
    history: [(player, (x, y)), ...]"""
    def next_board(b, tp):
        turn, player = tp
        return make_turn(board=b, turn=turn, player=player)
    return reduce(next_board, history, board.copy())


# # bot strategy purposed functions
def all_variants(board, deep, player, order):
    """start recursive lookup, similar to 'dynamic' cartesian product
    -> iterator of variants"""
    return multiply_variants(board, deep, player, order)


def multiply_variants(board, deep, player, order):
    """recursive lookup, similar to dynamic cartesian product
    -> iterator of variants"""
    board = board.copy()
    turns0, turns1 = tee(board.player_poss(player), 2)
    if deep == 0 or not list(turns0):
        return [board]
    next_player = shift_player(player, order, board)
    return chain.from_iterable(multiply_variants(
        make_turn(board, turn, player), deep - 1, next_player, order)
        for turn in turns1)


def value_turn(player, turn, board, order, value_func, deep=1):
    """-> 'value' of the `turn` for the the `player`,
    `value_func`(board) -> value"""
    variants = all_variants(
        make_turn(board, turn, player), len(order) - 1,
        shift_player(player, order, board), order)
    if deep == 1:
        variant = min(variants, key=value_func, default=None)
        if variant is None:
            return inf  # win
        return value_func(variant)
    elif deep > 1:
        return min((
            max((
                value_turn(
                    player, turn, board, order, deep=deep - 1,
                    value_func=value_func)
                for turn in board.player_poss(player)), default=0)
            for board in variants), default=inf)


# # misc
def board2str(board, none=MAP_STR_NONE, empty=MAP_STR_EMPTY, fill=MAP_STR_FILL):
    """str representation of the board"""
    def dimension(xi):
        return sorted(set(map(itemgetter(xi), board)))

    def new_str(pos):
        return (
            (
                empty if board.is_empty_pos(pos)
                else fill.format(*reversed(board[pos])))
            if pos in board else none)

    return '\n'.join(
        ''.join(new_str((x, y)) for x in dimension(0))
        for y in dimension(1)) + '\n'


def cross(pos):
    "-> list of 4-vicinity of the `pos`"
    x, y = pos
    return [(x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)]


def safe_cross(board, pos):
    "-> iterator of existing 4-vicinity of the `pos`"
    x, y = pos
    return filter(
        lambda pos: pos in board,
        ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)))

# pasted from panda3d-clonium/core.py
# TODO: update applications! 


# draw-related functions
def explode(board, player, order):
    board = board.copy()
    d = deque(order)
    # QUESTION: what is it?


def calculate_cell_size(board, min_size):
    return int(ceil(min_size/max(board.width, board.height))) - 1


def display_text(surface, text, pos, font, color):
    text = font.render(text, True, color)
    surface.blit(text, pos)


def draw_background(surface, board, cell_size, shift=(0, 0)):
    surface.fill(BOARD_BACKGROUND_COLOR)
    for pos in board:
        pygame.draw.rect(surface, BOARD_CELL_COLOR, expand4(
            cell_size, pos, shift, margin=1))


def draw_item(surface, pos, pair, items, cell_size, shift=(0, 0)):
    surface.blit(items[pair[1]][pair[0]], expand2(cell_size, pos, shift))


def draw_items(surface, board, items, cell_size, shift=(0, 0)):
    for pos, pair in board.nonempty_part().items():
        draw_item(surface, pos, pair, items, cell_size, shift)


def draw_new(surface, pos, cell_size, shift=(0, 0), margin=5):
    pygame.draw.rect(surface, BOARD_NEW_TURN_COLOR, expand4(
        cell_size, pos, shift, margin=margin))


def draw_news(surface, news, cell_size, shift=(0, 0)):
    for pos in news:
        draw_new(surface, pos, cell_size, shift)


def draw_selection(surface, pos, cell_size, shift=(0, 0), margin=5):
    pygame.draw.rect(surface, BOARD_SELECTION_COLOR, expand4(
        cell_size, pos, shift, margin=margin))


def draw_selections(surface, board, player, cell_size, shift=(0, 0), margin=5):
    for pos in board.player_poss(player):
        draw_selection(surface, pos, cell_size, shift, margin=margin)


def draw_stat(surface, font, player, order):
    printing_surface = font.render(
        "Player: {}, Order: {}".format(player, order), True, BOARD_STAT_COLOR)
    printing_rectangle = printing_surface.get_rect()
    printing_rectangle.center = BOARD_STAT_CENTER
    surface.blit(printing_surface, printing_rectangle)


def expand2(cell_size, pos, shift=(0, 0), margin=0):
    pos = pos[0] + shift[0], pos[1] + shift[1]
    return (
        int(round(cell_size*pos[0] + margin)),
        int(round(cell_size*pos[1] + margin)))


def expand4(cell_size, pos, shift=(0, 0), margin=0):
    pos = pos[0] + shift[0], pos[1] + shift[1]
    return (
        int(round(cell_size*pos[0] + margin)),
        int(round(cell_size*pos[1] + margin)),
        int(round(cell_size - 2*margin)),
        int(round(cell_size - 2*margin)))


def reduce2(cell_size, pos, backshift=(0, 0)):
    return (
        int(pos[0]/cell_size) - backshift[0],
        int(pos[1]/cell_size) - backshift[1])


# string representation
def player2str(player, bots):
    return "#{}: {} {}".format(player, bots[player] if player in bots else "player", "PC" if player in bots else "NPC")


def live_player2str(player, bots, n_clips, n_holes):
    return "1) {} ({}/{})".format(player2str(player, bots), n_clips, n_holes)


def dead_player2str(player, bots, i):
    return "{}) {}".format(i, player2str(player, bots))


def results2str(board, bots={}, loosers=[]):
    return (
        '\n'.join(
            live_player2str(
                player, bots,
                board.player_population(player), board.player_level(player))
            for player in board.players)
        + '\n' +
        '\n'.join(
            dead_player2str(player, bots, i)
            for i, player in enumerate(reversed(loosers), 2)))


def win2str():
    return "Winner(s) under 1)"


def draw2str():
    return "Draw"


def transformed_items(items, cell_size):
    return {
        i: [
            pygame.transform.smoothscale(image, (cell_size, cell_size))
            for image in L]
        for i, L in items.items()}


# save-load related functions
def load_font(name=None, size=None):
    name = name or CORE_FONT_NAME
    size = size or CORE_FONT_SIZE
    return pygame.font.Font(pygame.font.match_font(name), size)


def load_items():
    global items
    if items is None:
        items = {
            i: [
                pygame.image.load(preference.clip_filename(n=i, color_i=j))
                for j in range(len(CORE_COLORS))]
            for i in range(1, 6)}
    return items


def save_map(board, filename, full=False):
    if not full:
        filename = preference.map_filename(name=filename)
    with open(filename, 'wb') as file:
        pickle.dump(board, file)


# # decorated
# loaders
def loader(name):
    def decorator(func):
        loaders[name] = func
        return func
    return decorator


@loader('name2map')
def load_map(filename, full=False):
    if not full:
        filename = preference.map_filename(name=filename)
    with open(filename, 'rb') as file:
        return Board(pickle.load(file))


@loader('filename2map')
def loadf_map(filename):
    with open(filename, 'rb') as file:
        return Board(pickle.load(file))


@loader('state2game')
def load_state(filename=None):
    if filename is None:
        filename = preference.save_filename()
    with open(filename, mode='rb') as file:
        d = pickle.load(file)
    loosers = d.get('loosers', None)
    board = Board(d['board'])
    initial_board = Board(d['initial_board']) if 'initial_board' in d else None
    order = d.get('order', None)
    initial_order = d.get('initial_order', None)
    bots = d.get('bots', None)
    history = d.get('history', None)
    player = d.get('player', None)
    return dict(
        initial_board=initial_board, board=board,
        bots=bots, initial_order=initial_order, order=order,
        player=player, history=history, loosers=loosers)


@loader('preset2game')
def load_preset(filename=None, preserve_order=True):
    if filename is None:
        filename = preference.save_filename()
    with open(filename, mode='rb') as file:
        d = pickle.load(file)
    board = Board(d.get('initial_board', d['board']))
    order = d.get('initial_order', d.get('order', None))
    bots = d.get('bots', None)
    if preserve_order:
        return dict(board=board, bots=bots, order=order)
    else:
        return dict(board=board, bots=bots)


@loader('preset2map')
def extract_map(filename):
    with open(filename, mode='rb') as file:
        d = pickle.load(file)
        return Board(d.get('initial_board', d['board']))


@loader('state2map')
def construct_map(filename):
    with open(filename, mode='rb') as file:
        d = pickle.load(file)
    return Board(d['board'])


def clear_load(filename):
    with open(filename, mode='rb') as file:
        return pickle.load(file)


# conditions
def condition(name):
    def decorator(func):
        conditions[name] = func
        return func
    return decorator


@condition("save?")
def is_save(filename):
    return filename.endswith('.' + SAVE_EXTENSION)


@condition("map?")
def is_map(filename):
    return filename.endswith('.' + MAP_EXTENSION)


@condition("file?")
def is_file(filename):
    return '.' in filename


# bots' strategies
def strategy(name):
    def decorator(func):
        strategies[name] = func
        return func
    return decorator


def checkersX(player, poss, board, order, deep):
    "the best turn for max checkers (with the `deep`)"
    func = partial(Board.player_population, player=player)
    return max(poss, key=lambda pos: value_turn(
            player, pos, board, order, deep=deep, value_func=func))


def levelsX(player, poss, board, order, deep):
    "the best turn for max levels (with the `deep`)"
    func = partial(Board.player_level, player=player)
    return max(poss, key=lambda pos: value_turn(
        player, pos, board, order, deep=deep, value_func=func))


@strategy('checkers-1')
def checkers1(player, poss, board, order):
    return checkersX(player, poss, board, order, deep=1)


@strategy('checkers-2')
def checkers2(player, poss, board, order):
    return checkersX(player, poss, board, order, deep=2)


@strategy('checkers-3')
def checkers3(player, poss, board, order):
    return checkersX(player, poss, board, order, deep=3)


@strategy('levels-1')
def levels1(player, poss, board, order):
    return levelsX(player, poss, board, order, deep=1)


@strategy('levels-2')
def levels2(player, poss, board, order):
    return levelsX(player, poss, board, order, deep=2)


@strategy('levels-3')
def levels3(player, poss, board, order):
    return levelsX(player, poss, board, order, deep=3)


@strategy('random')
def chooser(player, poss, board=None, order=None):
    "random turn"
    return choice(list(poss))


# animations on >= 4
def animation(name):
    def decorator(func):
        animations[name] = func
        return func
    return decorator


@animation('linear_jump')
def ljump(self, pos):
    x, y = self.expand2(pos, self.shift)
    start_time = time()
    progress = -1
    while progress < 1:
        self.draw_background()
        self.draw_selections()
        for p in ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)):
            self.draw_selection(p)
        self.draw_items()
        self.draw_stat()
        # shift = 2*self.cell_size*(1 - cos(progress)) # shift [1; 0; 1] when progress [-1; 0; +1]
        shift = self.cell_size*abs(progress)
        width = height = int(round(shift))
        h_item = pygame.transform.smoothscale(self.items[1][self.turn], (width, self.cell_size))
        v_item = pygame.transform.smoothscale(self.items[1][self.turn], (self.cell_size, height))
        if progress < 0:
            self.blit(h_item, (x + self.cell_size - shift, y)) # right
            self.blit(h_item, (x, y)) # left
            self.blit(v_item, (x, y + self.cell_size - shift)) # bottom
            self.blit(v_item, (x, y)) # top
        else:
            self.blit(h_item, (x + self.cell_size, y)) # right
            self.blit(h_item, (x - shift, y)) # left
            self.blit(v_item, (x, y + self.cell_size)) # bottom
            self.blit(v_item, (x, y - shift)) # top
        self.update_all()
        self.clock.tick(GAME_FPS)
        progress = 1000*(time() - start_time)/GAME_BLAST_TIME - 1


@animation('jump')
def jump(self, pos):
    x, y = self.expand2(pos, self.shift)
    start_time = time()
    progress = -1
    while progress < 1:
        self.draw_background()
        self.draw_selections()
        for p in ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)):
            self.draw_selection(p)
        self.draw_items()
        self.draw_stat()
        shift = 2*self.cell_size*(1 - cos(progress)) # shift [1; 0; 1] when progress [-1; 0; +1]
        width = height = int(round(shift))
        h_item = pygame.transform.smoothscale(self.items[1][self.turn], (width, self.cell_size))
        v_item = pygame.transform.smoothscale(self.items[1][self.turn], (self.cell_size, height))
        if progress < 0:
            self.blit(h_item, (x + self.cell_size - shift, y)) # right
            self.blit(h_item, (x, y)) # left
            self.blit(v_item, (x, y + self.cell_size - shift)) # bottom
            self.blit(v_item, (x, y)) # top
        else:
            self.blit(h_item, (x + self.cell_size, y)) # right
            self.blit(h_item, (x - shift, y)) # left
            self.blit(v_item, (x, y + self.cell_size)) # bottom
            self.blit(v_item, (x, y - shift)) # top
        self.update_all()
        self.clock.tick(GAME_FPS)
        progress = 1000*(time() - start_time)/GAME_BLAST_TIME - 1


@animation('rotate')
def rotate(self, pos):
    x, y = self.expand2(pos, self.shift)
    start_time = time()
    progress = -1
    while progress < 1:
        self.draw_background()
        self.draw_selections()
        for p in ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)):
            self.draw_selection(p)
        self.draw_items()
        self.draw_stat()
        shift = self.cell_size*(1 + progress)/2
        # item = self.items[1][self.turn]
        item = pygame.transform.rotate(self.items[1][self.turn], GAME_TPS*(1 + progress)/2)
        self.blit(item, (x + shift, y)) # right
        self.blit(item, (x - shift, y)) # left
        self.blit(item, (x, y + shift)) # bottom
        self.blit(item, (x, y - shift)) # top
        self.update_all()
        self.clock.tick(GAME_FPS)
        progress = 1000*(time() - start_time)/GAME_BLAST_TIME - 1


formats = {} # fill with Format(...)
class Format(object):

    def __init__(self, name, ext_filter, ext_description, condition, map_loader=None, loader=None):
        self.name = name
        self.filter = ext_filter
        self.description = ext_description
        self.condition = condition
        self.map_loader = map_loader
        self.loader = map_loader if loader is None else loader
        formats[name] = self

    def load(self, filename):
        return self.loader(filename)

    def check(self, filename):
        return self.condition(filename)


# initialize formats
for name, f in request("formats").items():
    condition = conditions[f["condition"]]
    map_loader = None if "map_loader" not in f else loaders[f["map_loader"]]
    game_loader = None if "game_loader" not in f else loaders[f["game_loader"]]
    Format(
        name, f["filter"], f["description"],
        condition, map_loader, game_loader)
