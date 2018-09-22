# Clonium
PC analogue of [Android Clonium](http://4pda.ru/forum/lofiversion/index.php?t632925.html) game (from scratch).
<br>
![android-clonium](https://user-images.githubusercontent.com/30413024/45918854-87a5e180-be95-11e8-93e1-2e844d27f841.jpeg)
<br>
Dependencies: [python3](https://www.python.org/downloads/), [pygame](https://www.pygame.org/).

# Rules
There are different clips/checkers on the board.
Checker has number of holes (level) and color (marks its owner).
Each player has own set of checkers and could increase level of one of them in his turn.
When level of checker reaches 3, after next level-up it explodes in four directions:
<br>
![3-checker](https://user-images.githubusercontent.com/30413024/45918549-50353600-be91-11e8-988e-805f9ab06f37.png)
![3-checker-explosion](https://user-images.githubusercontent.com/30413024/45918562-7bb82080-be91-11e8-9722-672dfb946048.png)
<br>
When checker explodes on other checkers, levels are summarized and new checkers get color (and owner) of exploded one.
<br>
Victory: capture all checkers.

# Progress
...
