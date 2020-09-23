import sys
import random
import pygame
import numpy as np

pygame.init()

DEBUG = 1

class Colours:
    Background = 100, 100, 100
    Pavement = 125, 125, 125
    Debug = 255, 0, 0

size = width, height = 800, 500
clock = pygame.time.Clock()
font = pygame.font.SysFont('Consolas', 30)
screen = pygame.display.set_mode(size)

class Entity:

    def __init__(self, img, **kwargs):
        self.enable = True
        self.image = pygame.image.load(img)
        self.image = pygame.transform.scale(self.image,
            [int(dim * kwargs.get('scale', 1)) for dim in self.image.get_size()])
        self.image = pygame.transform.flip(self.image,
            kwargs.get('x_flip', False), kwargs.get('y_flip', False))
        self.rect = self.image.get_rect()
        self.spatial = np.zeros(shape=(3,3))
        for idim, dim in enumerate(['x', 'y', 'z']):
            for iqnt, qnt in enumerate(['', 'v_', 'a_']):
                arg_name = qnt + dim
                self.spatial[iqnt][idim] = kwargs.get(arg_name, 0.0)
        self.rect.centerx = int(self.spatial[0][0])
        self.rect.centery = int(self.spatial[0][1])
        self.has_ground = kwargs.get('has_ground', True)
        self.bounce = self.has_ground and kwargs.get('bounce', True)
        self.bounciness = kwargs.get('bounciness', 1.0) if self.bounce else 0.0
        self.friction = kwargs.get('friction', 0.0) if self.has_ground else 1.0

    def get_top(self):
        return self.rect.centery - self.rect.height * self.get_scale() / 2

    def get_bottom(self):
        return self.rect.centery + self.rect.height * self.get_scale() / 2

    def get_left(self):
        return self.rect.centerx - self.rect.width * self.get_scale() / 2

    def get_right(self):
        return self.rect.centerx + self.rect.width - self.get_scale() / 2

    def get_height(self):
        return self.rect.height * self.get_scale()

    def get_width(self):
        return self.rect.width * self.get_scale()

    def update(self):
        if not self.enable:
            return # Not enabled
        self.spatial[1] += self.spatial[2] # speed += acceletation
        self.spatial[1][:2] *= (1.0 - self.friction) # speed(x,z) *= (1 - friction)
        self.spatial[0] += self.spatial[1] # pos += speed
        if self.has_ground and self.spatial[0][2] < 0: # z < 0
            if self.bounce:
                self.spatial[0][2] = (self.bounciness *
                    (self.spatial[0][2] - self.spatial[1][2])) # z' = (z - v_z) * bounciness
                self.spatial[1][2] *= -self.bounciness # v_z *= -bounciness
            else:
                self.spatial[0][2] = 0 # z = 0
                self.spatial[1][2] = 0 # v_z = 0
        self.rect.centerx = int(self.spatial[0][0])
        self.rect.centery = int(self.spatial[0][1])

    def get_scale(self):
        return 1. + self.spatial[0][2] / 1000. # 1 + z / 1000

    def draw(self):
        if not self.enable:
            return # Not enabled
        x_flip = bool(self.spatial[1][0] < 0) # v_x < 0
        y_flip = bool(self.spatial[1][1] < 0) # v_y < 0
        img = self.image
        rect = self.rect
        if x_flip or y_flip:
            img = pygame.transform.flip(self.image, x_flip, y_flip)
        scale = self.get_scale()
        if scale != 1:
            new_size = [int(arg * scale) for arg in self.image.get_size()]
            if min(new_size) <= 0:
                return # Don't draw
            img = pygame.transform.scale(self.image, new_size)
            rect = rect.copy()
            rect.width = int(rect.width * scale)
            rect.height = int(rect.height * scale)
            rect.centerx = self.rect.centerx
            rect.centery = self.rect.centery
            rect.normalize()
        if DEBUG:
            pygame.draw.rect(screen, Colours.Debug, rect)
        screen.blit(img, rect)

class Player(Entity):

    def __init__(self, **kwargs):
        super().__init__("data/ball.gif", scale=0.5, a_z=-10,
            bounce=False, friction=0.3, **kwargs)
        self.basesp = 5
        self.maxsp = 10
        self.can_jump = True
    def update(self):
        if not self.enable:
            return
        key = pygame.key.get_pressed()
        if self.can_jump and key[pygame.K_SPACE]:
            self.spatial[1][2] = 200
            self.can_jump = False
        if not self.is_on_air() and not key[pygame.K_SPACE]:
            self.can_jump = True
        if key[pygame.K_LEFT]:
            self.spatial[1][0] = max(-self.maxsp, self.spatial[1][0] - self.basesp)
        if key[pygame.K_RIGHT]:
            self.spatial[1][0] = min(self.maxsp, self.spatial[1][0] + self.basesp)
        if key[pygame.K_UP]:
            self.spatial[1][1] = max(-self.maxsp, self.spatial[1][1] - self.basesp)
        if key[pygame.K_DOWN]:
            self.spatial[1][1] = min(self.maxsp, self.spatial[1][1] + self.basesp)
        super().update()

    def is_on_air(self):
        return self.spatial[0][2] > 0

class Car(Entity):
    def __init__(self, **kwargs):
        super().__init__("data/car.gif", scale=0.5, **kwargs)
    def update(self):
        super().update()
        if self.get_right() < 0:
            self.spatial[0][0] = width + self.get_width() / 2
        if self.get_left() > width:
            self.spatial[0][0] = - self.get_width() / 2
        if self.get_top() > height:
            self.spatial[0][1] = height + self.get_height() / 2
        if self.get_bottom() < 0:
            self.spatial[0][1] = - self.get_height() / 2

class Game:
    def __init__(self):
        self.level = 1
        self.score = 0
        self.player = Player(x=width/2, y=height*0.95)
        self.lower_pavement = pygame.Rect(0, 0,               width, int(height*0.1))
        self.upper_pavement = pygame.Rect(0, int(height*0.9), width, int(height*0.1))
        self.cars = {} # indexed by level
        self.end = False
    def _end(self):
        self.end = True
    def _check_colisions(self):
        for car in self.cars[self.level]:
            if (not self.player.is_on_air()
                and self.player.rect.colliderect(car.rect)):
                self.end = True
                self.player.enable = False
                break
    def _check_level(self):
        if self.player.spatial[0][1] < 0:
            self.player.spatial[0][1] = height
            self.cars.clear()
            self.level += 1
            self.score += 10
        if self.level not in self.cars:
            self.cars[self.level] = []
            car_y = height*0.25
            while True:
                direction = -1 if random.random() > 0.5 else 1
                car_x = random.randint(0, width)
                speed = direction * max(1, int(self.level * random.uniform(0.5, 1.5)))
                car = Car(x=car_x, y=car_y, v_x=speed)
                if (car.rect.colliderect(self.lower_pavement) or
                    car.rect.colliderect(self.upper_pavement)):
                    break
                self.cars[self.level].append(car)
                car_y += car.rect.height
    def update(self):
        self._check_level()
        self.player.update()
        for car in self.cars[self.level]:
            car.update()
        self._check_colisions()
    def draw(self):
        pygame.draw.rect(screen, Colours.Pavement, self.lower_pavement)
        pygame.draw.rect(screen, Colours.Pavement, self.upper_pavement)
        for car in self.cars[self.level]:
            car.draw()
        self.player.draw()
        screen.blit(font.render(f"Score: {self.score:07d}", True, (0, 0, 0)), (32, 10))
        screen.blit(font.render(f"Level: {self.level:07d}", True, (0, 0, 0)), (532, 10))
        if self.end:
            screen.blit(font.render("Game Over!", True, (100, 0, 0)), (232, 10))

game = Game()

#ball = Entity("data/ball.gif", x=width//2, y=height//2, v_x=1, a_x=-0.01, v_z=200, a_z=-10)

while True:

    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    game.update()

    screen.fill(Colours.Background)
    game.draw()
    pygame.display.flip()
