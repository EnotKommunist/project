import os
import random
import sys
from time import time
import pygame
import math
from settings import *
from items import *


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


level_map = load_level("map.map")


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


class Item(pygame.sprite.Sprite):
    def __init__(self, type, x, y, inventory_icon, inventory_place=-1):
        self.inventory_pos = inventory_place
        if type == "inventory":
            super().__init__(inventory_item_group)
        else:
            super().__init__(basic_item_group)
        self.text = Text(x + Basic_item_text_x - (len(ITEMS[inventory_icon][2]) + 11) * 3, y + Basic_item_text_y, f"[E] Взять: {ITEMS[inventory_icon][2]}")
        self.pos = [x, y]
        self.pos_x = x
        self.pos_y = y
        self.image = load_image(f"{ITEMS[inventory_icon][0]}")
        self.rect = self.image.get_rect(topleft=self.pos)
        self.inventory_icon = inventory_icon

    def draw(self, surf):
        self.rect = self.image.get_rect(topleft=self.pos)
        surf.blit(self.image, self.rect)


class Inventory(pygame.sprite.Sprite):
    def __init__(self, x, y, img=None, inventory_icon="#"):
        pygame.sprite.Sprite.__init__(self)
        super().__init__(inventory_group)
        self.pos = [x, y]

        self.image = load_image(f"{img}")
        self.rect = self.image.get_rect(topleft=self.pos)

    def draw(self, surf):
        self.rect = self.image.get_rect(topleft=self.pos)
        surf.blit(self.image, self.rect)


class Text:
    def __init__(self, x, y, text, color=(255, 255, 255)):
        self.color = color
        f1 = pygame.font.Font(None, 25)
        self.text = f1.render(f'{text}', True, self.color)
        self.pos_x = x
        self.pos_y = y

    def draw(self, surf):
        surf.blit(self.text, (self.pos_x, self.pos_y))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, type, speed, color=(255, 255, 255)):
        pygame.sprite.Sprite.__init__(self)
        self.pos = [x, y]
        if type == "player":
            super().__init__(player_bullets)
            mx, my = pygame.mouse.get_pos()
        elif type == "enemy":
            super().__init__(enemy_bullets)
            mx, my = player.rect.centerx + random.randint(-30, 30), player.rect.top + 30 + random.randint(-30, 30)
        self.color = color
        self.dir = (mx - x, my - y)
        length = math.hypot(*self.dir)
        if length == 0.0:
            self.dir = (0, -1)
        else:
            self.dir = (self.dir[0]/length, self.dir[1]/length)
        angle = math.degrees(math.atan2(-self.dir[1], self.dir[0]))

        self.image = pygame.Surface((10, 10)).convert_alpha()
        self.image.fill(color)
        self.speed = speed
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
    def __init__(self, pos_x, pos_y, hp, armor, mana, inventory=INVENTORY):
        super().__init__(player_group)
        self.hp = hp
        self.armor = armor
        self.mana = mana
        self.max_hp = hp
        self.max_armor = armor
        self.max_mana = mana
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.pos = (pos_x, pos_y)
        self.start_pos = (pos_x, pos_y)
        self.razn_x = 0
        self.razn_y = 0
        self.inventory_list = inventory

    def move(self, x, y):
        camera.dx -= tile_width * (x - self.pos[0])
        camera.dy -= tile_height * (y - self.pos[1])
        level_map[self.pos[1]][self.pos[0]] = "."
        self.pos = (x, y)
        level_map[self.pos[1]][self.pos[0]] = "@"

        camera.x += camera.dx
        camera.y += camera.dy

        # смещение спрайтов
        for sprite in tiles_group:
            camera.apply(sprite)
        for sprite in solid_objects:
            camera.apply(sprite)
        for sprite in enemies_group:
            sprite.type = "player_move"
            camera.apply(sprite)
        for sprite in player_bullets:
            camera.apply(sprite)
        for sprite in enemy_bullets:
            camera.apply(sprite)
        for sprite in basic_item_group:
            camera.apply(sprite)

    def shoot(self, storona):
        if self.mana > 3:
            self.mana -= 4
            bullet = Bullet(self.rect.centerx, self.rect.top + 30, "player", 7, (255, 0, 0))
            player_bullets.add(bullet)
            all_sprites.add(bullet)

    def update_image(self, name_image):
        AnimatedSprite(load_image(name_image), 10, 1, (player.pos[0] - self.razn_x) * 50, (player.pos[1] - self.razn_y) * 50, 5)


class Status:
    def __init__(self, x, y, img=None, x2=10, y2=10,  color="green"):
        self.pos = [x, y]
        self.x2 = x2
        self.y2 = y2
        self.long = [x2, y2]
        self.color = color

        if img != None:
            self.image = load_image(f"{img}")
        else:
            self.image = pygame.Surface((self.x2, self.y2)).convert_alpha()
            self.image.fill(pygame.Color(color))
        self.speed = 2
        self.rect = self.image.get_rect(topleft=self.pos)
        status_list.append(self)

    def draw(self, surf):
        self.rect = self.image.get_rect(topleft=self.pos)
        surf.blit(self.image, self.rect)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(enemies_group)
        self.image = enemies_image
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.storona = "l"
        self.rect = self.image.get_rect().move(
            tile_width * self.pos_x, tile_height * self.pos_y)
        self.pos = [self.pos_x, self.pos_y]
        self.razn_x = 0
        self.razn_y = 0
        self.type = 0
        self.camera_pos = [self.pos[0], self.pos[1]]

    def brain(self):
        storona = random.randint(0, 3)
        if storona == 0:
            storona = "right"
        elif storona == 1:
            storona = "left"
        elif storona == 2:
            storona = "down"
        elif storona == 3:
            storona = "up"
        return storona

    def move(self, x, y):
        level_map[self.pos[1]][self.pos[0]] = "."
        #print(level_map[self.pos[1]][self.pos[0]])
        x2, y2 = self.rect.x, self.rect.y
        enem_pos = (self.pos[0] - x, self.pos[1] - y)
        self.pos_x = x
        self.pos_y = y
        self.rect = self.image.get_rect().move(self.rect.x + enem_pos[0] * 50, self.rect.y + enem_pos[1] * 50)
        self.pos = [self.pos_x, self.pos_y]
        #print(level_map[self.pos[1]][self.pos[0]])
        level_map[self.pos[1]][self.pos[0]] = "&"
        #print(level_map[self.pos[1]][self.pos[0]])

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top + 30, "enemy", 5, (255, 255, 0))
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0
        self.x = 0
        self.y = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        # т.к класс пуль и врагов по итогу немного отличается, приходится осуществлять проверку:
        if isinstance(obj, (Bullet)):
            obj.pos[0] += self.dx
            obj.pos[1] += self.dy
        #elif isinstance(obj, (Enemy)):
        #    if obj.type == "enemy_move":
        #        obj.rect.x += self.x
        #        obj.rect.y += self.y
        #    elif obj.type == "player_move":
        #        obj.rect.x += self.dx
        #        obj.rect.y += self.dy
        else:
            obj.rect.x += self.dx
            obj.rect.y += self.dy

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = 0
        self.dy = 0


class Sprite_Mouse_Location(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        super().__init__(mouse_group)
        self.image = load_image("mouse.png")
        self.rect = pygame.Rect(0, 0, 1, 1)


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
                new_player = Player(x, y, max_player_HP, max_player_AR, max_player_AM, INVENTORY)
            elif level[y][x] == "&":
                Tile('empty', x, y)
                new_enemy = Enemy(x, y)
    # вернем игрока, а также размер поля в клетках
    return new_player, x, y


def move(object, movement):
    x, y = object.pos
    if not isinstance(object, (Player)):
        #print(movement)
        pass
    if movement == "up":
        if y > 0 and level_map[y - 1][x] == ".":
            object.move(x, y - 1)
            if isinstance(object, (Player)):
                object.razn_y -= 1
    elif movement == "down":
        if y < max_y and level_map[y + 1][x] == ".":
            object.move(x, y + 1)
            if isinstance(object, (Player)):
                object.razn_y += 1
    elif movement == "left":
        if x > 0 and level_map[y][x - 1] == ".":
            object.move(x - 1, y)
            if isinstance(object, (Player)):
                object.razn_x -= 1
    elif movement == "right":
        if x < max_x and level_map[y][x + 1] == ".":
            object.move(x + 1, y)
            if isinstance(object, (Player)):
                object.razn_x += 1


pygame.init()
pygame.display.set_caption("Soul Night")
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
my_time = 0
next_time = 0
inventory_view = False


def start_screen():
    global level_map
    fon = pygame.transform.scale(load_image('fon3.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    cube1_x, cube1_y = 200, 100
    cube2_x, cube2_y = 200, 300
    cube3_x, cube3_y = 200, 500
    line_x = cube1_x + 200
    line_y = cube1_y + 1
    line2_x = cube2_x + 200
    line2_y = cube2_y + 1
    line2_x = cube2_x + 200
    line2_y = cube2_y + 1
    line2_x = cube2_x + 200
    line2_y = cube2_y + 1
    line3_x = cube3_x + 200
    line3_y = cube3_y + 1
    line1 = 400
    line2 = 100
    last_x, last_y = 0, 0
    x, y = 0, 0

    cube = pygame.draw.polygon(screen, (0, 0, 0),
                               ((cube1_x, cube1_y), (cube1_x, line_y), (line_x, line_y), (line_x, cube1_y)))
    pygame.draw.polygon(screen, (0, 180, 0),
                        ((cube.x, cube.y), (cube.x, cube.y + line2), (cube.x + line1, cube.y + line2),
                         (cube.x + line1, cube.y)))
    cube_2 = pygame.draw.polygon(screen, (0, 0, 0),
                                 ((cube2_x, cube2_y), (cube2_x, line2_y), (line2_x, line2_y), (line2_x, cube2_y)))
    pygame.draw.polygon(screen, (180, 180, 0),
                        ((cube_2.x, cube_2.y), (cube_2.x, cube_2.y + line2), (cube_2.x + line1, cube_2.y + line2),
                         (cube_2.x + line1, cube_2.y)))
    cube_3 = pygame.draw.polygon(screen, (0, 0, 0),
                                 ((cube3_x, cube3_y), (cube3_x, line3_y), (line3_x, line3_y), (line3_x, cube3_y)))
    pygame.draw.polygon(screen, (180, 0, 0),
                        ((cube_3.x, cube_3.y), (cube_3.x, cube_3.y + line2), (cube_3.x + line1, cube_3.y + line2),
                         (cube_3.x + line1, cube_3.y)))

    f1 = pygame.font.Font(None, 36)
    text = f1.render(f'Легкий', True, (255, 255, 255))
    text_2 = f1.render(f'Нормальный', True, (255, 255, 255))
    text_3 = f1.render(f'Сложный', True, (255, 255, 255))

    screen.blit(text, (cube1_x + 150, cube1_y + 50))
    screen.blit(text_2, (cube2_x + 125, cube2_y + 50))
    screen.blit(text_3, (cube3_x + 140, cube3_y + 50))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if x >= cube.x and x <= cube.x + line1 and y >= cube.y and y <= cube.y + line2:
                    level_map = load_level("map.map")
                    return
                elif x >= cube_2.x and x <= cube_2.x + line1 and y >= cube_2.y and y <= cube_2.y + line2:
                    level_map = load_level("map2.map")
                    return
                elif x >= cube_3.x and x <= cube_3.x + line1 and y >= cube_3.y and y <= cube_3.y + line2:
                    level_map = load_level("map3.map")
                    return
        pygame.display.flip()
        clock.tick(FPS)

start_screen()

# список статусов:
status_list = []

tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
solid_objects = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
animation_group = pygame.sprite.Group()
inventory_group = pygame.sprite.Group()
inventory_item_group = pygame.sprite.Group()
basic_item_group = pygame.sprite.Group()
mouse_group = pygame.sprite.Group()

collision_list = [(solid_objects, player_bullets, False, True), (enemies_group, player_bullets, True, True), (player_group, enemy_bullets, False, True),
                  (basic_item_group, player_group, False, False), (solid_objects, enemy_bullets, False, True)]

tile_images = {
    'wall': load_image('box.png'),
    'empty': load_image('grass.png')
}

player_image = load_image('r.png')
enemies_image = load_image("turel.png")

tile_width = tile_height = 50

camera = Camera()
#level_map = load_level("map.map")
player, max_x, max_y = generate_level(level_map)

AnimatedSprite(load_image("m_r.png"), 10, 1, 350, 200, 5)
running = True
Storona = 'u'


# жизни:
Status(HP_bar[0] + 10, HP_bar[1] + 10, "heart.png")
Status(HP_bar[0] + 40, HP_bar[1] + 10, None, bars_len, bars_height, "white")
Status(HP_bar[0] + 40 + bars_border // 2, HP_bar[1] + 10 + bars_border // 2, None, bars_len - bars_border, bars_height - bars_border, "black")
realy_heart_line = Status(HP_bar[0] + 40 + bars_border // 2, HP_bar[1] + 10 + bars_border // 2, None, bars_len - bars_border, bars_height - bars_border, "green")

# броня:
Status(AR_bar[0] + 10, AR_bar[1] + 10, "shield.png")
Status(AR_bar[0] + 40, AR_bar[1] + 10, None, bars_len, bars_height,  "white")
Status(AR_bar[0] + 40 + bars_border // 2, AR_bar[1] + 10 + bars_border // 2, None, bars_len - bars_border, bars_height - bars_border,  "black")
realy_shield_line = Status(AR_bar[0] + 40 + bars_border // 2, AR_bar[1] + 10 + bars_border // 2, None, bars_len - bars_border, bars_height - bars_border,  "grey")

# мана:
Status(AM_bar[0] + 10, AM_bar[1] + 10, "mana.png")
Status(AM_bar[0] + 40, AM_bar[1] + 10, None, bars_len, bars_height,  "white")
Status(AM_bar[0] + 40 + bars_border // 2, AM_bar[1] + 10 + bars_border // 2, None, bars_len - bars_border, bars_height - bars_border,  "black")
realy_mana_line = Status(AM_bar[0] + 40 + bars_border // 2, AM_bar[1] + 10 + bars_border // 2, None, bars_len - bars_border, bars_height - bars_border,  "blue")

# запасной шрифт для текста:
f1 = pygame.font.Font(None, 36)

# у мыши теперь есть квадратный спрайт 1|1 пикселя:
mouse_sprite = Sprite_Mouse_Location()

# эту конструкцию не трогать(перенос предметов в инвентаре):
move_item = Item("inventory", 10, 100, "med_kit")


def dist(p1, p2=(move_item.pos[0] + ITEMS[move_item.inventory_icon][1][0], move_item.pos[1] + ITEMS[move_item.inventory_icon][1][1])):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


inventory_item_group.remove(move_item)
move_item = None
move_item_start_pos = [0, 0]
# за счет этой конструкции функция думает, что move_item - объект класса:

#счётчики игровых событий:
mana_time = 0
enemy_bullet_time = 0
ememy_bullet_reload = 0
bullet_count = 0


def get_anim_file(storona):
    if storona == "u":
        player.update_image('m_u.png')
    elif storona == "d":
        player.update_image('m_d.png')
    elif storona == "l":
        player.update_image('m_l.png')
    elif storona == "r":
        player.update_image('m_r.png')


def update_status_bar(player, bar, type, max_type):
    k = bar.long[0] / max_type
    bar.x2 = int(type * k)
    bar.image = pygame.Surface((bar.x2, bar.y2)).convert_alpha()
    bar.image.fill(pygame.Color(bar.color))


def new_inventory(inventory=INVENTORY):
    x, y = WIDTH / 2, HEIGHT / 2
    x2, y2 = INVENTORY_W, INVENTORY_H
    x2 = x2 / 2 * INVENTORY_CELL
    y2 = y2 / 2 * INVENTORY_CELL
    x, y = x - x2, y - y2
    for i in range(len(inventory)):
        if inventory[i] == "\n":
            x = WIDTH / 2 - x2
            y += INVENTORY_CELL
        else:
            if inventory[i] != "#":
                Item("inventory", x + ITEMS[inventory[i]][1][0], y + ITEMS[inventory[i]][1][1], inventory[i], i)
            Inventory(x, y, "inventory_icon.png", inventory[i])
            x += INVENTORY_CELL


new_inventory()


def get_inventory_coords(type, coords, inventory=INVENTORY):
    x, y = WIDTH / 2, HEIGHT / 2
    x2, y2 = INVENTORY_W, INVENTORY_H
    x2 = x2 / 2 * INVENTORY_CELL
    y2 = y2 / 2 * INVENTORY_CELL
    x, y = x - x2, y - y2

    for i in range(len(inventory)):
        if type == "coords" and inventory[i] == "#":
            return (x, y), i
        elif type == "count" and x == coords[0] and y == coords[1]:
            return i
        if inventory[i] == "\n":
            x = WIDTH / 2 - x2
            y += INVENTORY_CELL
        else:
            x += INVENTORY_CELL


while running:
    tic = time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:

            if not inventory_view:
                player.shoot(Storona)
            else:
                for my_mouse in mouse_group:
                    my_mouse.rect.center = pygame.mouse.get_pos()
                hits = pygame.sprite.groupcollide(inventory_item_group, mouse_group, False, False)
                for hit in hits:
                    move_item = hit
                    move_item_start_pos = hit.pos
                    player.inventory_list[move_item.inventory_pos] = "#"
                    break

        if event.type == pygame.MOUSEBUTTONUP:
            if move_item != None:
                hits = pygame.sprite.spritecollide(move_item, inventory_group, False)
                coords = []
                for hit in hits:
                    coords.append(hit.pos)
                if coords:
                    # если переносим в инвентарь, то предмет перенесется к ближайшей ячейке:
                    res = min(coords, key=dist)

                    if player.inventory_list[get_inventory_coords("count", (res[0],res[1]), player.inventory_list)] == "#":
                        player.inventory_list[move_item.inventory_pos] = "#"
                        move_item.pos = (
                        res[0] + ITEMS[move_item.inventory_icon][1][0], res[1] + ITEMS[move_item.inventory_icon][1][1])
                    else:
                        move_item.pos = move_item_start_pos

                    move_item.inventory_pos = get_inventory_coords("count",
                                                                   (move_item.pos[0] -
                                                                    ITEMS[move_item.inventory_icon][1][0],
                                                                    move_item.pos[1] -
                                                                    ITEMS[move_item.inventory_icon][1][1]),
                                                                   player.inventory_list)
                    player.inventory_list[move_item.inventory_pos] = move_item.inventory_icon

                else:
                    # иначе выбрасывает предмет себе под ноги:
                    player.inventory_list[move_item.inventory_pos] = "#"
                    move_item.pos = (player.pos[0] - player.razn_x) * 50, (player.pos[1] - player.razn_y) * 50
                    Item("Basic", move_item.pos[0], move_item.pos[1], move_item.inventory_icon)
                    inventory_item_group.remove(move_item)

                move_item.draw(screen)
            move_item = None

        if event.type == pygame.MOUSEMOTION:
            x, y = pygame.mouse.get_pos()

            # претаскивание предметов в инвентаре:
            if move_item != None:
                move_item.pos = pygame.mouse.get_pos()
                move_item.pos = move_item.pos[0] - ITEMS[move_item.inventory_icon][1][0], move_item.pos[1] - ITEMS[move_item.inventory_icon][1][
                    1]
                move_item.draw(screen)

            # поворот модельки героя к мыши:
            x2, y2 = (player.pos[0] - player.razn_x) * 50, (player.pos[1] - player.razn_y) * 50
            if x < player.start_pos[0] * 50 and y < player.start_pos[1] * 50:
                if x > y:
                    Storona = "u"
                elif x < y:
                    Storona = "l"
            elif x > player.start_pos[0] * 50 and y < player.start_pos[1] * 50:
                if x > y:
                    Storona = "r"
                elif x < y:
                    Storona = "u"
            elif x < player.start_pos[0] * 50 and y > player.start_pos[1] * 50:
                if x > y:
                    Storona = "d"
                elif x < y:
                    Storona = "l"
            elif x > player.start_pos[0] * 50 and y > player.start_pos[1] * 50:
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
            elif event.key == pygame.K_i:
                if inventory_view:
                    inventory_view = False
                else:
                    inventory_view = True

            elif event.key == pygame.K_e:
                # игрок берет 1 предмет в инвентарь:
                hits = pygame.sprite.groupcollide(basic_item_group, player_group, False, False)

                for hit in hits:
                    if "#" in player.inventory_list:
                        player.inventory_list[hit.inventory_pos] = "#"
                        hit.pos, k = get_inventory_coords("coords", hit.pos, player.inventory_list)
                        hit.pos = hit.pos[0] + ITEMS[hit.inventory_icon][1][0], hit.pos[1] + ITEMS[hit.inventory_icon][1][1]
                        hit.inventory_pos = k
                        player.inventory_list[hit.inventory_pos] = hit.inventory_icon
                        Item("inventory", hit.pos[0], hit.pos[1], hit.inventory_icon, hit.inventory_pos)
                        basic_item_group.remove(hit)
                    break
    if my_time > 0.01:
        mana_time += 0.01
        enemy_bullet_time += 0.01

        if mana_time > 0.25:
            mana_time = 0
            if player.mana < player.max_mana:
                player.mana += 1

        # 0.1
        if enemy_bullet_time > 0.1:
            enemy_bullet_time = 0
            if bullet_count > 0:
                bullet_count -= 1
            if ememy_bullet_reload <= 10 and bullet_count <= 0:
                ememy_bullet_reload += 1
            if ememy_bullet_reload >= 10 and bullet_count <= 0:
                ememy_bullet_reload = 0
                bullet_count = 1 + random.randint(1, 4)

            for enem in enemies_group.sprites():
                if screen.get_rect().collidepoint(enem.rect.x, enem.rect.y):
                    if bullet_count > 0:
                        enem.shoot()
        my_time = 0
    screen.fill(pygame.Color("black"))
    camera.update(player)
    tiles_group.draw(screen)
    solid_objects.draw(screen)
    player_group.draw(screen)
    enemies_group.draw(screen)
    enemy_bullets.draw(screen)
    player_bullets.draw(screen)
    mouse_group.draw(screen)

    for bullet in player_bullets:
        bullet.draw(screen)
    for bullet in player_bullets:
        bullet.update()

    for bullet in enemy_bullets:
        bullet.draw(screen)
    for bullet in enemy_bullets:
        bullet.update()

    basic_item_group.draw(screen)
    if inventory_view:
        for item in inventory_group:
            item.draw(screen)
        inventory_item_group.draw(screen)

    # отображает все показатели игрока:
    for status in status_list:
        status.draw(screen)

    text1 = Text(100, 10, f'{player.hp}/{player.max_hp}', (180, 0, 0))
    text2 = Text(110, 35, f'{player.armor}/{player.max_armor}', (180, 0, 0))
    text3 = Text(80, 60, f'{player.mana}/{player.max_mana}', (180, 0, 0))

    text1.draw(screen)
    text2.draw(screen)
    text3.draw(screen)

    # обновляем bar:
    update_status_bar(player, realy_heart_line, player.hp, player.max_hp)
    update_status_bar(player, realy_shield_line, player.armor, player.max_armor)
    update_status_bar(player, realy_mana_line, player.mana, player.max_mana)

    # собственно проверка на столкновение, надо вынести в отдельную функцию нрн:
    for test in collision_list:
        hits = pygame.sprite.groupcollide(test[0], test[1], test[2], test[3])
        if test[0] == enemies_group:
            for hit in hits:
                pass
                level_map[hit.pos_y][hit.pos_x] = "."
        if test[0] == basic_item_group:
            hit_list = []
            for hit in hits:
                hit.text.draw(screen)
        if test[0] == player_group and test[1] == enemy_bullets:
            for hit in hits:
                if player.armor > 0:
                    player.armor -= 1
                elif player.hp > 0:
                    player.hp -= 1

    if player.hp == 0:
        running = False

    animation_group.draw(screen)
    animation_group.update()
    pygame.display.flip()
    clock.tick(FPS)

    toc = time()
    my_time += toc - tic
    next_time += toc - tic

pygame.display.quit()
pygame.quit()
