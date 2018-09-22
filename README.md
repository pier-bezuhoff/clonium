# Clonium
PC analogue of android [Clonium](http://4pda.ru/forum/lofiversion/index.php?t632925.html) game.

Dependencies: python3, pygame.

# Rules:
There are different clips/checkers on the board.
Checker has number of holes (level) and color (marks its owner).
Each player has own set of checkers and could increase level of one of them in his turn.
When level of checker reaches 3, after next level-up it explodes in four directions:
<br>
![3-checker](https://user-images.githubusercontent.com/30413024/45918549-50353600-be91-11e8-988e-805f9ab06f37.png)
![3-checker-explosion](https://user-images.githubusercontent.com/30413024/45918562-7bb82080-be91-11e8-9722-672dfb946048.png)
<br>
When checker explodes on other checkers, levels are summarized and new checkers get color (and owner) of exploded one.
Victory: capture all checkers.

# Strength of bots
I can win _holes2_ and _clip2_ on rather small boards, the larger the harder, lose to _holes3_ and _clips3_.
In general, _holesN_ is stronger than _clipsN_.

# Progress
- [x] Standard clonium rules.
- [x] Create game with custom map, players and bots' strategies.
- [x] Human vs Human, Human vs Bot and Bot vs Bot modes (with any number of players).
- [x] Bots' strategies (_holesN_: maximizing overall level, _clipsN_: maximizing number of checkers and random).
- [x] Different depths of strategy (_N_ in _holesN_ and _clipsN_).
- [x] Create, edit and save maps in Map Editor.
- [x] Autosave initial board and history of turns on quit.
- [x] Preview of board when loading game or map.
- [x] Editable settings in "settings.json".
- [ ] Undo turn (bug).
- [ ] Back to main menu on win/defeat.
- [ ] "Edit" and "Create" buttons on "New game" screen.
- [ ] Optimize strategies (especially _clips3_ and _holes3_ and more).
- [ ] Add other strategies.
- [ ] Better GUI.
