import pygame

size = WIDTH, HEIGHT = (800, 800)
FPS = 50

bars_len = 200
bars_height = 20

# не больше bars_height:
bars_border = 2

# хп игрока нужно внести в класс:
player_HP = 5
max_player_HP = 10

# защита игрока:
player_AR = 7
max_player_AR = 7

# мана игрока:
player_AM = 100
max_player_AM = 200

HP_bar = [0, 0]
AR_bar = [0, 25]
AM_bar = [0, 50]

# размеры инвентаря игрока:
INVENTORY = ["med_kit", "gun", "#", "\n",
             "#", "#", "#", "\n",
             "#", "#", "#", "\n"]

INVENTORY_CELL = 100

INVENTORY_W = 3
INVENTORY_H = 3


Basic_item_text_x = 0
Basic_item_text_y = -20
