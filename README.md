# Clonium
PC analogue of android [Clonium](http://4pda.ru/forum/lofiversion/index.php?t632925.html) game.

Dependencies: python3, pygame.

# Rules:
There are different clips/checkers on the board.
Checker has number of holes (level) and color (marks its owner).
Each player has own set of checkers and could increase level of one of them in his turn.
When level of checker reaches 3 after next level-up it explodes in four direction:
![Level 3 checker](/home/vanfed/Pictures/screenshots/3-checker.png)

Each player has set of clips/checkers 

# Progress
- [x] Implemented standard clonium rules.
- [x] Creating, editing and saving maps in Map Editor.
- [x] Autosaving initial board and history of turns.
- [x] Editable settings in "settings.json".

- [ ] Undo.
- [ ] "Edit" and "Create" buttons on "New game" screen.
