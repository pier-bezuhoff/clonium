from random import shuffle, choice, sample
from itertools import product, chain, tee
from functools import reduce, partial
from operator import itemgetter
from math import sin, copysign, pi, inf
# import pickle

from panda3d.core import Vec3
from direct.interval.LerpInterval import LerpFunctionInterval, LerpPosInterval

# from preference import request

# <board> =
#   {<pos = (<x: int>, <y: int>)>:
#   <cell = (<player: int (>= 0)>, <level: int (>= 0)>)>}
N = 3  # max cell level
strategies = {}  # filling with @strategy('<name>')
animations = {}  # filling with @animation('<name>')


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
    next_board = (
        lambda b, turn_player: make_turn(
            b, turn_player[1], turn_player[0]))
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

# TODO: alpha-beta reducing, chains,
#       looking-glass, etc...


# # saves
def save_history(history):
    pass
    # with open(request("save.history_filename"), 'wb') as file:
    #     pickle.dump(history, file)


def save_board(board):
    pass
    # with open(request("save.board_filename"), 'wb') as file:
    #     pickle.dump(board, file)


def save_order(order):
    pass
    # with open(request("save.order_filename"), 'wb') as file:
    #     pickle.dump(order, file)


# # misc
def board2str(board, none=' ' * 6, empty='_' * 5 + '|', fill="{}x[{}]|"):
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


def pos2vector(pos, cell_size, z=0):
    "-> Vec3(...) == Vec3(Vec2(`pos`) * `cell_size`, `z`)"
    return Vec3(pos[0] * cell_size, pos[1] * cell_size, z)


def diff2vector(pos, pos0, cell_size, z=0):
    p = (pos0[0] - pos[0], pos0[1] - pos[1])
    return pos2vector(p, cell_size, z=z)


# # decorated
# bots' strategies
def strategy(name):
    "add bot strategy"
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


# animations
def animation(name):
    def decorator(func):
        animations[name] = func
        return func
    return decorator


def jumping_maker(obj, start, end, h, degree=360):
    """-> tragectory(t) function for LerpFunctionInterval:
    directed rotate (`degree`) and 'sinus' jump"""
    v = end - start
    p = -copysign(1, v.y) if abs(v.y) > abs(v.x) else 0
    r = copysign(1, v.x) if abs(v.y) <= abs(v.x) else 0

    def trajectory(t):
        obj.setHpr(
            Vec3(0, p, r) * (degree * t))
        obj.setPos(start + v * t + Vec3(
            0, 0, h * sin((0.99 * pi) * t)))  # T < `pi` => covering
    return trajectory


def jumping_interval(obj, start, end, h, period, degree=360):
    "-> LerpFunctionInterval: directed rotate (`degree`) and 'sinus' jump"
    return LerpFunctionInterval(
        jumping_maker(obj, start, end, h, degree),
        duration=period)


def falling_maker(obj, h, degree=720):
    """-> trajectory(t) function for LerpFunctionInterval:
    'h' rotate (`degree`) and falling (speed = const);
    negative `h` counts for takeoff"""
    start = obj.getPos()

    def trajectory(t):
        obj.setH(degree * t)
        obj.setPos(start + Vec3(0, 0, h * t))
    return trajectory


def falling_interval(obj, h, period, degree=720):
    """-> LerpFunctionInterval: 'h' rotate (`degree`) and falling (speed = const)
    negative `h` counts for takeoff"""
    return LerpFunctionInterval(
        falling_maker(obj, h, degree),
        duration=period)


def smooth_height_interval(obj, h, period):
    shift = Vec3(0, 0, h)
    end_pos = obj.getPos() + shift
    return LerpPosInterval(obj, period, end_pos)
