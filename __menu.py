import tkinter as tk
from tkinter import filedialog
from sys import exit as sys_exit

import settings
import game

class Menu(object):

	def __init__(self, game=None):
		self.game = game

		self.root = tk.Tk()
		# self.root.bind('<Destroy>', self.close)
		# self.root.bind('<Escape>', self.close)
		self.root.wm_title('Menu')
		self.menu = tk.Menu(self.root)
		self.root.config(menu=self.menu)

		self.file_menu = tk.Menu(self.menu)
		self.menu.add_cascade(label='File', menu=self.file_menu)
		self.file_menu.add_command(label='New game', command=self.new_game)
		self.file_menu.add_command(label='Open...', command=self.open)
		self.file_menu.add_command(label='Open last', command=self.open_last)
		self.file_menu.add_command(label='Save', command=self.save)
		self.file_menu.add_command(label='Save...', command=self.save_as)
		self.file_menu.add_separator()
		self.file_menu.add_command(label='Map editor', command=self.to_map_editor)
		self.file_menu.add_command(label='Close menu', command=self.close)
		self.file_menu.add_command(label='Quit', command=self.quit)

		self.edit_menu = tk.Menu(self.menu)
		self.menu.add_cascade(label='Edit', menu=self.edit_menu)
		self.edit_menu.add_command(label='Undo', command=self.undo)
		self.edit_menu.add_command(label='Redo', command=self.redo)
		self.edit_menu.add_command(label='Show history', command=self.show_history)
		self.file_menu.add_separator()
		self.edit_menu.add_command(label='Preferences', command=self.show_preferences)

		self.bots_menu = tk.Menu(self.menu)
		self.menu.add_cascade(label='Bots', menu=self.bots_menu)
		# for i in self.game.bots:
		# 	self.bots_menu.add_command(label='{}: {}'.format(i, 'bot' if i in bots else 'human'),
		# 		command=lambda: self.show_player_settings(i))

		self.help_menu = tk.Menu(self.menu)
		self.menu.add_cascade(label='Help', menu=self.help_menu)
		self.help_menu.add_command(label='Rules', command=self.show_rules)

		self.root.mainloop()

		# self.game.start()

	def update(self):
		# clean self.bots_menu
		...

	def undo(self):
		...

	def redo(self):
		...

	def show_preferences(self):
		master = tk.Toplevel()
		master.bind('<Escape>', master.destroy)
		master.wm_title('Preferences')
		tk.Button(master, text='button', command=lambda: print('clicked'))

	def show_history(self):
		history = ['#1: e2-e4'] # tmp
		master = tk.Toplevel()
		master.bind('<Escape>', master.destroy)
		master.wm_title('History')
		for i, turn in enumerate(history):
			b = tk.Button(master, text=turn, command=lambda: self.return_to(i))

	def show_rules(self):
		master = tk.Toplevel()
		master.bind('<Escape>', master.destroy)
		master.wm_title('Rules')
		text = Text(master)
		scroll = Scrollbar(master, command=text.yview)
		text.configure(yscrollcommand=scroll.set)
		rules = """
		Rules of **Clonium**:
		* Click on clip and it will grow
		* When a clip grows more than 4 it explode on 4 free neighboring cells and its owner capture them
		* To win you should capture all clips"""
		# text.tag_configure("colored", foreground='#476042', font=('Tempus Sans ITC', 9, 'bold'))
		# with open(RULES) as file:
		# 	rules = file.read()
		text.insert(tk.END, rules)
		text.pack(side=tk.LEFT)
		scroll.pack(side=tk.RIGHT, fill=tk.Y)

	def new_game(self):
		filename = filedialog.askopenfilename().split('/')[-1].split('.')[0]
		board = game.load_map(filename)
		self.game = game.Game(board=board)

	def return_to(self):
		...

	def open(self):
		...

	def open_last(self):
		...

	def save(self):
		...

	def save_as(self):
		...

	def to_map_editor(self):
		...

	def close(self):
		self.root.destroy()

	def quit(self):
		self.close()
		sys_exit()