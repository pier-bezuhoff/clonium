# Clonium
PC analogue of [Android Clonium](http://4pda.ru/forum/lofiversion/index.php?t632925.html) game (from scratch).
<br>
![android-clonium](https://user-images.githubusercontent.com/30413024/45918854-87a5e180-be95-11e8-93e1-2e844d27f841.jpeg)
<br>
Dependencies: [python3](https://www.python.org/downloads/), [pygame](https://www.pygame.org/).

[**Rules** at wiki](https://github.com/pier-bezuhoff/clonium/wiki/Rules-of-Clonium)

# Strength of bots
Bots are much tougher than in Android Clonium.
I can win _levels2_ and _checkers2_ on rather small boards, the larger the harder, lose to _levels3_ and _checkers3_.
In general, _levelsN_ is stronger than _checkersN_.

# Progress
- [x] Standard clonium rules.
- [x] Create game with custom map, players and bots' strategies.
- [x] Human vs Human, Human vs Bot and Bot vs Bot modes (with any number of players).
- [x] Bots' strategies (_levelsN_: maximizing overall level, _checkersN_: maximizing number of checkers and _random_).
- [x] Different depths of strategy (_N_ in _levelsN_ and _checkersN_).
- [x] Create, edit and save maps in Map Editor.
- [x] Autosave initial board and history of turns on quit.
- [x] Preview of board when loading game or map.
- [x] Highlight current player checkers.
- [x] Highlight last turn (deltas).
- [x] Editable settings in "settings.json".
- [x] Undo turn.
- [ ] Back to main menu on win/defeat.
- [ ] Online stat.
- [ ] "Edit" and "Create" buttons on "New game" screen.
- [ ] Optimize strategies (especially _checkers3_ and _levels3_ and more).
- [ ] Add other strategies.
- [ ] Better GUI.
- [ ] Compile and check on Windows.
