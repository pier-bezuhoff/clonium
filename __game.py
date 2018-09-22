
import math
import time
import pygame

import pgu_gui as gui
import pgu_timer as timer

import core
import preference
from preference import request
from widgets import init_td_style

td_style = request("core.style")
theme = gui.Theme(preference.theme())

class DrawingArea(gui.Widget):
	def __init__(self, width, height):
		gui.Widget.__init__(self, width=width, height=height)
		self.surface = pygame.Surface((width, height))

	def paint(self, surface):
		surface.blit(self.surface, (0, 0))

	def save_background(self):
		"""take a snapshot and blit it"""
		display = pygame.display.get_surface()
		self.surface.blit(display, self.get_abs_rect())

class TestDialog(gui.Dialog):
	def __init__(self):
		title = gui.Label("Some Dialog Box")
		label = gui.Label("Close this window to resume.")
		gui.Dialog.__init__(self, title, label)

class Game(object):
	"""analogue of Android BGC/Clonium game for PC"""

	def __init__(self, board, bots=None, N=3, order=None, turn=None, initial_board=None, history=None, loosers=None, name=None):
		self.AUTOSAVE = request("core.autosave")
		self.DELAY = request("game.delay")
		self.EXPLOSIVE_ANIMATION = request("game.explosive_animation")
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
		self.loosers = [] if loosers is None else loosers
		self.news = set() # recently changed cells
		self.end = False
		self.state = "loaded"

	def update(self):
		if self.state == "loaded":
			self.start()
			self.draw()
			self.state == "started"
		elif self.state == "started":
			self.next_turn()

	def event(self, event):
		if self.state == "choosing" and event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			self.pos = core.reduce2(self.cell_size, event.pos, self.shift)
			if self.pos in poss:
				self.state = "choosed"
		elif event.type == pygame.KEYUP and event.key in (pygame.K_LEFT,) and len(self.history) > len(self.order):
			print("undo")
			# self.undo()

	def start(self):
		# define self.surface
		if self.AUTOSAVE:
			self.save_state()
		# while not self.end:
		# 	self.next_turn()
		# players = self.players()
		# if players:
		# 	self.win_end()
		# else:
		# 	self.draw_end()
		# self.quit()

	def draw_background(self):
		core.draw_background(surface=self.surface, board=self.board, cell_size=self.cell_size, shift=self.shift)

	def draw_selection(self, pos, margin=5):
		core.draw_selection(surface=self.surface, pos=pos, cell_size=self.cell_size, margin=margin, shift=self.shift)

	def draw_selections(self, margin=5):
		core.draw_selections(surface=self.surface, board=self.board, player=self.turn, cell_size=self.cell_size, margin=margin, shift=self.shift)

	def draw_news(self):
		core.draw_news(surface=self.surface, news=self.news, cell_size=self.cell_size, shift=self.shift)

	def draw_items(self):
		core.draw_items(surface=self.surface, board=self.board, items=self.items, cell_size=self.cell_size, shift=self.shift)

	def draw_stat(self):
		core.draw_stat(surface=self.surface, font=self.font, player=self.turn, order=self.order)

	def blit(self, image, pos):
		self.surface.blit(image, pos)

	def draw(self):
		self.draw_background()
		self.draw_selections()
		self.draw_news()
		self.draw_items()
		self.draw_stat()

	def players(self):
		return core.map_players(self.board)

	def before_turn(self):
		self.state = "turning"
		self.poss = {pos for pos in self.board if self.board[pos][0] == self.turn}
		if self.poss:
			self.news = set()
			if self.turn in self.bots:
				self.state = "calculating"
				self.pos = self.bot_choice(self.poss)
			else:
				self.state = "choosing"
		else:
			self.skip_player()

	def after_turn(self, pos):
		self.news.add(pos)
		if self.AUTOSAVE:
			self.history.append((self.turn, pos))
			self.save_history()
		self.board[pos] = (self.turn, self.board[pos][1] + 1)
		wave = self.board[pos][1] > self.N
		delay = False
		while wave:
			# if delay:
			# 	pygame.time.delay(self.DELAY)
			delay = True
			current_board = self.board.copy()
			# for pos in current_board:
			# 	if current_board[pos][1] > self.N:
			# 		self.explode(pos)
			wave = any(pair[1] > self.N for pair in self.board.values())
		for pos, pair in self.board.items():
			if pair[1] == 0 and pair[0] != 0:
				self.board[pos] = (0, 0)
		for player in self.order:
			if len([0 for pair in self.board.values() if pair[0] == player]) == 0 and player not in self.loosers:
				self.loosers.append(player)
		self.turn = core.shift_player(self.turn, self.order)
		self.end = len(self.players()) <= 1
		self.draw()

	def skip_player(self):
		self.turn = core.shift_player(self.turn, self.order)

	def next_turn(self):
		# check events
		self.draw()
		poss = {pos for pos in self.board if self.board[pos][0] == self.turn}
		if poss:
			self.news = set()
			pygame.time.delay(self.DELAY) # for seeing previous turn
			if self.turn in self.bots:
				pos = self.bot_choice(poss)
			else:
				pos = self.player_choice(poss)
			self.news.add(pos)
			if self.AUTOSAVE:
				self.history.append((self.turn, pos))
				self.save_history()
			self.board[pos] = (self.turn, self.board[pos][1] + 1)
			wave = self.board[pos][1] > self.N
			delay = False
			while wave:
				if delay:
					pygame.time.delay(self.DELAY)
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
		...
		# if poss:
		# 	check events
		# 	on click:
		# 		pos = core.reduce2(self.cell_size, event.pos, self.shift)
		# 		if pos in poss:
		# 			return pos
		# 	on left arrow:
		# 		return self.undo()
		# else:
		# 	return None

	def bot_choice(self, poss):
		if poss:
			return core.strategies[self.bots[self.turn]](board=self.board, order=self.order, player=self.turn, poss=poss)
		else:
			return None

	def explode(self, pos):
		i, x = self.board[pos]
		self.board[pos] = (i, x - 4)
		if self.board[pos][1] == 0:
			self.board[pos] = (0, 0)
			self.news.remove(pos)
		x, y = pos
		core.animations[self.EXPLOSIVE_ANIMATION](self, pos)
		for pos in ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)):
			if pos in self.board:
				x = self.board[pos][1]
				self.board[pos] = (i, x + 1)
				self.news.add(pos)
		self.draw()

	def win_end(self):
		s = 'Winner(s) under 1)'
		print(s)

	def draw_end(self):
		s = "Draw"
		print(s)

	def quit(self):
		self.last_save()
		self.print_results()

	def print_results(self):
		print(core.str_results(self.board, self.bots, self.loosers))

	def expand4(self, pos, shift=(0, 0), margin=0):
		return core.expand4(self.cell_size, pos=pos, shift=shift, margin=margin)

	def expand2(self, pos, shift=(0, 0), margin=0):
		return core.expand2(self.cell_size, pos=pos, shift=shift, margin=margin)

	def last_save(self):
		core.last_save(self.loosers)

	def save_state(self):
		core.save_state(self.initial_board, self.order, self.bots, self.turn, self.N)

	def save_history(self):
		core.save_history(self.history, self.loosers)

class MainGui(gui.Desktop):
	height = 600
	area = None
	menu = None
	game = None
	# The game engine
	engine = None

	def __init__(self, display):
		gui.Desktop.__init__(self, theme=theme)

		# Setup the 'game' area where the action takes place
		self.area = DrawingArea(display.get_width(), self.height)
		# Setup the gui area
		self.menu = gui.Container(height=display.get_height() - self.height)

		table = gui.Table(height=display.get_height())
		table.tr()
		table.td(self.area)
		table.tr()
		table.td(self.menu)

		self.setup_menu()

		self.init(table, display)

	def setup_menu(self):

		table = gui.Table(vpadding=5, hpadding=2)
		init_td_style(table)
		table.tr()

		dialog = TestDialog()

		def dialog_cb():
			dialog.open()

		button = gui.Button("Modal dialog", height=50)
		button.connect(gui.CLICK, dialog_cb)
		table.td(button)

		# Add a button for pausing / resuming the game clock
		def pause_cb():
			if (self.engine.clock.paused):
				self.engine.resume()
			else:
				self.engine.pause()

		button = gui.Button("Pause/resume clock", height=50)
		button.connect(gui.CLICK, pause_cb)
		table.td(button)

		# Add a slider for adjusting the game clock speed
		table2 = gui.Table()
		init_td_style(table2)

		timeLabel = gui.Label("Clock speed")

		table2.tr()
		table2.td(timeLabel)

		slider = gui.HSlider(value=23, min=0, max=100, size=20, height=16, width=120)

		def update_speed():
			self.engine.clock.set_speed(slider.value/10.0)

		slider.connect(gui.CHANGE, update_speed)

		table2.tr()
		table2.td(slider)

		table.td(table2)

		self.menu.add(table, 0, 0)

	def open(self, dialog, pos=None):
		# Gray out the game area before showing the popup
		rect = self.area.get_abs_rect()
		dark = pygame.Surface(rect.size).convert_alpha()
		dark.fill((0, 0, 0, 150))
		pygame.display.get_surface().blit(dark, rect)
		# Save whatever has been rendered to the 'game area' so we can
		# render it as a static image while the dialog is open.
		self.area.save_background()
		# Pause the gameplay while the dialog is visible
		running = not(self.engine.clock.paused)
		self.engine.pause()
		gui.Desktop.open(self, dialog, pos)
		while (dialog.is_open()):
			for event in pygame.event.get():
				self.event(event)
			rects = self.update()
			if (rects):
				pygame.display.update(rects)
		if (running):
			# Resume gameplay
			self.engine.resume()

	def get_render_area(self):
		return self.area.get_abs_rect()


class GameEngine(object):
	def __init__(self, display, game):
		self.display = display
		self.square = pygame.Surface((400, 400)).convert_alpha()
		self.square.fill((255, 0, 0))
		self.game = game
		self.game.surface = pygame.Surface((400, 400)).convert_alpha()
		self.app = MainGui(self.display)
		self.app.engine = self
		
	# Pause the game clock
	def pause(self):
		self.clock.pause()

	# Resume the game clock
	def resume(self):
		self.clock.resume()

	# def render(self, dest, rect):
	# 	# Draw a rotating square
	# 	angle = self.clock.get_time()*10
	# 	surface = pygame.transform.rotozoom(self.square, angle, 1)
	# 	r = surface.get_rect()
	# 	r.center = rect.center
	# 	dest.fill((0, 0, 0), rect)
	# 	self.display.blit(surface, r)

	# 	def draw_clock(name, pt, radius, col, angle):
	# 		pygame.draw.circle(dest, col, pt, radius)
	# 		pygame.draw.line(dest, (0, 0, 0), pt, 
	# 						 (pt[0]+radius*math.cos(angle),
	# 						  pt[1]+radius*math.sin(angle)), 2)
	# 		tmp = self.font.render(name, True, (255, 255, 255))
	# 		dest.blit(tmp, (pt[0]-radius, pt[1]+radius+5))

	# 	# Draw the real time clock
	# 	angle = self.clock.get_real_time()*2*math.pi/10.0
	# 	draw_clock("Real time", (30, 30), 25, (255, 200, 100), angle)

	# 	# Now draw the game clock
	# 	angle = self.clock.get_time()*2*math.pi/10.0
	# 	draw_clock("Game time", (90, 30), 25, (255, 100, 255), angle)

	# 	return (rect, )

	def run(self):
		self.app.update()
		pygame.display.flip()

		self.font = pygame.font.SysFont("", 16)

		self.clock = timer.Clock()
		done = False
		while not done:
			# Process events
			for event in pygame.event.get():
				if (event.type == pygame.QUIT or 
					event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
					done = True
					# Pass the event off to pgu
				self.app.event(event)
				self.game.event(event)
			self.game.update()
			# Render the game
			rect = self.app.get_render_area()
			updates = []
			self.display.set_clip(rect)
			# L = self.game.get_render_area()
			# if (L):
			# 	updates += L
			self.display.set_clip()

			# Cap it at 30fps
			self.clock.tick(30)

			# Give pgu a chance to update the display
			L = self.app.update()
			if (L):
				updates += L
			pygame.display.update(updates)
			pygame.time.wait(10)

def start_game(game):
	display = pygame.display.set_mode((800, 700))
	engine = GameEngine(display, game)
	pygame.display.set_caption(request("game.name"))
	pygame.display.set_icon(pygame.image.load(preference.game_icon()))
	engine.run()

def main():
	start_game(Game(board=core.rectangle_board(3, 4), bots=['clips1', 'holes1', 'random', 'random']))

if __name__ == '__main__':
	main()