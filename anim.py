import os
import sys

import pygame


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


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, n_frames=1):
        super().__init__(all_sprites)
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


pygame.init()
size = WIDTH, HEIGHT = (500, 500)
pygame.display.set_caption("Анимированный спрайт")
screen = pygame.display.set_mode(size)
FPS = 50
clock = pygame.time.Clock()

all_sprites = pygame.sprite.Group()
AnimatedSprite(load_image("m_l.png"), 10, 1, 100, 50, 5)

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                all_sprites = pygame.sprite.Group()
                AnimatedSprite(load_image("m_u.png"), 10, 1, 50, 50, 5)
    screen.fill(pygame.Color("black"))
    all_sprites.draw(screen)
    all_sprites.update()
    pygame.display.flip()
    clock.tick(FPS)
pygame.display.quit()
pygame.quit()