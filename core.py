from random import shuffle, choice, sample
from math import cos, sin, ceil
from itertools import product, chain, tee, takewhile
from functools import reduce
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
STRF_MAP_NONE = request("strf_map.none")
STRF_MAP_EMPTY = request("strf_map.empty")
STRF_MAP_FILL = request("strf_map.fill")

loaders = {}
conditions = {}
strategies = {}
animations = {}
items = None

def loader(name):
    def decorator(func):
        loaders[name] = func
        return func
    return decorator

def condition(name):
    def decorator(func):
        conditions[name] = func
        return func
    return decorator

def strategy(name):
    def decorator(func):
        strategies[name] = func
        return func
    return decorator

# def __trace(board, n, after, order):
#   board = board.copy()
#   boards = []
#   for turn1 in turns(board, after):
#       b = after_turn(board, turn1, after)
#       i = shift_player(after, order)
#       for turn2 in turns(b, i):
#           b = after_turn(b, turn2, i)
#           i = shift_player(after, order)
#           for turn3 in turns(b, i):
#               ...
#               # turnN, where N == len(order) - 1
#   # TODO: create something like it.product instead of recursion in trace/get_variants

def explode(board, player, order):
    board = board.copy()
    d = deque(order)

def after_turn(board, turn, player, N=3): # TODO: make it better
    """return board after the turn of the player"""
    board = board.copy()
    assert board[turn][0] == player, "impossible turn {} on cell {}".format(turn, board[turn])
    board[turn] = board[turn][0], board[turn][1] + 1
    filtered = [pos for pos in board if board[pos][1] > N]
    while len(filtered) > 0:
        _board = board.copy()
        for (x, y) in filtered:
            for pos in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
                if pos in board:
                    _board[pos] = player, _board[pos][1] + 1
            _board[(x, y)] = player, _board[(x, y)][1] - 4
            if _board[(x, y)][1] == 0:
                _board[(x, y)] = (0, 0)
        board = _board
        filtered = [pos for pos in board if board[pos][1] > N]
    return board

def calculate_cell_size(board, min_size):
    return int(ceil(min_size/max(width(board), height(board)))) - 1

def make_turns(board, history, N): # BUG: when `undo` raise an `impossible turn` error from after_turn()
    """return final board and last player"""
    next_board = lambda b_, t_p: (after_turn(b_[0], t_p[0], t_p[1], N), t_p[1])
    return reduce(next_board, history, (board.copy(), 0))

def clips(board, i):
    return {pos: pair for pos, pair in board.items() if pair[0] == i}

def n_clips(board, player):
    return len([0 for pair in board.values() if pair[0] == player])

def n_holes(board, player):
    return sum(pair[1] for pair in board.values() if pair[0] == player)

def display_text(surface, text, pos, font, color):
    text = font.render(text, True, color)
    surface.blit(text, pos)

def draw_background(surface, board, cell_size, shift=(0, 0)):
    surface.fill(BOARD_BACKGROUND_COLOR)
    for pos in board:
        pygame.draw.rect(surface, BOARD_CELL_COLOR, expand4(cell_size, pos, shift, margin=1))

def draw_item(surface, pos, pair, items, cell_size, shift=(0, 0)):
    surface.blit(items[pair[1]][pair[0]], expand2(cell_size, pos, shift))

def draw_items(surface, board, items, cell_size, shift=(0, 0)):
    for pos, pair in board.items():
        if pair[1] != 0:
            draw_item(surface, pos, pair, items, cell_size, shift)

def draw_new(surface, pos, cell_size, shift=(0, 0), margin=5):
    pygame.draw.rect(surface, BOARD_NEW_TURN_COLOR, expand4(cell_size, pos, shift, margin=margin))

def draw_news(surface, news, cell_size, shift=(0, 0)):
    for pos in news:
        draw_new(surface, pos, cell_size, shift)

def draw_selection(surface, pos, cell_size, shift=(0, 0), margin=5):
    pygame.draw.rect(surface, BOARD_SELECTION_COLOR, expand4(cell_size, pos, shift, margin=margin))

def draw_selections(surface, board, player, cell_size, shift=(0, 0), margin=5):
    poss = {pos for pos in board if board[pos][0] == player}
    for pos in poss:
        draw_selection(surface, pos, cell_size, shift, margin=margin)
        
def draw_stat(surface, font, player, order):
    printing_surface = font.render("Player: {}, Order: {}".format(player, order), True, BOARD_STAT_COLOR)
    printing_rectangle = printing_surface.get_rect()
    printing_rectangle.center = BOARD_STAT_CENTER
    surface.blit(printing_surface, printing_rectangle)

def expand2(cell_size, pos, shift=(0, 0), margin=0):
    pos = pos[0] + shift[0], pos[1] + shift[1]
    return (int(round(cell_size*pos[0] + margin)), int(round(cell_size*pos[1] + margin)))

def expand4(cell_size, pos, shift=(0, 0), margin=0):
    pos = pos[0] + shift[0], pos[1] + shift[1]
    return (int(round(cell_size*pos[0] + margin)), int(round(cell_size*pos[1] + margin)),
        int(round(cell_size - 2*margin)), int(round(cell_size -2*margin)))

def reduce2(cell_size, pos, backshift=(0, 0)):
    return int(pos[0]/cell_size) - backshift[0], int(pos[1]/cell_size) - backshift[1]

def load_font(name=None, size=None):
    name = name or CORE_FONT_NAME
    size = size or CORE_FONT_SIZE
    return pygame.font.Font(pygame.font.match_font(name), size)

def load_items():
    global items
    if items is None:
        items = {i: [pygame.image.load(preference.clip_filename(n=i, color_i=j))
        for j in range(len(CORE_COLORS))] for i in range(1, 6)}
    return items

def map_players(board):
    return {pair[0] for pair in board.values() if pair[0] > 0}

def sizes(board):
    max_x = max(map(itemgetter(0), board))
    min_x = min(map(itemgetter(0), board))
    max_y = max(map(itemgetter(1), board))
    min_y = min(map(itemgetter(1), board))
    return max_x, min_x, max_y, min_y

def shift(board):
    s = sizes(board)
    return (-s[1], -s[3])

def width(board):
    return max(pos[0] for pos in board) - min(pos[0] for pos in board) + 1

def height(board):
    return max(pos[1] for pos in board) - min(pos[1] for pos in board) + 1

def size(board):
    return (width(board), height(board))

def corners(board):
    max_x = max(board, key=lambda pos: pos[0])
    min_x = min(board, key=lambda pos: pos[0])
    max_y = max(board, key=lambda pos: pos[1])
    min_y = min(board, key=lambda pos: pos[1])
    return max_x, min_x, max_y, min_y

def extend(board):
    board = board.copy()
    max_x, min_x, max_y, min_y = sizes(board)
    for x in range(min_x - 1, max_x + 2):
        board[(x, min_y - 1)] = (0, 0)
        board[(x, max_y + 1)] = (0, 0)
    for y in range(min_y, max_y + 1):
        board[(min_x - 1, y)] = (0, 0)
        board[(max_x + 1, y)] = (0, 0)
    return board

def add_top_row(board):
    board = board.copy()
    max_x, min_x, max_y, min_y = sizes(board)
    for x in range(min_x, max_x + 1):
        board[(x, min_y - 1)] = (0, 0)
    return board

def add_bottom_row(board):
    board = board.copy()
    max_x, min_x, max_y, min_y = sizes(board)
    for x in range(min_x, max_x + 1):
        board[(x, max_y + 1)] = (0, 0)
    return board

def add_left_column(board):
    board = board.copy()
    max_x, min_x, max_y, min_y = sizes(board)
    for y in range(min_y, max_y + 1):
        board[(min_x - 1, y)] = (0, 0)
    return board

def add_right_column(board):
    board = board.copy()
    max_x, min_x, max_y, min_y = sizes(board)
    for y in range(min_y, max_y + 1):
        board[(max_x + 1, y)] = (0, 0)
    return board

def remove_row(board, y):
    board = board.copy()
    for pos in board.copy().keys():
        if pos[1] == y:
            del board[pos]
    return board

def remove_top_row(board):
    return remove_row(board, sizes(board)[3])

def remove_bottom_row(board):
    return remove_row(board, sizes(board)[2])

def remove_column(board, x):
    board = board.copy()
    for pos in board.copy().keys():
        if pos[0] == x:
            del board[pos]
    return board

def remove_left_column(board):
    return remove_column(board, sizes(board)[0])

def remove_right_column(board):
    return remove_column(board, sizes(board)[1])

def reduce_(board):
    board = board.copy()
    max_x, min_x, max_y, min_y = sizes(board)
    for pos, cell in board.copy().items():
        if not (max_x > pos[0] > min_x) or not (max_y > pos[1] > min_y):
            del board[pos]
    return board

def remove_clips(board, condition=lambda cell: True):
    board = board.copy()
    for pos, cell in board.items():
        if condition(board[pos]):
            board[pos] = (0, 0)
    return board

def remove_cells(board):
    return {(0, 0): (0, 0)}

def add_cells(board):
    board = board.copy()
    max_x, min_x, max_y, min_y = sizes(board)
    for pos in product(range(min_x, max_x + 1), range(min_y, max_y + 1)):
        if pos not in board:
            board[pos] = (0, 0)
    return board

def add_clips(board, player, amount):
    board = board.copy()
    for pos, cell in board.items():
        if board[pos] == (0, 0):
            board[pos] = (player, amount)
    return board

def permute_clips(board):
    board = board.copy()
    poss, cells = list(board.keys()), list(board.values())
    shuffle(poss)
    board = {}
    for pos, cell in zip(poss, cells):
        board[pos] = cell
    return board

def permute_cells(board):
    board = board.copy()
    cells = list(board.values())
    n = len(board)
    max_x, min_x, max_y, min_y = sizes(board)
    board = {}
    p = product(range(min_x, max_x + 1), range(min_y, max_y + 1))
    L = list(p)
    poss = sample(L, n)
    for pos, cell in zip(poss, cells):
        board[pos] = cell
    return board

def have_turns(board, i):
    return any(map(lambda pos: board[pos][0] == i, board))

def shift_player(i, order, shift=1, check_exist=False, board=None, check_shift=1):
    if check_exist:
        d = deque(order)
        d.rotate(-order.index(i))
        d.popleft()
        exist = lambda i: any(map(lambda pos: board[pos][0] == i, board)) # borrowed from `have_turns` in sake of *performance*
        return list(takewhile(exist, d))[-1] # BUG: `IndexError: list index out of range` when a player has been near destroying
    else:
        return order[(order.index(i) + check_shift) % len(order)]

def print_map(board, none=' '*6, empty='_'*5 + '|', fill="{}x[{}]|"):
    print('\n' + map2str(board, none=none, empty=empty, fill=fill))

def rectangle_board(w, h, shift=1, N=3):
    empty_board = {pos for pos in product(range(w), range(h))}
    board = {pos: (0, 0) for pos in empty_board}
    board[(shift, shift)] = (1, N)
    board[(w - shift - 1, h - shift - 1)] = (2, N)
    return board

def reduced_square_board(n, shift=1, L=None, N=3):
    L = L or []
    board = square_board(n, shift, N)
    for pos in L:
        del board[pos]
    return board

def rounded_square_board(n, shift=1, delete=1, N=3):
    L = product(set([*range(delete), *[n - 1 - i for i in range(delete)]]), repeat=2)
    return reduced_square_board(n, shift, L, N)

def last_save(loosers, filename=None): # ISSUE: save & load initial board and saved turns
    if filename is None:
        filename = preference.save_filename()
    with open(filename, mode='rb') as file:
        d = pickle.load(file)
    with open(filename, mode='wb') as file:
        d['loosers'] = loosers
        pickle.dump(d, file)

def save_state(initial_board, order, bots, turn, N, filename=None):
    if filename is None:
        filename = preference.save_filename()
    with open(filename, 'wb') as file:
        pickle.dump({'board': initial_board, 'order': order, 'bots': bots, 'turns': [], 'turn': turn, 'N': N}, file)

def save_history(history, loosers, filename=None):
    if filename is None:
        filename = preference.save_filename()
    with open(filename, mode='rb') as file:
        d = pickle.load(file)
    with open(filename, mode='wb') as file:
        d['turns'] = history
        d['loosers'] = loosers
        pickle.dump(d, file)

def save_map(board, filename, full=False):
    if not full:
        filename = preference.map_filename(name=filename)
    with open(filename, 'wb') as file:
        pickle.dump(board, file)

def square_board(n, shift=1, N=3):
    empty_board = {pos for pos in product(range(n), repeat=2)}
    board = {pos: (0, 0) for pos in empty_board}
    board[(shift, shift)] = (1, N)
    board[(shift, n - shift - 1)] = (2, N)
    board[(n - shift - 1, shift)] = (3, N)
    board[(n - shift - 1, n - shift - 1)] = (4, N)
    return board

def player2str(player, bots):
    return "#{}: {} {}".format(player, bots[player] if player in bots else "player", "PC" if player in bots else "NPC")

def live_player2str(player, bots, n_clips, n_holes):
    return "1) {} ({}/{})".format(player2str(player, bots), n_clips, n_holes)

def dead_player2str(player, bots, i):
    return "{}) {}".format(i, player2str(player, bots))

def results2str(board, bots={}, loosers=[]):
    return ('\n'.join(live_player2str(player, bots, n_clips(board, player), n_holes(board, player))
        for player in map_players(board)) + '\n' +
    '\n'.join(dead_player2str(player, bots, i)
        for i, player in enumerate(reversed(loosers), 2)))

def win2str():
    return "Winner(s) under 1)"

def draw2str():
    return "Draw"

def map2str(board, none=STRF_MAP_NONE, empty=STRF_MAP_EMPTY, fill=STRF_MAP_FILL):
    """str representation of the board"""
    dimension = lambda xi: sorted(set(map(itemgetter(xi), board)))
    new_str = lambda x, y: ((empty if board[(x, y)][0] == 0
            else fill.format(*reversed(board[(x, y)])))
        if (x, y) in board else none)
    return '\n'.join(''.join(new_str(x, y) for x in dimension(0))
        for y in dimension(1)) + '\n'

def trace(board, n, after, order):
    """start recursion"""
    return get_variants(board, n, after, order)

def transformed_items(items, cell_size):
    return {i: [pygame.transform.smoothscale(image, (cell_size, cell_size)) for image in L] for i, L in items.items()}

def turns(board, i):
    """turns(board, player_i) --> iterator of possible player turns"""
    return filter(lambda pos: board[pos][0] == i, board)

def get_variants(board, n, after, order, tee=tee, turns=turns, shift_player=shift_player, len=len, list=list, chain_from_iterable=chain.from_iterable):
    """recursive"""
    board = board.copy()
    turns0, turns1 = tee(turns(board, after), 2)
    if n == 0 or len(list(turns0)) == 0:
        return [board]
    i = shift_player(after, order, check_exist=True, board=board)
    return chain_from_iterable(get_variants(after_turn(board, turn, after), n - 1, i, order) for turn in turns1)

def value_turn(i, turn, board, order, deep=1, value_func=None):
    """return value of the turn for the i-th player"""
    if value_func is None:
        value_func = lambda b: len([0 for pos in b if b[pos][0] == i])
    variants = trace(after_turn(board, turn, i), len(order) - 1, shift_player(i, order), order)
    if deep == 1:
        variant = min(variants, key=value_func, default=None)
        if variant is None:
            return 1e10 # win
        return value_func(variant)
    elif deep > 1:
        return min((max((value_turn(i, t, b, order, deep=deep - 1, value_func=value_func)
            for t in turns(b, i)), default=0) for b in variants), default=1e5)

def value_tuple_turn(i, turn, board, order, deep=1, value_func=None):
    """return value of the turn for the i-th player"""
    if value_func is None:
        value_func = lambda b: len([0 for pos in b if b[pos][0] == i])
    variants, sum_variants, n_variants = tee(trace(after_turn(board, turn, i), len(order) - 1, shift_player(i, order), order), 3)
    if deep == 1:
        variant = min(variants, key=value_func, default=None)
        length = len(list(n_variants))
        if length == 0:
            return (1e5, 0)
        average = sum([value_func(v) for v in sum_variants])/length
        if variant is None:
            return (1e5, 0) # win
        return (value_func(variant), average)
    elif deep > 1:
        return min((max((value_tuple_turn(i, t, b, order, deep=deep - 1, value_func=value_func) for t in turns(b, i)),
            default=(0, 0)) for b in variants), default=(1e5, 0))

## decorated
# loaders

@loader('name2map')
def load_map(filename, full=False):
    if not full:
        filename = preference.map_filename(name=filename)
    with open(filename, 'rb') as file:
        return pickle.load(file)

@loader('filename2map')
def loadf_map(filename):
    with open(filename, 'rb') as file:
        return pickle.load(file)

@loader('history2game')
def load_history(filename=None):
    if filename is None:
        filename = preference.history_filename()
    with open(filename, mode='rb') as file:
        d = pickle.load(file)
    loosers = d.get('loosers', None)
    board = d['board']
    order = d['order']
    bots = d['bots']
    turns = d['turns']
    N = d['N']
    p = d['turn']
    for player, turn in turns:
        assert p == player, "wrong turns order stored at '{}':\nplayer {} intead of {} (turn #{} {})".format(filename, player, p, turns.index((player, turn)), turn)
        board = after_turn(board, turn, player, N=N)
        p = shift_player(p, order)
        while n_clips(board, p) == 0:
            p = shift_player(p, order)
    return dict(board=board, bots=bots, N=N, order=order, turn=p, loosers=loosers)

@loader('state2game')
def load_state(filename=None, preserve_order=True):
    if filename is None:
        filename = preference.save_filename()
    with open(filename, mode='rb') as file:
        d = pickle.load(file)
    board = d['board']
    order = d['order']
    bots = d['bots']
    first_player = d['turn']
    N = d['N']
    if preserve_order:
        return dict(board=board, bots=bots, N=N, order=order, turn=first_player)
    else:
        return dict(board=board, bots=bots, N=N)

@loader('state2map')
def extract_map(filename):
    with open(filename, mode='rb') as file:
        return pickle.load(file)['board']

@loader('history2map')
def construct_map(filename):
    with open(filename, mode='rb') as file:
        d = pickle.load(file)
    board = d['board']
    order = d['order']
    bots = d['bots']
    turns = d['turns']
    N = d['N']
    p = d['turn']
    for player, turn in turns:
        assert p == player, "wrong turns order stored at '{}':\nplayer {} intead of {} (turn #{} {})".format(filename, player, p, turns.index((player, turn)), turn)
        board = after_turn(board, turn, player, N=N)
        p = shift_player(p, order)
        while n_clips(board, p) == 0:
            p = shift_player(p, order)
    return board

def clear_load(filename):
    with open(filename, mode='rb') as file:
        return pickle.load(file)

# conditions

@condition("?save")
def is_save(filename):
    return filename.endswith('.' + SAVE_EXTENSION)

@condition("?map")
def is_save(filename):
    return filename.endswith('.' + MAP_EXTENSION)

@condition("?file")
def is_save(filename):
    return '.' in filename

# bots' strategies

def clipsX(player, poss, board, order, n):
    return max(poss, key=lambda pos: value_turn(player, pos, board, order, deep=n))

def holesX(player, poss, board, order, n):
    func = lambda b, i=player: n_holes(b, i)
    return max(poss, key=lambda pos: value_turn(player, pos, board, order, deep=n, value_func=func))

@strategy('clips1')
def clips1(board, order, player, poss):
    return max(poss, key=lambda pos: value_turn(player, pos, board, order))

@strategy('clips2')
def clips2(player, poss, board, order):
    return max(poss, key=lambda pos: value_turn(player, pos, board, order, deep=2))

@strategy('holes1')
def holes1(player, poss, board, order):
    func = lambda b, i=player: n_holes(b, i)
    return max(poss, key=lambda pos: value_turn(player, pos, board, order, value_func=func))

@strategy('holes2')
def holes2(player, poss, board, order):
    func = lambda b, i=player: n_holes(b, i)
    return max(poss, key=lambda pos: value_turn(player, pos, board, order, deep=2, value_func=func))

@strategy('holes3')
def holes3(player, poss, board, order):
    func = lambda b, i=player: n_holes(b, i)
    return max(poss, key=lambda pos: value_turn(player, pos, board, order, deep=3, value_func=func))

@strategy('clips1+')
def clips1p(player, poss, board, order):
    return max(poss, key=lambda pos: value_tuple_turn(player, pos, board, order))

@strategy('clips2+')
def clips2p(player, poss, board, order):
    return max(poss, key=lambda pos: value_tuple_turn(player, pos, board, order, deep=2))

@strategy('holes1+')
def holes1p(player, poss, board, order):
    func = lambda b, i=player: n_holes(b, i)
    return max(poss, key=lambda pos: value_tuple_turn(player, pos, board, order, value_func=func))

@strategy('holes2+')
def holes2p(player, poss, board, order):
    func = lambda b, i=player: n_holes(b, i)
    return max(poss, key=lambda pos: value_tuple_turn(player, pos, board, order, deep=2, value_func=func))

@strategy('random')
def chooser(player, poss, board=None, order=None):
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
    Format(name, f["filter"], f["description"], condition, map_loader, game_loader)
