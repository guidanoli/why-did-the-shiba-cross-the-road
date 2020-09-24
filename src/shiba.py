import os

import pygame
from pygame.locals import *
from pygame.compat import geterror

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, '..', 'data')

# functions to create our resources
def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

# classes for our game objects
class Shiba(pygame.sprite.Sprite):

    class State:
        WalkingTowards = 0
        WalkingRight = 1
        WalkingAway = 2
        WalkingLeft = 3
        SitTowards = 4

    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.frames = []
        self.basesp = 4
        for i in range(4 * 5):
            img, rect = load_image(os.path.join('shiba', f'tile{i:03d}.gif'), -1)
            img = pygame.transform.scale(img, [dim * self.basesp for dim in rect.size])
            rect = img.get_rect()
            self.frames.append((img, rect))
        self.image, self.rect = self.frames[0]
        self.previous_state = self.state = Shiba.State.SitTowards
        self.frame_cnt = 0
        self.frame = 0

    def update(self):
        key = pygame.key.get_pressed()
        if key[K_DOWN]:
            self.state = Shiba.State.WalkingTowards
            self.rect.move_ip((0, self.basesp))
        elif key[K_RIGHT]:
            self.state = Shiba.State.WalkingRight
            self.rect.move_ip((self.basesp, 0))
        elif key[K_UP]:
            self.state = Shiba.State.WalkingAway
            self.rect.move_ip((0, -self.basesp))
        elif key[K_LEFT]:
            self.state = Shiba.State.WalkingLeft
            self.rect.move_ip((-self.basesp, 0))
        else:
            self.state = Shiba.State.SitTowards
        if self.previous_state != self.state:
            self.frame_cnt = 0
            self.frame = 0
        if self.state == Shiba.State.SitTowards:
            self.image, _ = self.frames[self.state * 4 + self.frame]
            self.frame_cnt = min(self.frame_cnt + 1, 10*4 - 1)
            self.frame = self.frame_cnt // 10
        else:
            self.image, _ = self.frames[self.state * 4 + self.frame]
            self.frame_cnt = (self.frame_cnt + 1) % 40
            self.frame = (self.frame_cnt // 10) % 4
        self.previous_state = self.state

def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption('Shiba animation')

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))

    screen.blit(background, (0, 0))
    pygame.display.flip()

    clock = pygame.time.Clock()
    shiba = Shiba()
    allsprites = pygame.sprite.Group((shiba,))

    # Main Loop
    going = True
    while going:
        clock.tick(60)

        # Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                going = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    going = False

        allsprites.update()

        # Draw Everything
        screen.blit(background, (0, 0))
        allsprites.draw(screen)
        pygame.display.flip()

    pygame.quit()

# Game Over


# this calls the 'main' function when this script is executed
if __name__ == '__main__':
    main()
