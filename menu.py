from sys import exit as sys_exit

import pygame

import pgu_gui as gui

import preference
from preference import request
import game
import core
from widgets import NewGameDialog, RulesDialog, FileDialog, Preview
from map_editor import MapEditor

class Menu(object):

	theme = gui.Theme(preference.theme())

	def __init__(self):
		self.desktop = gui.Desktop(theme=self.theme)
		self.desktop.connect(gui.QUIT, self.close)

		self.table = gui.Table(width=request("main_menu.width"), height=request("main_menu.height"))
		self.table.tr()
		self.table.td(gui.Label("Menu"), colspan=4)
		self.table.tr()
		self.new_game_button = gui.Button("New game")
		self.new_game_button.connect(gui.CLICK, self.new_game)
		self.table.td(self.new_game_button)
		self.table.tr()
		self.load_last_button = gui.Button("Load")
		self.load_last_button.connect(gui.CLICK, self.load_game)
		self.table.td(self.load_last_button)
		self.table.tr()
		self.map_editor_button = gui.Button("Map editor")
		self.map_editor_button.connect(gui.CLICK, self.to_map_editor)
		self.table.td(self.map_editor_button)
		self.table.tr()
		self.rules_button = gui.Button("Rules")
		self.rules_button.connect(gui.CLICK, self.show_rules)
		self.table.td(self.rules_button)
		self.table.tr()
		self.quit_button = gui.Button("Quit")
		self.quit_button.connect(gui.CLICK, self.quit)
		self.table.td(self.quit_button)
		# self.menu = gui.Menus(menu_data)
		# self.table.td(self.menu, rowspan=10, colspan=10, columnspan=5)
		self.desktop.run(self.table)

	def show_preferences(self):
		...

	def load_game(self):
		dialog = FileDialog("Choose saved game", "Choose",
			path=request("paths.save_folder"),
			preview=Preview(display_players=False),
			exts=['state', 'history'])
		def on_change(dialog):
			filename = dialog.value
			loader = dialog.format.loader
			self.game = game.Game(**loader(filename))
			# self.game.open()
			self.game.start()
		dialog.connect(gui.CHANGE, on_change, dialog)
		dialog.open()

	def show_rules(self):
		RulesDialog().open()

	def new_game(self):
		dialog = NewGameDialog() # and filename to save with?
		def on_change(dialog):
			dialog.close()
			self.filename = dialog.filename
			self.game = game.Game(board=dialog.map, bots=dialog.bots) # GameWidget(board=dialog.map, bots=dialog.bots)
			# self.game.open()
			self.game.start()
		dialog.connect(gui.CHANGE, on_change, dialog)
		dialog.open(dialog)

	def to_map_editor(self):
		MapEditor().run()

	def close(self):
		self.desktop.quit()

	def quit(self):
		self.close()
		sys_exit()

def main():
	Menu()

if __name__ == '__main__':
	main()

		