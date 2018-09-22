#!/usr/bin/env python3

# python imports
import sys
import traceback
# from time import time

# panda3d imports
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    Vec3, VBase4, LRotation,
    CollisionTraverser, CollisionHandlerQueue, CollisionRay, CollisionNode,
    BitMask32,
    TextNode,
    DirectionalLight,
    TextureStage,
    WindowProperties
)
from direct.task.Task import Task
from direct.interval.MetaInterval import Sequence, Parallel
from direct.interval.FunctionInterval import FunctionInterval
from direct.gui.OnscreenText import OnscreenText

# game imports
import core
from preference import (
    request, request_vector, request_color, request_colors
)
from main_menu import MainMenu

LIGHT_COLOR = VBase4(2.0, 1.5, 2.0, 1)
LIGHT_DIRECTION = Vec3(10, 45, -60)

BEFORE_QUIT_TIME = 1.0  # tmp
BEFORE_TASK_TIME = 0.01  # tmp


class App(ShowBase):

    def __init__(self):
        ShowBase.__init__(self, windowType='none')
        self.startTk()
        # self.title = OnscreenText(
        #     text="Panda3D: Clonium",
        #     parent=self.a2dTopCenter, scale=0.07,
        #     align=TextNode.ACenter, pos=(0, -0.1),
        #     fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.5))
        self.setProperties()
        self.initialActions()

    def setProperties(self):
        # info = self.pipe.getDisplayInformation()
        # for i in range(info.getTotalDisplayModes()):
        #     print(info.getDisplayModeWidth(i), info.getDisplayModeHeight(i))
        self.tkRoot.update()
        self.tkRoot.title(request("display.title"))
        screen_width, screen_height = self.tkRoot.winfo_screenwidth(), self.tkRoot.winfo_screenheight()
        # pad = 0
        # self.tkRoot.geometry(
        #     "{}x{}+0+0".format(screen_width - pad, screen_height - pad))
        id = self.tkRoot.winfo_id()
        width, height = self.tkRoot.winfo_width(), self.tkRoot.winfo_height()
        prop = WindowProperties()
        prop.setParentWindow(id)
        prop.setOrigin(0, 0)
        prop.setSize(width, height)
        self.makeDefaultPipe()
        self.openDefaultWindow(props=prop)
        # width, height = request("display.resolution")
        # prop.setSize(
        #     width or info.getDisplayModeWidth(0),
        #     height or info.getDisplayModeHeight(0))
        # prop.setFullscreen(request("display.fullscreen"))
        # self.win.requestProperties(prop)

    def initialActions(self):
        self.accept('quit', self.quit)
        self.tkRoot.protocol("WM_DELETE_WINDOW", self.quit)
        self.accept('start_game', self.startGame)

    def startGame(self, board, bots=None, order=None):
        self.loadModels(board, bots, order)
        self.setupCollisions()
        self.setupLights()
        self.perspectiveView()
        self.disableMouse()
        self.setupActions()
        self.updateState()

    # loadings

    def loadModels(self, board, bots=None, order=None):
        self.loadTextures()
        # game
        self.board = board
        self.bots = bots or {}
        self.order = order if order is not None else list(self.board.players)
        self.player = self.order[0]
        # game process
        self.state = "start"
        self.initial_board = self.board.copy()
        self.initial_order = self.order.copy()
        # TODO: save board & order -> file
        self.history = []
        self.loosers = []
        self.end = False
        # board
        # TODO: remove 'magic numbers'
        self.cell_size = 1.0 / max(
            self.board.width,
            self.board.height)
        self.outline_size = 0.45 * self.cell_size
        self.shift = self.board.left_top_shift(self.cell_size)

        # scene
        self.addScene()
        # places == dummy cells
        self.places = {}
        self.lowered_places = {}
        self.raised_places = {}
        self.addPlaces()
        # cells
        self.cells = {}
        self.brightened_cell = None
        self.lightened_cells = {}
        self.darkened_cell = None
        self.addCells()
        # checkers
        self.checkers = {}
        self.checker_height = 0.01
        self.addCheckers()

    def loadTextures(self):
        self.textures = {}
        self.textures['cell'] = self.loader.loadTexture('textures/cell.png')
        self.textures['checker'] = {
            level:
                # self.loader.loadTexture('textures/checker-{}.png'.format(level))
                self.loader.loadTexture('textures/checker.png')
            for level in range(1, 10)
        }
        self.cell_ts = TextureStage('cell_stage')
        self.checker_ts = TextureStage('checker_stage')

    # creating & updating nodes

    # [scene]
    # creation
    def addScene(self):
        self.scene = self.render.attachNewNode('scene')
        self.scene.reparentTo(self.render)

    # [places]
    # creation
    def addPlace(self, pos):
        place = self.scene.attachNewNode('place-{}'.format(pos))
        place.setPos(self.pos2vector(pos))
        self.places[pos] = place

    def addPlaces(self):
        for pos in self.board.fill_cells().extend():
            self.addPlace(pos)

    # animation
    def raisePlace(self, pos):
        if pos not in self.raised_places:
            place = self.places[pos]
            raising = core.smooth_height_interval(
                place,
                h=request("animation.place_motion_height") * self.cell_size,
                period=request("animation.place_motion_time"))
            place.setPythonTag('interval', raising)
            raising.start()
            self.raised_places[pos] = place

    def markPossibleTurns(self):
        poss = self.board.player_poss(self.player)
        for pos in poss:
            self.raisePlace(pos)
            self.lightenCell(pos)

    def lowerPlace(self, pos):
        if pos not in self.lowered_places:
            place = self.places[pos]
            lowering = core.smooth_height_interval(
                place,
                h=-request("animation.place_motion_height") * self.cell_size,
                period=request("animation.place_motion_time"))
            place.setPythonTag('interval', lowering)
            lowering.start()
            self.lowered_places[pos] = place

    def lowerPlaces(self, poss):
        for pos in poss:
            self.lowerPlace(pos)

    def retrievePlace(self, pos):
        place = self.places[pos]
        interval = place.getPythonTag('interval')
        if interval is not None and interval.isPlaying():
            interval.finish()
        place.setZ(0)
        # retrieving = core.smooth_height_interval(
        #     cell,
        #     h=0,
        #     period=request("animation.cell_motion_time"))
        # place.setPythonTag('interval', retrieving)
        # retrieving.start()

    def retrievePlaces(self):
        self.unlowerPlaces()
        self.unraisePlaces()

    def unlowerPlaces(self):
        for pos in self.lowered_places:
            self.retrievePlace(pos)
        self.lowered_places = {}

    def unraisePlaces(self):
        for pos in self.raised_places:
            self.retrievePlace(pos)
        self.raised_places = {}

    # [cells]
    # creation
    def addCell(self, pos):
        cell = self.loader.loadModel('models/cell')
        collision = cell.find('**/Collision')
        cell.reparentTo(self.places[pos])
        cell.setScale(self.outline_size)
        cell.setTexture(self.cell_ts, self.textures['cell'])
        collision.setPythonTag('board_pos', pos)
        collision.setPythonTag('name', 'cell')
        self.cells[pos] = cell

    def addCells(self):
        for pos in self.board.keys():
            self.addCell(pos)

    # colorizing
    def lightenCell(self, pos):
        cell = self.cells[pos]
        cell.setColorScale(request_color("board.lighten_color_scale"))
        self.lightened_cells[pos] = cell

    def unlightenCells(self):
        for cell in self.lightened_cells.values():
            cell.clearColorScale()
        self.lightened_cells = {}

    def brightenCell(self, pos):
        if self.brightened_cell is not None:
            self.brightened_cell.clearColorScale()
        cell = self.cells[pos]
        cell.setColorScale(request_color("board.brighten_color_scale"))
        self.brightened_cell = cell

    def darkenCell(self, pos):
        if self.darkened_cell is not None:
            self.darkened_cell.clearColorScale()
        cell = self.cells[pos]
        cell.setColorScale(
            request_color("board.darken_color_scale"))
        self.darkened_cell = cell

    # [checkers]
    # creation
    def newChecker(self, pos, cell):
        "-> checker at `pos` with `cell`"
        player, level = cell
        checker = self.loader.loadModel('models/checker-{}'.format(level))
        collision = checker.find('**/Collision')
        checker.reparentTo(self.places[pos])
        checker.setScale(self.outline_size)
        checker.setZ(self.checker_height)
        checker.setTexture(self.checker_ts, self.textures['checker'][level])
        checker.setColor(request_colors("board.colors")[player])
        collision.setPythonTag('board_pos', pos)
        collision.setPythonTag('name', 'checker')
        return checker

    def addChecker(self, pos, cell=None):
        if cell is None:
            cell = self.board[pos]
        self.checkers[pos] = self.newChecker(pos, cell)

    def addCheckers(self):
        for pos, cell in self.board.nonempty_part().items():
            self.addChecker(pos, cell)

    # destruction
    def removeChecker(self, pos):
        self.checkers[pos].removeNode()
        del self.checkers[pos]

    def removeCheckers(self):
        for pos in list(self.checkers.keys()):
            # NOTE: `self.checkers` mutates here
            self.removeChecker(pos)

    # updating
    def updateChecker(self, pos):
        if pos in self.checkers:
            self.removeChecker(pos)
        if not self.board.is_empty_pos(pos):
            self.addChecker(pos, self.board[pos])

    def updateCheckers(self):
        self.removeCheckers()
        self.addCheckers()

    # animation
    def makeCheckerBlasting(self, checker, blast_pos, pos):
        "-> blasting interval for `checker`"
        start = self.diff2vector(pos, blast_pos, z=self.checker_height)
        end = Vec3(0, 0, self.checker_height)
        flight = core.jumping_interval(
            checker, start, end,
            request("animation.blast_height") * self.cell_size,
            request("animation.blast_time"))
        return flight

    def makeCheckerFalling(self, checker):
        "-> `checker` falling interval from its position"
        falling = core.falling_interval(
            checker,
            -request("animation.falling_height") * self.cell_size,
            request("animation.falling_time"))
        return falling

    # setups

    def setupCollisions(self):
        self.selector = CollisionTraverser()
        self.selector_queue = CollisionHandlerQueue()
        self.mouse_node = CollisionNode('mouseRay')
        self.mouse_node.setFromCollideMask(BitMask32.bit(0))
        self.selector_ray = CollisionRay()
        self.mouse_node.addSolid(self.selector_ray)
        self.selector.addCollider(
            self.camera.attachNewNode(self.mouse_node),
            self.selector_queue)
        # self.selector.showCollisions(self.scene)

    def setupLights(self):
        self.setBackgroundColor(0, 0, 0, 1)
        # TODO: add shades
        light = DirectionalLight('light')
        light.setColor(LIGHT_COLOR)
        light.setDirection(LIGHT_DIRECTION)
        light.setShadowCaster(True)
        lightNP = self.scene.attachNewNode(light)
        self.scene.setLight(lightNP)
        self.scene.setShaderAuto()

    def setupActions(self):
        self.taskMgr.setupTaskChain('game', 0)
        self.taskMgr.setupTaskChain('bot', 1)

        self.ignore('start_game')
        self.accept('escape', self.gameOver)
        self.accept('mouse1-up', self.leftClick)
        self.accept('space', self.pause)
        self.accept('tab', self.toggleView)
        self.accept('arrow_left', self.arrowLeftPressed)
        self.accept('arrow_right', self.arrowRightPressed)
        self.accept('arrow_down', self.arrowDownPressed)
        self.taskMgr.add(self.gameLoop, 'game.loop', taskChain='game')

    # tasks

    def pause(self):
        # set 'game' and 'bot' task chains' time to 0
        self.accept('space', self.resume)

    def resume(self):
        # resume 'game' and 'bot' task chains' time
        self.accept('space', self.pause)

    def gameLoop(self, task):
        if self.end:
            self.taskMgr.doMethodLater(
                BEFORE_QUIT_TIME,
                lambda _: self.gameOver(),
                'game.over',
                taskChain='game')
            return Task.done
        return Task.cont

    # mouse & keyboard handlers
    def leftClick(self):
        if self.mouseWatcherNode.hasMouse():
            mouse_point = self.mouseWatcherNode.getMouse()
            self.selector_ray.setFromLens(
                self.camNode, mouse_point.getX(), mouse_point.getY())
            self.selector.traverse(self.scene)
            if self.selector_queue.getNumEntries() > 0:
                self.selector_queue.sortEntries()
                selected = self.selector_queue.getEntry(0).getIntoNode()
                pos = selected.getPythonTag('board_pos')
                name = selected.getPythonTag('name')
                if pos in self.board:
                    self.brightenCell(pos)
                    if (name == 'checker' and
                            self.board[pos][0] == self.player and
                            self.state == "turn?"):
                        self.makeTurn(pos)

    def arrowLeftPressed(self):
        self.rotateCamera(90)

    def arrowRightPressed(self):
        self.rotateCamera(-90)

    def arrowDownPressed(self):
        self.undoTurn()

    # performing turn

    def makeTurn(self, pos):
        "update `self.history` and `self.checkers` with the turn"
        self.unlightenCells()
        self.retrievePlaces()
        self.history.append((self.player, pos))
        # update saved history
        self.darkenCell(pos)
        self.turn = pos
        self.state = "turn"
        self.applying_turn = self.applyTurn()
        next(self.applying_turn)

    def applyTurn(self):
        "self-sustaining generator, display blasts"
        self.board.increase_level(self.turn)
        self.lowerPlace(self.turn)
        overflowed = list(self.board.overflowed_poss)
        while len(overflowed) > 0:
            board = self.board.copy()  # tmp, for right order
            self.blasting_poss = {}
            for blast_pos in overflowed:
                self.blasting_poss[blast_pos] = []
                for pos in core.cross(blast_pos):
                    if pos in self.board:
                        board.increase_level(pos, player=self.player)
                    self.blasting_poss[blast_pos].append(pos)
                board.decrease_level(blast_pos, 4)
            # pause itself
            self.pauseApplying()
            yield None
            self.board = board  # update
            self.blast()
            # waiting blasts
            yield None
            # self.updateCheckers()
            overflowed = list(board.overflowed_poss)
        self.updateCheckers()
        self.player = self.nextPlayer()
        self.updateState()
        yield None

    def pauseApplying(self):
        "resume `self.applyTurn()` after a while"
        self.taskMgr.doMethodLater(
            request("animation.delay_before_blast"),
            lambda _: next(self.applying_turn),
            'game.applyingTurn',
            taskChain='game')

    def blast(self):
        "start blasting intervals"
        cell = (self.player, 1)
        blasts = Parallel(name='blasts')
        out_blasts = Parallel(name='blasts out')
        self.blasted_poss = set()
        for blast_pos, poss in self.blasting_poss.items():
            self.updateChecker(blast_pos)
            self.lowerPlace(blast_pos)
            for pos in poss:
                checker = self.newChecker(pos, cell)
                blast = self.makeCheckerBlasting(checker, blast_pos, pos)
                death = FunctionInterval(checker.removeNode)
                if pos in self.board:
                    self.lowerPlace(pos)
                    life = Sequence(blast, death)
                    blasts.append(life)
                    self.blasted_poss.add(pos)
                else:
                    falling = self.makeCheckerFalling(checker)
                    life = Sequence(blast, falling, death)
                    out_blasts.append(life)
        blast_end = FunctionInterval(self.afterBlast)
        blast_wave = Sequence(blasts, blast_end, name='blast wave')
        Parallel(blast_wave, out_blasts).start()

    def afterBlast(self):
        "update blasted checkers and resume `self.applying_turn`"
        for pos in self.blasted_poss:
            self.updateChecker(pos)
        # resume `self.applyTurn()` after a while
        self.taskMgr.doMethodLater(
            BEFORE_TASK_TIME,
            lambda _: next(self.applying_turn),
            'game.applyingTurn',
            taskChain='game')

    def nextPlayer(self):
        "update `self.loosers` and return next player"
        for looser in set(self.order) - self.board.players:
            self.removePlayer(looser)
        return core.next_player(self.player, self.order)

    def updateState(self, resumed=False):
        """update `self.state`, `self.end`;
        start `self.botTurn()` if `self.state == "think"`"""
        self.end = len(self.order) <= 1
        if not self.end:
            self.markPossibleTurns()
            if self.player in self.bots:
                self.state = "think"
                self.botTurn()
            else:
                self.state = "turn?"
        elif resumed:
            self.state = "turn?"
            if self.player in self.bots:
                self.player = self.loosers[-1]
            self.end = False

    def removePlayer(self, player):
        "remove `player` when (s)he is 'dead'"
        self.loosers.append(player)
        self.order.remove(player)

    def undoTurn(self):
        "undo 'round' with `self.history`"
        if (len(self.history) >= len(self.initial_order) and self.state == "turn?"):
            self.retrievePlaces()
            player, turn = self.history.pop(-1)
            while player != self.player:
                player, turn = self.history.pop(-1)
            self.board = core.make_turns(self.initial_board, self.history)
            self.order = core.updated_order(self.initial_order, self.board)
            # self.player = inv
            loosers_set = core.collect_loosers(self.initial_board, self.board)
            self.loosers = [
                looser for looser in self.loosers if looser in loosers_set]

            self.updateCheckers()
            self.brightenCell(turn)
            if self.history:
                self.darkenCell(self.history[-1][1])

    def botTurn(self):
        "start `self.botCalculation`"
        self.taskMgr.add(
            self.botCalculation, 'bot.calculation', taskChain='bot')

    def botCalculation(self, task):
        "start calculating bot's turn"
        # start_time = time()
        try:
            pos = core.strategies[self.bots[self.player]](
                player=self.player,
                poss=self.board.player_poss(self.player),
                board=self.board,
                order=self.order)
            self.state = "found"
            self.taskMgr.doMethodLater(
                BEFORE_TASK_TIME, self.makeTurn, 'game.makeBotTurn',
                extraArgs=[pos],
                taskChain='game')
        except Exception as e:
            traceback.print_exc()
            self.quit()
        finally:
            # elapsed_time = time() - start_time
            # print("found in {}s".format(elapsed_time))
            return Task.done

    # camera

    def rotateCamera(self, angle=90):
        "rotate camera on `angle` (in degrees) around 'up' (Oz)"
        if self.perspective:
            rotation = LRotation(Vec3.up(), angle)  # unit quaternion
            pos = rotation.xform(self.camera.getPos())
            self.camera.setPos(pos)
            self.camera.lookAt(request_vector("board.camera_target"))
        else:
            self.camera.setR(self.camera, -angle)

    def toggleView(self):
        if self.perspective:
            self.floatView()
        else:
            self.perspectiveView()

    def floatView(self):
        self.perspective = False
        self.camera.setPos(0, 0, 2.0)  # TODO: proper height
        self.camera.lookAt(request_vector("board.camera_target"))

    def perspectiveView(self):
        self.perspective = True
        self.camera.setPos(request_vector("board.camera_pos"))
        self.camera.lookAt(request_vector("board.camera_target"))

    # endings

    def gameOver(self):
        "ignore actions, remove tasks and `self.scene`, show results"
        self.ignoreAll()
        self.initialActions()
        self.taskMgr.removeTasksMatching('bot.*')
        self.taskMgr.removeTasksMatching('game.*')
        # show results
        self.acceptOnce('restart_game', self.restartGame)
        self.acceptOnce('resume_game', self.resumeGame)
        self.acceptOnce('end_game', self.endGame)
        self.messenger.send(
            'show_results',
            sentArgs=[self.board, self.order, self.loosers, self.bots])

    def resumeGame(self):
        self.setupActions()
        self.updateState(resumed=True)

    def restartGame(self):
        self.scene.removeNode()
        self.startGame(
            board=self.initial_board,
            bots=self.bots,
            order=self.initial_order)

    def endGame(self):
        self.scene.removeNode()

    def quit(self):
        # save all
        self.tkRoot.quit()
        sys.exit()

    def pos2vector(self, pos, z=0):
        return core.pos2vector(pos, self.cell_size, z=z) + self.shift

    def diff2vector(self, pos, pos0, z=0):
        return core.diff2vector(pos, pos0, self.cell_size, z=z)


def main():
    app = App()
    MainMenu(app.tkRoot).pack()
    app.run()


if __name__ == '__main__':
    main()
