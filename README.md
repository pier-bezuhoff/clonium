# Clonium
PC analogue of [Android Clonium](http://4pda.ru/forum/lofiversion/index.php?t632925.html) game (from scratch).
<br>
![android-clonium](https://user-images.githubusercontent.com/30413024/45918854-87a5e180-be95-11e8-93e1-2e844d27f841.jpeg)
<br>
Dependencies: [python3](https://www.python.org/downloads/), [panda3d](https://www.panda3d.org/).

[**Rules** at wiki](https://github.com/pier-bezuhoff/clonium/wiki/Rules-of-Clonium)

# Progress
- [x] Standard clonium rules.
- [ ] Create game with custom map, players and bots' strategies.
- [ ] Human vs Human, Human vs Bot and Bot vs Bot modes (with any number of players).
- [x] Bots' strategies (_holesN_: maximizing overall level, _clipsN_: maximizing number of checkers and _random_).
- [x] Different depths of strategy (_N_ in _holesN_ and _clipsN_).
- [ ] Create, edit and save maps in Map Editor.
- [ ] Autosave initial board and history of turns on quit.
- [ ] Preview of board when loading game or map.
- [x] Highlight current player checkers.
- [x] Highlight last turn (deltas).
- [x] Editable settings in "settings.json".
- [x] Undo turn.
- [ ] Back to main menu on win/defeat.
- [ ] Online stat.
- [ ] Optimize strategies (especially _clips3_ and _holes3_ and more).
- [ ] Add other strategies.
- [ ] Better GUI.
- [ ] Compile and check on Windows.
