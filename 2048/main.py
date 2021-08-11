import pygame
pygame.init()
import random
import json
import copy

class InputBox:
    def __init__(self, game, x, y, width, height, color, font):
        self.game = game
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.font = font
        self.text = 0

    def handle_key(self, e):
        if e.key == pygame.K_BACKSPACE:
            if len(self.text)>0:
                self.text = self.text[:-1]
        else:
            self.text += e.unicode

    def draw(self):
        pygame.draw.rect(self.game.window, self.color, [self.x, self.y, self.width, self.height])
        pygame.draw.rect(self.game.window, (0, 0, 0), [self.x, self.y, self.width, self.height], width=4)
        t = self.font.render(self.text, True, (0, 0, 0)).convert_alpha()
        self.game.window.blit(t, (self.x+self.width/2-t.get_width()/2, self.y+self.height/2-t.get_height()/2))

class Tile:
    colors = {2: (236, 228, 220),
              4: (235, 224, 203),
              8: (232, 179, 129),
              16: (230, 155, 114),
              32: (229, 127, 99),
              64: (217, 99, 68),
              128: (230, 207, 130),
              256: (232, 204, 118),
              512: (230, 200, 107),
              1024: (225, 195, 104),
              2048: (226, 191, 98),
              4096: (60, 58, 51)}
    def __init__(self, gridX, gridY, value):
        self.x = gridX
        self.y = gridY
        self.value = value
        self.color = self.get_color(self.value)
        self.changedValue = False
        self.prevPos = (self.x, self.y)
        self.prevValue = self.value
        self.state = 1

    def get_color(self, value):
        if value in self.colors:
            return self.colors[value]
        else:
            return (230, 230, 230)

    def __repr__(self):
        return f"[Tile({self.x}, {self.y}) val:{self.value} state:{self.state}]"

    def move_until_hit(self, board, depth=1):
        if depth:
            self.state = 0
            self.prevPos = (self.x, self.y)
            self.prevValue = self.value

        self.changedValue = False
        self.x += board.direction[0]
        self.y += board.direction[1]
        while 0 <= self.x < board.width and 0 <= self.y < board.height:
            t = board.get_tiles_at(self.x, self.y)
            t.remove(self)
            if len(t) == 1:
                if t[0].handle_collision(board, self, depth):
                    self.state = -1
                    self.x += board.direction[0]
                    self.y += board.direction[1]
                break
            elif len(t) > 1:
                print("More than one tile colliding")
            self.x += board.direction[0]
            self.y += board.direction[1]
        self.x -= board.direction[0]
        self.y -= board.direction[1]

    def handle_collision(self, board, tile, depth):
        if self.value == tile.value:
            if not self.changedValue:
                self.value = self.value*2
                self.changedValue = True
                self.color = self.get_color(self.value)
                if depth:
                    board.score += self.value
                return True
        return False

    def set_size(self, game, width, value):
        s = 70
        t = game.fonts[s].render(str(value), True, (0, 0, 0)).convert_alpha()
        while t.get_width() > width - 15:
            s -= 5
            if s < 20:
                return False
            t = game.fonts[s].render(str(value), True, (0, 0, 0)).convert_alpha()
        return t

    def draw(self, board, game, lerp):
        if self.state == -1 and lerp <= 5:
            board.tiles.remove(self)
            del self
            return

        if self.state != 1:
            if lerp > 5:
                if lerp <= 0:
                    x = self.x
                    y = self.y
                else:
                    l = (lerp-5)/5
                    x = self.x * (1 - l) + self.prevPos[0] * l
                    y = self.y * (1 - l) + self.prevPos[1] * l
            else:
                x = self.x
                y = self.y
        else:
            if lerp > 5:
                return
            x = self.x
            y = self.y

        midX = game.tileWidth * (x+0.5)
        midY = game.tileWidth * (y+0.5)

        if self.value != self.prevValue and lerp > 5:
            value = self.prevValue
            color = self.get_color(self.prevValue)
        else:
            value = self.value
            color = self.color

        if self.state == 1:
            if lerp <= 0:
                width = game.tileWidth-game.tileSpace
            else:
                width = (game.tileWidth-game.tileSpace)*(1 - lerp/4)
        else:
            width = game.tileWidth-game.tileSpace

        t = self.set_size(game, width, value)
        pygame.draw.rect(game.window, color, (midX - width / 2, midY - width / 2, width, width))
        if t is not False:
            game.window.blit(t, (
            game.tileWidth * (x + 0.5) - t.get_width() / 2, game.tileWidth * (y + 0.5) - t.get_height() / 2))

class Board:
    def __init__(self, width, height, tileSpawns):
        self.width = width
        self.height = height
        self.tileSpawns = tileSpawns
        self.tiles = []
        self.direction = (0, 0)
        self.end = False
        self.score = 0

    def reset(self):
        self.tiles = []
        for i in range(2):
            self.spawn_new_tile()
        self.direction = (0, 0)
        self.end = False
        self.score = 0

    def create_tile(self, x, y, value):
        self.tiles.append(Tile(x, y, value))

    def move(self, direction, depth=1):
        self.direction = direction
        if abs(self.direction[0]) > 0:
            for y in range(self.height):
                l = sorted([tile for tile in self.tiles if tile.y == y and tile.state != -1], key=lambda a:a.x, reverse=self.direction[0] > 0)
                for i in l:
                    i.move_until_hit(self, depth)
        elif abs(self.direction[1]) > 0:
            for x in range(self.width):
                l = sorted([tile for tile in self.tiles if tile.x == x and tile.state != -1], key=lambda a:a.y, reverse=self.direction[1] > 0)
                for i in l:
                    i.move_until_hit(self, depth)
        if depth:
            self.spawn_new_tile()
            self.detect_end()

    def get_tiles_at(self, x, y):
        return [i for i in self.tiles if i.x == x and i.y == y and i.state != -1]

    def spawn_new_tile(self):
        if len([i for i in self.tiles if i.state != -1]) >= self.width*self.height:
            return
        x = random.randrange(0, self.width)
        y = random.randrange(0, self.height)
        while len(self.get_tiles_at(x, y)) > 0:
            x = random.randrange(0, self.width)
            y = random.randrange(0, self.height)
        value = random.choice(self.tileSpawns)
        self.create_tile(x, y, value)

    def detect_end(self):
        if len([i for i in self.tiles if i.state != -1]) >= self.width*self.height:
            orig = copy.deepcopy(self.tiles)
            noMoves = 0
            for m in [(0, 1), (1, 0)]:
                self.move(m, depth=0)
                if len([i for i in self.tiles if i.state != -1]) >= self.width*self.height:
                    noMoves += 1
                self.tiles = copy.deepcopy(orig)
            if noMoves == 2:
                self.end = True

class Game:
    def __init__(self, gridWidth, gridHeight, tileSpawns):
        self.board = Board(gridWidth, gridHeight, tileSpawns)
        self.board.reset()

        self.tileWidth = 150
        self.tileSpace = 15
        self.animationLength = 10
        self.SCREEN_WIDTH = self.tileWidth*self.board.width
        self.SCREEN_HEIGHT = self.tileWidth*self.board.height+50
        self.window = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.fonts = dict(zip([i for i in range(20, 101)], [pygame.font.Font("Roboto.ttf", i) for i in range(20, 101)]))
        pygame.display.set_caption("2048")

        self.inputBox = InputBox(self, self.SCREEN_WIDTH / 2 - 160, self.SCREEN_HEIGHT / 2 - 160, 320, 60, (230, 230, 230), self.fonts[50])

        self.animateFrame = self.animationLength
        self.queueMove = None
        self.inputBox.text = ""

        self.reset()

    def reset(self):
        self.queueMove = None
        self.animateFrame = self.animationLength

        self.inputBox.text = ""
        pygame.key.set_repeat(0)

    def move(self, direction, depth=1):
        self.board.move(direction, depth)
        self.animateFrame = self.animationLength

    def update_display(self):
        self.window.fill((185, 173, 161))
        self.draw_empty()
        for tile in self.board.tiles:
            if tile.state != -1:
                tile.draw(self.board, self, self.animateFrame)
        for tile in self.board.tiles:
            if tile.state == -1:
                tile.draw(self.board, self, self.animateFrame)

        if self.board.end:
            self.draw_lose()
        t = self.fonts[40].render(f"Score: {self.board.score}", True, (0, 0, 0)).convert_alpha()
        self.window.blit(t, (10, self.tileWidth*self.board.height+5))

        pygame.display.flip()

    def draw_lose(self):
        s = pygame.Surface((self.SCREEN_WIDTH, 150))
        s.fill((230, 230, 230))
        s.set_alpha(180)
        self.window.blit(s, (0, self.SCREEN_HEIGHT / 2 - 50))
        
        t = self.fonts[20].render("Type your name to save your score:", True, (0, 0, 0)).convert_alpha()
        self.window.blit(t, (self.SCREEN_WIDTH / 2 - t.get_width() / 2, self.SCREEN_HEIGHT / 2 - t.get_height() / 2 - 200))
        t = self.fonts[100].render("You lost!", True, (0, 0, 0)).convert_alpha()
        self.window.blit(t, (self.SCREEN_WIDTH / 2 - t.get_width() / 2, self.SCREEN_HEIGHT / 2 - t.get_height() / 2))
        t = self.fonts[50].render("Press Enter to reset", True, (0, 0, 0)).convert_alpha()
        self.window.blit(t,
                         (self.SCREEN_WIDTH / 2 - t.get_width() / 2, self.SCREEN_HEIGHT / 2 - t.get_height() / 2 + 80))
        self.inputBox.draw()

    def draw_empty(self):
        for x in range(self.board.width):
            for y in range(self.board.height):
                pygame.draw.rect(self.window, (202, 193, 181), (self.tileWidth*x+self.tileSpace/2, self.tileWidth*y+self.tileSpace/2, self.tileWidth-self.tileSpace, self.tileWidth-self.tileSpace))

    def add_score(self, name, score):
        try:
            with open("score.json", "r") as f:
                d = json.load(f)
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            d = []
        newList = sorted(d + [(name, score)], key=lambda a: a[1], reverse=True)
        with open("score.json", "w") as f:
            json.dump(newList, f)

    def get_scores(self):
        try:
            with open("score.json", "r") as f:
                d = json.load(f)
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            with open("score.json", "w") as f:
                json.dump([], f)
            d = []
        return d

    def main(self):
        run = True
        clock = pygame.time.Clock()
        while run:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if bool(self.inputBox.text) and self.board.score > 0:
                            self.add_score(self.inputBox.text, self.board.score)
                        self.board.reset()
                        self.reset()
                    if not self.board.end:
                        if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                            self.queueMove = event.key
                        if event.key == pygame.K_s:
                            scores = self.get_scores()
                            newScores = []
                            for i in scores:
                                newScores.append(": ".join([str(j) for j in i]))
                            print("\n".join(["=== Scores ==="]+newScores))
                    else:
                        self.inputBox.handle_key(event)

            if self.queueMove is not None:
                if self.animateFrame == -1:
                    if not self.board.end:
                        if self.queueMove == pygame.K_UP:
                            self.move((0, -1))
                        if self.queueMove == pygame.K_DOWN:
                            self.move((0, 1))
                        if self.queueMove == pygame.K_LEFT:
                            self.move((-1, 0))
                        if self.queueMove == pygame.K_RIGHT:
                            self.move((1, 0))
                        self.queueMove = None

            self.update_display()
            if self.animateFrame > -1:
                self.animateFrame -= 1

        pygame.quit()

g = Game(2, 2, [2 for i in range(9)] + [4]) # GridWidth(int), GridHeight(int), TileSpawn(list)
g.main()
