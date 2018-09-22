from random import shuffle
from math import cos
from sys import exit as sys_exit
from time import time
import pickle
import pygame
from pygame.locals import QUIT, KEYUP, K_ESCAPE, MOUSEBUTTONUP, K_LEFT

import core
import preference
from preference import request

explosive_animations = {} # fill with @explosive_animation


class Game(object):
    """analogue of Android BGC/Clonium game for PC"""

    items = core.load_items()

    def __init__(self, board, bots=None, N=3, order=None, turn=None, surface=None, initial_board=None, history=None, loosers=None):
        """board = {(x:int, y:int): (player_index or -1, n), ...}"""
        self.N = N
        self.board = board.copy()
        self.initial_board = board.copy() if initial_board is None else initial_board.copy()
        self.history = [] if history is None else history.copy()
        self.bots = [] if bots is None else bots.copy()
        if order is None:
            self.order = list(core.map_players(self.board))
            shuffle(self.order)
        else:
            self.order = order.copy()
        self.turn = self.order[0] if turn is None else turn # index of turning player
        self.display = surface
        self.loosers = [] if loosers is None else loosers
        self.end = len(self.players()) <= 1

    def draw_background(self):
        core.draw_background(surface=self.display, board=self.board, cell_size=self.cell_size, shift=self.shift)

    def draw_selection(self, pos, margin=5):
        core.draw_selection(surface=self.display, pos=pos, cell_size=self.cell_size, margin=margin, shift=self.shift)

    def draw_selections(self, margin=5):
        core.draw_selections(surface=self.display, board=self.board, player=self.turn, cell_size=self.cell_size, margin=margin, shift=self.shift)

    def draw_news(self):
        core.draw_news(surface=self.display, news=self.news, cell_size=self.cell_size, shift=self.shift)

    def draw_items(self):
        core.draw_items(surface=self.display, board=self.board, items=self.items, cell_size=self.cell_size, shift=self.shift)

    def draw_stat(self):
        core.draw_stat(surface=self.display, font=self.font, player=self.turn, order=self.order)

    def _draw(self):
        self.draw_background()
        self.draw_selections()
        self.draw_news()
        self.draw_items()
        self.draw_stat()

    def draw(self):
        self._draw()
        pygame.display.update()

    def players(self):
        return core.map_players(self.board)

    def start(self):
        if request("core.autosave"):
            self.save_state()
        # pygame
        pygame.init()
        self.font = core.load_font()
        self.width = self.height = max(request("game.width"), request("game.height"))
        if self.display is None:
            self.display = pygame.display.set_mode((self.width, self.height))
        self.cell_size = core.calculate_cell_size(min_size=min(self.width, self.height), board=self.board)
        self.items = core.transformed_items(items=Game.items, cell_size=self.cell_size)
        self.clock = pygame.time.Clock()
        pygame.display.set_caption('Clonium')
        pygame.display.set_icon(pygame.image.load(preference.game_icon()))
        self.news = set()
        self.shift = core.shift(self.board)
        self.draw()

        while not self.end:
            self.next_turn()
        players = self.players()
        if players:
            self.win_end()
        else:
            self.draw_end()
        # core.print_map(self.board)
        self.quit()

    def next_turn(self):
        for event in pygame.event.get():
            if event.type == QUIT or event.type == KEYUP and event.key in (K_ESCAPE,):
                self.quit()
        self.draw()
        # self.__display()
        poss = {pos for pos in self.board if self.board[pos][0] == self.turn}
        if poss:
            self.news = set()
            pygame.time.delay(request("game.delay"))
            if self.turn in self.bots:
                pos = self.bot_choice(poss)
            else:
                pos = self.player_choice(poss)
            self.news.add(pos)
            if request("core.autosave"):
                self.history.append((self.turn, pos))
                self.save_history()
            self.board[pos] = (self.turn, self.board[pos][1] + 1)
            wave = self.board[pos][1] > self.N
            delay = False
            while wave:
                if delay:
                    pygame.time.delay(request("game.blast_time"))
                delay = True
                current_board = self.board.copy()
                for pos in current_board:
                    if current_board[pos][1] > self.N:
                        self.explode(pos)
                wave = any(pair[1] > self.N for pair in self.board.values())
            for pos, pair in self.board.items():
                if pair[1] == 0 and pair[0] != 0:
                    self.board[pos] = (0, 0)
            for player in self.order:
                if len([0 for pair in self.board.values() if pair[0] == player]) == 0 and player not in self.loosers:
                    self.loosers.append(player)
        self.turn = core.shift_player(self.turn, self.order)
        self.end = len(self.players()) <= 1

    def player_choice(self, poss):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT or event.type == KEYUP and event.key in (K_ESCAPE,):
                    self.quit()
                elif event.type == MOUSEBUTTONUP and event.button == 1:
                    x, y = event.pos
                    x, y = int(x/self.cell_size), int(y/self.cell_size)
                    if (x, y) in poss:
                        return (x, y)
                elif event.type == KEYUP and event.key in (K_LEFT,) and len(self.history) > len(self.order):
                    return self.undo()

    def bot_strategy(name):
        def decorator(func):
            bot_strategies[name] = func
            return func
        return decorator

    def bot_choice(self, poss):
        if poss:
            return core.strategies[self.bots[self.turn]](board=self.board, order=self.order, player=self.turn, poss=poss)
        else:
            return None

    def __player_choice(self, poss):
        print("{} can choose turn from {}".format(self.turn, poss))
        core.print_map(board=self.board)
        turn = eval(input("{} choice: ".format(self.turn)))
        while turn not in poss:
            print("wrong choice... ({})".format(turn))
            turn = eval(input("{} choice: ".format(self.turn)))
        return turn

    def explode(self, pos, x=None):
        i, x = self.board[pos]
        self.board[pos] = (i, x - 4)
        if self.board[pos][1] == 0:
            self.board[pos] = (0, 0)
            self.news.remove(pos)
        x, y = pos
        explosive_animations[request("game.explosive_animation")](self, pos)
        for pos in ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)):
            if pos in self.board:
                x = self.board[pos][1]
                self.board[pos] = (i, x + 1)
                self.news.add(pos)
        self.draw()

    def explosive_animation(name):
        def decorator(func):
            explosive_animations[name] = func
            return func
        return decorator

    @explosive_animation('linear_jump')
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
                self.display.blit(h_item, (x + self.cell_size - shift, y)) # right
                self.display.blit(h_item, (x, y)) # left
                self.display.blit(v_item, (x, y + self.cell_size - shift)) # bottom
                self.display.blit(v_item, (x, y)) # top
            else:
                self.display.blit(h_item, (x + self.cell_size, y)) # right
                self.display.blit(h_item, (x - shift, y)) # left
                self.display.blit(v_item, (x, y + self.cell_size)) # bottom
                self.display.blit(v_item, (x, y - shift)) # top
            pygame.display.update()
            self.clock.tick(request("game.fps"))
            progress = 1000*(time() - start_time)/request("game.blast_time") - 1

    @explosive_animation('jump')
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
                self.display.blit(h_item, (x + self.cell_size - shift, y)) # right
                self.display.blit(h_item, (x, y)) # left
                self.display.blit(v_item, (x, y + self.cell_size - shift)) # bottom
                self.display.blit(v_item, (x, y)) # top
            else:
                self.display.blit(h_item, (x + self.cell_size, y)) # right
                self.display.blit(h_item, (x - shift, y)) # left
                self.display.blit(v_item, (x, y + self.cell_size)) # bottom
                self.display.blit(v_item, (x, y - shift)) # top
            pygame.display.update()
            self.clock.tick(request("game.fps"))
            progress = 1000*(time() - start_time)/request("game.blast_time") - 1

    @explosive_animation('rotate')
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
            item = pygame.transform.rotate(self.items[1][self.turn], request("game.tps")*(1 + progress)/2)
            self.display.blit(item, (x + shift, y)) # right
            self.display.blit(item, (x - shift, y)) # left
            self.display.blit(item, (x, y + shift)) # bottom
            self.display.blit(item, (x, y - shift)) # top
            pygame.display.update()
            self.clock.tick(request("game.fps"))
            progress = 1000*(time() - start_time)/request("game.blast_time") - 1

    def undo(self):
        n = len(self.order)
        self.history = self.history[:-n]
        board, player = core.make_turns(self.initial_board, self.history, N=self.N)
        self.board = board
        self.turn = core.shift_player(player, self.order, shift=1)
        self.save_history()
        poss = {pos for pos in self.board if self.board[pos][0] == self.turn}
        self.draw()
        return self.player_choice(poss)

    def quit(self):
        self.print_results()
        self.save()
        pygame.quit()
        sys_exit()

    def save(self, filename=None): # ISSUE: save & load initial board and saved turns
        if filename is None:
            filename = preference.save_filename()
        with open(filename, mode='rb') as file:
            d = pickle.load(file)
        with open(filename, mode='wb') as file:
            d['loosers'] = self.loosers
            pickle.dump(d, file)

    def save_state(self, filename=None):
        if filename is None:
            filename = preference.save_filename()
        with open(filename, 'wb') as file:
            pickle.dump({'board': self.initial_board, 'order': self.order, 'bots': self.bots, 'turns': [], 'turn': self.turn, 'N': self.N}, file)

    def save_history(self, filename=None):
        if filename is None:
            filename = preference.save_filename()
        with open(filename, mode='rb') as file:
            d = pickle.load(file)
        with open(filename, mode='wb') as file:
            d['turns'] = self.history
            d['loosers'] = self.loosers
            pickle.dump(d, file)

    def win_end(self):
        print(core.win2str())

    def draw_end(self):
        print(core.draw2str())

    def print_results(self):
        print(core.results2str(self.board, self.bots, self.loosers))

    def expand4(self, pos, shift=(0, 0), margin=0):
        return core.expand4(self.cell_size, pos=pos, shift=shift, margin=margin)

    def expand2(self, pos, shift=(0, 0), margin=0):
        return core.expand2(self.cell_size, pos=pos, shift=shift, margin=margin)

    def display_text(self, text, pos=None, color=request("core.font.color")):
        if pos is None: pos = (self.width//2, self.height//2)
        core.display_text(surface=self.display, text=text, pos=pos, font=self.font, color=color)
