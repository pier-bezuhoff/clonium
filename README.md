# Clonium
PC analogue of [Android Clonium](http://4pda.ru/forum/lofiversion/index.php?t632925.html) game (from scratch).
<br>
![android-clonium](https://user-images.githubusercontent.com/30413024/45918854-87a5e180-be95-11e8-93e1-2e844d27f841.jpeg)
<br>
Dependencies: [python3](https://www.python.org/downloads/), [pygame](https://www.pygame.org/).

[**Rules** at wiki](https://github.com/pier-bezuhoff/clonium/wiki/Rules-of-Clonium)

# Strength of bots
Bots are much tougher than in Android Clonium.
I can win _holes2_ and _clip2_ on rather small boards, the larger the harder, lose to _holes3_ and _clips3_.
In general, _holesN_ is stronger than _clipsN_.

# Progress
- [x] Standard clonium rules.
- [x] Create game with custom map, players and bots' strategies.
- [x] Human vs Human, Human vs Bot and Bot vs Bot modes (with any number of players).
- [x] Bots' strategies (_holesN_: maximizing overall level, _clipsN_: maximizing number of checkers and _random_).
- [x] Different depths of strategy (_N_ in _holesN_ and _clipsN_).
- [x] Create, edit and save maps in Map Editor.
- [x] Autosave initial board and history of turns on quit.
- [x] Preview of board when loading game or map.
- [x] Highlight current player checkers.
- [x] Highlight last turn (deltas).
- [x] Editable settings in "settings.json".
- [ ] Undo turn (bug).
- [ ] Back to main menu on win/defeat.
- [ ] Online stat.
- [ ] "Edit" and "Create" buttons on "New game" screen.
- [ ] Optimize strategies (especially _clips3_ and _holes3_ and more).
- [ ] Add other strategies.
- [ ] Better GUI.
- [ ] Compile and check on Windows.
