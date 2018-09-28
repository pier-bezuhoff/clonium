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

explosive_animations = {} # filling with @explosive_animation


class Game(object):
    """analogue of Android BGC/Clonium game for PC"""

    items = core.load_items()

    def __init__(self, board, bots=None, order=None, player=None, surface=None, initial_board=None, initial_order=None, history=None, loosers=None):
        """
        `initial_board` = `board` = {(x, y): (owner index or -1, level), ...}
        `bots` = ?
        `order` = [1st player index...]
        `player` = player index of current player
        `history` = [(player index, (turn_x, turn_y))...]
        `loosers` = [1st looser index...]
        """
        self.board = board.copy()
        self.initial_board = board.copy() if initial_board is None else initial_board.copy()
        self.history = [] if history is None else history.copy()
        self.bots = [] if bots is None else bots.copy()
        if order is None:
            self.order = list(self.board.players)
            shuffle(self.order)
        else:
            self.order = order.copy()
        self.initial_order = self.order.copy() if initial_order is None else initial_order.copy()
        self.player = self.order[0] if player is None else player
        self.surface = surface
        self.loosers = [] if loosers is None else loosers
        self.end = len(self.board.players) <= 1

    def draw_background(self):
        core.draw_background(surface=self.surface, board=self.board, cell_size=self.cell_size, shift=self.shift)

    def draw_selection(self, pos, margin=5):
        core.draw_selection(surface=self.surface, pos=pos, cell_size=self.cell_size, margin=margin, shift=self.shift)

    def draw_selections(self, margin=5):
        core.draw_selections(surface=self.surface, board=self.board, player=self.player, cell_size=self.cell_size, margin=margin, shift=self.shift)

    def draw_news(self):
        core.draw_news(surface=self.surface, news=self.news, cell_size=self.cell_size, shift=self.shift)

    def draw_items(self):
        core.draw_items(surface=self.surface, board=self.board, items=self.items, cell_size=self.cell_size, shift=self.shift)

    def draw_stat(self):
        core.draw_stat(surface=self.surface, font=self.font, player=self.player, order=self.order)

    def _draw(self):
        self.draw_background()
        self.draw_selections()
        self.draw_news()
        self.draw_items()
        self.draw_stat()

    def draw(self):
        self._draw()
        pygame.display.update()

    def start(self):
        if request("core.autosave"):
            self.save_preset()
            self.save()
        # pygame
        pygame.init()
        self.font = core.load_font()
        self.width = self.height = max(request("game.width"), request("game.height"))
        if self.surface is None:
            self.surface = pygame.display.set_mode((self.width, self.height))
        self.cell_size = core.calculate_cell_size(min_size=min(self.width, self.height), board=self.board)
        self.items = core.transformed_items(items=Game.items, cell_size=self.cell_size)
        self.clock = pygame.time.Clock()
        pygame.display.set_caption('Clonium')
        pygame.display.set_icon(pygame.image.load(preference.game_icon()))
        self.news = set()
        self.shift = self.board.shift
        self.draw()

        while not self.end:
            self.next_turn()
        players = self.board.players
        if players:
            self.win_end()
        else:
            self.draw_end()
        # print(self.board)
        self.quit()

    def next_turn(self):
        for event in pygame.event.get():
            if event.type == QUIT or event.type == KEYUP and event.key in (K_ESCAPE,):
                self.quit()
        self.draw()
        # self.__display()
        poss = self.board.player_poss(self.player)
        if poss:
            self.news = set()
            pygame.time.delay(request("game.delay"))
            if self.player in self.bots:
                pos = self.bot_choice(poss)
            else:
                pos = self.player_choice(poss)
            self.news.add(pos)
            if request("core.autosave"):
                self.history.append((self.player, pos))
                self.save()
            self.board.increase_level(pos, player=self.player)
            wave = self.board[pos][1] > core.N
            # do delays between waves
            delay = False
            while wave:
                if delay:
                    pygame.time.delay(request("game.blast_time"))
                delay = True
                for pos in self.board.overflowed_poss:
                    self.explode(pos)
                wave = any(pair[1] > core.N for pair in self.board.values())
            for player in self.order:
                if not self.board.player_alive(player) and player not in self.loosers:
                    self.loosers.append(player)
                    self.order.remove(player)
        self.player = core.shift_player(self.player, self.order, self.board)
        self.end = len(self.board.players) <= 1

    def player_choice(self, poss):
        poss = tuple(poss)
        while True:
            for event in pygame.event.get():
                if event.type == QUIT or event.type == KEYUP and event.key in (K_ESCAPE,):
                    self.quit()
                elif event.type == MOUSEBUTTONUP and event.button == 1:
                    x, y = event.pos
                    x, y = int(x/self.cell_size), int(y/self.cell_size)
                    if (x, y) in poss:
                        return (x, y)
                    else:
                        continue
                elif event.type == KEYUP and event.key in (K_LEFT,) and len(self.history) > len(self.initial_order):
                    return self.undo()

    def bot_choice(self, poss):
        if poss:
            return core.strategies[self.bots[self.player]](
                board=self.board, order=self.order, player=self.player, poss=poss)
        else:
            return None

    def __player_choice(self, poss):
        print("{} can choose turn from {}".format(self.player, poss))
        print(self.board)
        turn = eval(input("{} choice: ".format(self.player)))
        while turn not in poss:
            print("wrong choice... ({})".format(turn))
            turn = eval(input("{} choice: ".format(self.player)))
        return turn

    def explode(self, pos, x=None):
        player = self.board[pos][0]
        self.board.decrease_level(pos, 4)
        explosive_animations[request("game.explosive_animation")](self, pos)
        for p in core.safe_cross(self.board, pos):
            self.board.increase_level(p, player=player)
            self.news.add(p)
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
            h_item = pygame.transform.smoothscale(self.items[1][self.player], (width, self.cell_size))
            v_item = pygame.transform.smoothscale(self.items[1][self.player], (self.cell_size, height))
            if progress < 0:
                self.surface.blit(h_item, (x + self.cell_size - shift, y)) # right
                self.surface.blit(h_item, (x, y)) # left
                self.surface.blit(v_item, (x, y + self.cell_size - shift)) # bottom
                self.surface.blit(v_item, (x, y)) # top
            else:
                self.surface.blit(h_item, (x + self.cell_size, y)) # right
                self.surface.blit(h_item, (x - shift, y)) # left
                self.surface.blit(v_item, (x, y + self.cell_size)) # bottom
                self.surface.blit(v_item, (x, y - shift)) # top
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
            h_item = pygame.transform.smoothscale(self.items[1][self.player], (width, self.cell_size))
            v_item = pygame.transform.smoothscale(self.items[1][self.player], (self.cell_size, height))
            if progress < 0:
                self.surface.blit(h_item, (x + self.cell_size - shift, y)) # right
                self.surface.blit(h_item, (x, y)) # left
                self.surface.blit(v_item, (x, y + self.cell_size - shift)) # bottom
                self.surface.blit(v_item, (x, y)) # top
            else:
                self.surface.blit(h_item, (x + self.cell_size, y)) # right
                self.surface.blit(h_item, (x - shift, y)) # left
                self.surface.blit(v_item, (x, y + self.cell_size)) # bottom
                self.surface.blit(v_item, (x, y - shift)) # top
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
            # item = self.items[1][self.player]
            item = pygame.transform.rotate(self.items[1][self.player], request("game.tps")*(1 + progress)/2)
            self.surface.blit(item, (x + shift, y)) # right
            self.surface.blit(item, (x - shift, y)) # left
            self.surface.blit(item, (x, y + shift)) # bottom
            self.surface.blit(item, (x, y - shift)) # top
            pygame.display.update()
            self.clock.tick(request("game.fps"))
            progress = 1000*(time() - start_time)/request("game.blast_time") - 1

    def undo(self):
        # BUG
        player, turn = self.history.pop(-1)
        while player != self.player:
            player, turn = self.history.pop(-1)
        self.board, self.player = core.make_turns(
            self.initial_board, self.history)
        self.order = [player for player in self.initial_order if player in self.board.players]
        if request('core.autosave'):
            self.save()
        self.draw()
        poss = self.board.player_poss(self.player)
        return self.player_choice(poss)

    def quit(self):
        self.print_results()
        if request('core.autosave'):
            self.save()
        pygame.quit()
        sys_exit()

    def save_preset(self, filename=None):
        if filename is None:
            filename = preference.save_filename()
        with open(filename, 'wb') as file:
            pickle.dump({
                'initial_board': self.initial_board,
                'initial_order': self.initial_order,
                'bots': self.bots,
            }, file)

    def save(self, filename=None):
        if filename is None:
            filename = preference.save_filename()
        with open(filename, mode='rb') as file:
            d = pickle.load(file)
        with open(filename, mode='wb') as file:
            d['board'] = self.board
            d['order'] = self.order
            d['player'] = self.player
            d['history'] = self.history
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
        core.display_text(surface=self.surface, text=text, pos=pos, font=self.font, color=color)
