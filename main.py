import os
import random
import sys
from time import time
import pygame
import math


def load_image(name, color_key=-1):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)

    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def load_level(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: list(x.ljust(max_width, '.')), level_map))


def terminate():
    pygame.quit()
    sys.exit()


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):

        # проверяем на "твердый ли" объект:
        if tile_type != "wall":
            super().__init__(tiles_group)
        else:
            super().__init__(solid_objects)
        self.image = tile_images[tile_type]
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, q, q2):
        pygame.sprite.Sprite.__init__(self)
        super().__init__(player_bullets)
        self.pos = [x, y]
        mx, my = pygame.mouse.get_pos()
        self.dir = (mx - x, my - y)
        length = math.hypot(*self.dir)
        if length == 0.0:
            self.dir = (0, -1)
        else:
            self.dir = (self.dir[0]/length, self.dir[1]/length)
        angle = math.degrees(math.atan2(-self.dir[1], self.dir[0]))

        self.image = pygame.Surface((10, 10)).convert_alpha()
        self.image.fill((255, 0, 0))
        self.speed = 5
        self.rect = self.image.get_rect(center=self.pos)

    def update(self):
        self.pos = [self.pos[0]+self.dir[0]*self.speed,
                    self.pos[1]+self.dir[1]*self.speed]

    def draw(self, surf):
        self.rect = self.image.get_rect(center=self.pos)
        screen.blit(self.image, self.rect)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, n_frames=1):
        super().__init__(animation_group)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)
        self.n_frames = n_frames

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % (len(self.frames) * self.n_frames)
        self.image = self.frames[self.cur_frame // self.n_frames]


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group)
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.pos = (pos_x, pos_y)
        self.razn_x = 0
        self.razn_y = 0

    def move(self, x, y):
        camera.dx -= tile_width * (x - self.pos[0])
        camera.dy -= tile_height * (y - self.pos[1])
        level_map[self.pos[1]][self.pos[0]] = "."
        self.pos = (x, y)
        level_map[self.pos[1]][self.pos[0]] = "@"

        # смещение спрайтов
        for sprite in tiles_group:
            camera.apply(sprite)
        for sprite in solid_objects:
            camera.apply(sprite)
        for sprite in enemies_group:
            camera.apply(sprite)
        for sprite in player_bullets:
            camera.apply(sprite)
        for sprite in enemy_bullets:
            camera.apply(sprite)

    def shoot(self, storona):
        bullet = Bullet(self.rect.centerx, self.rect.top + 30, storona, "player")
        player_bullets.add(bullet)
        all_sprites.add(bullet)

    def update_image(self, name_image):
        AnimatedSprite(load_image(name_image), 10, 1, (player.pos[0] - self.razn_x) * 50, (player.pos[1] - self.razn_y) * 50, 5)


class Status:
    def __init__(self, x, y, img=None, x2=10, y2=10,  color="green"):
        self.pos = (x, y)
        self.long = (x2, y2)

        if img != None:
            self.image = load_image("heart.png")
        else:
            self.image = pygame.Surface((x2, y2)).convert_alpha()
            self.image.fill(pygame.Color(color))
        self.speed = 2
        self.rect = self.image.get_rect(center=self.pos)

    def draw(self, surf):
        self.rect = self.image.get_rect(center=self.pos)
        surf.blit(self.image, self.rect)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(enemies_group)
        self.image = enemies_image
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.storona = "l"
        self.rect = self.image.get_rect().move(
            tile_width * self.pos_x + 15, tile_height * self.pos_y + 5)
        self.pos = (self.pos_x, self.pos_y)
        self.count = 0

    def move(self, x, y):
        level_map[self.pos[1]][self.pos[0]] = "."
        self.pos_x = x
        self.pos_y = y
        storona = random.randint(0, 3)
        if storona == 0:
            if level_map[y][x + 1] == '.':
                self.pos_x += 1
        elif storona == 1:
            if level_map[y][x - 1] == '.':
                self.pos_x -= 1
        elif storona == 2:
            if level_map[y + 1][x] == '.':
                self.pos_y += 1
        elif storona == 3:
            if level_map[y - 1][x] == '.':
                self.pos_y -= 1
        self.rect = self.image.get_rect().move(
            tile_width * self.pos_x, tile_height * self.pos_y)
        self.pos = (self.pos_x, self.pos_y)
        level_map[self.pos[1]][self.pos[0]] = "&"

    def shoot(self, storona):
        bullet = Bullet(self.rect.centerx, self.rect.top + 30, storona, "enemy")
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        # т.к класс пуль по итогу немного отличается, приходится осуществлять проверку:
        if not isinstance(obj, (Bullet)):
            obj.rect.x += self.dx
            obj.rect.y += self.dy
        else:
            obj.pos[0] += self.dx
            obj.pos[1] += self.dy

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = 0
        self.dy = 0


def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            # не знаю как оформить проверку на то, является ли объект твердым, пускай будет пока тут:
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == '#':
                Tile('wall', x, y)
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x, y)
            elif level[y][x] == "&":
                Tile('empty', x, y)
                new_enemy = Enemy(x, y)
    # вернем игрока, а также размер поля в клетках
    return new_player, x, y


def move(player, movement):
    x, y = player.pos
    if movement == "up":
        if y > 0 and level_map[y - 1][x] == ".":
            player.move(x, y - 1)
            player.razn_y -= 1
    elif movement == "down":
        if y < max_y and level_map[y + 1][x] == ".":
            player.move(x, y + 1)
            player.razn_y += 1
    elif movement == "left":
        if x > 0 and level_map[y][x - 1] == ".":
            player.move(x - 1, y)
            player.razn_x -= 1
    elif movement == "right":
        if x < max_x and level_map[y][x + 1] == ".":
            player.move(x + 1, y)
            player.razn_x += 1


pygame.init()
size = WIDTH, HEIGHT = (800, 800)
pygame.display.set_caption("Марио")
screen = pygame.display.set_mode(size)
FPS = 50
clock = pygame.time.Clock()
my_time = 0
f1 = pygame.font.Font(None, 36)

# хп игрока нужно внести в класс:
player_HP = 5
max_player_HP = 10

# список статусов:
status_list = []

# сердечко:
my_heart = Status(10, 10, "heart.png")

# Рамка:
heart_ram = Status(125, 10, None, 200, 20,  "white")
heart_ram_1 = Status(125, 10, None, 198, 18,  "black")

# полоска жизней:
realy_heart_line = Status(125, 10, None, 198, 18,  "green")

status_list.append(my_heart)
status_list.append(heart_ram)
status_list.append(heart_ram_1)
status_list.append(realy_heart_line)
text1 = f1.render(f'{player_HP}/{max_player_HP}', True, (180, 0, 0))


tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
solid_objects = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
animation_group = pygame.sprite.Group()

collision_list = [(solid_objects, player_bullets, False, True), (enemies_group, player_bullets, True, True), (player_group, enemy_bullets, False, True)]

tile_images = {
    'wall': load_image('box.png'),
    'empty': load_image('grass.png')
}

player_image = load_image('r.png')
enemies_image = load_image("enemy.png")

tile_width = tile_height = 50

camera = Camera()
level_map = load_level("map.map")
player, max_x, max_y = generate_level(level_map)
AnimatedSprite(load_image("m_r.png"), 10, 1, 350, 200, 5)
running = True
screen.blit(text1, (10, 50))
Storona = 'u'


def get_anim_file(storona):
    if storona == "u":
        player.update_image('m_u.png')
    elif storona == "d":
        player.update_image('m_d.png')
    elif storona == "l":
        player.update_image('m_l.png')
    elif storona == "r":
        player.update_image('m_r.png')


while running:
    tic = time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            player.shoot(Storona)
        if event.type == pygame.MOUSEMOTION:
            x, y = pygame.mouse.get_pos()

            if x < player.pos[0] * 50 and y < player.pos[1] * 50:
                if x > y:
                    Storona = "u"
                elif x < y:
                    Storona = "l"
            elif x > player.pos[0] * 50 and y < player.pos[1] * 50:
                if x > y:
                    Storona = "r"
                elif x < y:
                    Storona = "u"
            elif x < player.pos[0] * 50 and y > player.pos[1] * 50:
                if x > y:
                    Storona = "d"
                elif x < y:
                    Storona = "l"
            elif x > player.pos[0] * 50 and y > player.pos[1] * 50:
                if x > y:
                    Storona = "r"
                elif x < y:
                    Storona = "d"

            animation_group = pygame.sprite.Group()
            get_anim_file(Storona)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                move(player, "up")
                animation_group = pygame.sprite.Group()
                get_anim_file(Storona)
            elif event.key == pygame.K_s:
                move(player, "down")
                animation_group = pygame.sprite.Group()
                get_anim_file(Storona)
            elif event.key == pygame.K_a:
                move(player, "left")
                animation_group = pygame.sprite.Group()
                get_anim_file(Storona)
            elif event.key == pygame.K_d:
                move(player, "right")
                animation_group = pygame.sprite.Group()
                get_anim_file(Storona)


    # каждые n количество секунд срабатывает рандомайзер для действий:
    if my_time > 1:
        my_time = 0
        for enem in enemies_group.sprites():
            x, y = enem.pos
            enem.move(x, y)


    # собственно проверка на столкновение, надо вынести в отдельную функцию нрн:
    for test in collision_list:
        hits = pygame.sprite.groupcollide(test[0], test[1], test[2], test[3])
        if test[0] == enemies_group:
            for hit in hits:
                print(level_map[hit.pos_y][hit.pos_x])
                level_map[hit.pos_y][hit.pos_x] = "."

    screen.fill(pygame.Color("black"))
    camera.update(player)
    tiles_group.draw(screen)
    solid_objects.draw(screen)
    player_group.draw(screen)
    enemies_group.draw(screen)
    enemy_bullets.draw(screen)
    player_bullets.draw(screen)
    for bullet in player_bullets:
        bullet.draw(screen)
    for bullet in player_bullets:
        bullet.update()
        if not screen.get_rect().collidepoint(bullet.pos):
            player_bullets.remove(bullet)

    # пример статуса игрока HP:
    for status in status_list:
        status.draw(screen)
    screen.blit(text1, (100, 0))

    animation_group.draw(screen)
    animation_group.update()
    pygame.display.flip()
    clock.tick(FPS)

    toc = time()
    my_time += toc - tic

pygame.display.quit()
pygame.quit()