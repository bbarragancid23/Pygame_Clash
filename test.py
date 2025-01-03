import pygame
from random import randint
import math
import ctypes
from helpers import is_positive, min_index
from troops import Troop
import config

ctypes.windll.user32.SetProcessDPIAware()

pygame.init()

WIDTH, HEIGHT = 1920, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

grey = (100, 100, 100)
yellow = (255, 255, 0)
red = (255, 0, 0)
blue = (0, 0, 255)

running = True

target_list = [(randint(50, 300), randint(50, 300)), 
                (randint(50, 300), randint(50, 300)),
                (randint(50, 300), randint(50, 300)),
                (randint(50, 300), randint(50, 300))]

test_group = pygame.sprite.Group()

global_zoom = 1.0

class Test(pygame.sprite.Sprite):
    def __init__(self, start_pos):
        super().__init__()
        self.og_size = (10, 30)
        size = int(10 * global_zoom), (30 * global_zoom)
        self.rect = pygame.rect.Rect((0, 0), size)
        self.rect.center = start_pos
        self.health = 400

    def update_size(self):
        size = int(self.og_size[0] * global_zoom), int(self.og_size[1] * global_zoom)
        self.rect.width, self.rect.height = size

    def draw(self):
        pygame.draw.rect(screen, blue, self.rect)

    def attacked(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()

for t in target_list:
    temp = Test(t)
    test_group.add(temp)

class Barb(pygame.sprite.Sprite):
    def __init__(self, start_pos):
        super().__init__()
        self.orignal_size = (10, 30)
        size = int(10 * global_zoom), int(30 * global_zoom)
        self.rect = pygame.rect.Rect((0, 0), size)
        self.rect.center = start_pos
        self.movex_timer = self.movey_timer = pygame.time.get_ticks()
        self.timex = self.timey = 0
        self.move_signs = [0, 0] #up/down, left/right
        self.vert_sign, self.horiz_sign = self.move_signs
        self.moving = True
        self.attacking = True
        self.damage = 8
        self.target_angle = 0
        self.movex, self.movey = 2, 2
        self.speed = 80
        self.dis_list = []
        self.target = ()
        self.radius = 5
    
    def update_size(self):
        size = int(self.orignal_size[0] * global_zoom), int(self.orignal_size[1] * global_zoom)
        self.rect.width, self.rect.height = size

    def draw(self):
        pygame.draw.rect(screen, yellow, self.rect)
        if self.target:
            new_radius = self.radius * global_zoom
            self.target_rect = self.target.rect.inflate(new_radius, new_radius)
            pygame.draw.rect(screen, red, self.target_rect)

    def calculate_target(self):
        centerx, centery = self.rect.center
        self.movex, self.movey = 2, 2
        self.dis_list = []
        for test in test_group:
            x, y = test.rect.center
            self.dis_list.append(math.sqrt((centerx - x)**2 + (centery - y)**2))
        self.target = test_group.sprites()[min_index(self.dis_list)]
        self.target_rect = self.target.rect.inflate(self.radius, self.radius)
        adjacent = self.target_rect.center[0] - centerx
        opposite = self.target_rect.center[1] - centery
        self.move_signs = is_positive(adjacent), is_positive(opposite)
        self.angle = math.atan2(opposite, adjacent)
        cos_angle, sin_angle = math.cos(self.angle), math.sin(self.angle)
        self.timex = abs(self.speed/cos_angle) if cos_angle != 0 else float('inf')
        self.timey = abs(self.speed/sin_angle) if sin_angle != 0 else float('inf')
        self.horiz_sign, self.vert_sign = self.move_signs
        self.movex *= self.horiz_sign
        self.movey *= self.vert_sign
        self.moving = True
    
    def run(self):
        if not self.target or not self.target in test_group:
            self.calculate_target()
        lx, ly = self.rect.midleft
        rx, ry = self.rect.midright
        if self.target_rect.collidepoint(lx, ly) or self.target_rect.collidepoint(rx, ry):
            self.movex, self.movey = 0, 0
            self.target.kill() #test
            self.target = ()
            test_group.add(Test((randint(50, 300), randint(50, 300))))
            return 0
        current_time = pygame.time.get_ticks()
        if current_time - self.movex_timer >= self.timex:
            self.rect.move_ip(self.movex * global_zoom, 0)
            self.movex_timer = pygame.time.get_ticks()
        if current_time - self.movey_timer >= self.timey:
            self.rect.move_ip(0, self.movey * global_zoom)
            self.movey_timer = pygame.time.get_ticks()

        return 1
    
barb_group = pygame.sprite.Group()

troop_group = pygame.sprite.Group()

all_entities = [barb_group, test_group]

def adjust_for_zoom(zoom_factor, mouse_pos):
    global global_zoom
    global_zoom *= zoom_factor
    for lst in all_entities:
        for entity in lst:
            dx = entity.rect.centerx - mouse_pos[0]
            dy = entity.rect.centery - mouse_pos[1]
            entity.rect.centerx = mouse_pos[0] + int(dx * zoom_factor)
            entity.rect.centery = mouse_pos[1] + int(dy * zoom_factor)

            entity.update_size()

def test_adjust(zoom_factor, mouse_pos):
    config.global_zoom *= zoom_factor
    for t in troop_group:
        t.adjust_for_zoom(zoom_factor, mouse_pos)

def event_handler(event):
    global barb_group, test_group, all_entities, running, zoom_factor
    if event.type == pygame.QUIT:
        running = False
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            running = False
        if event.key == pygame.K_k:
            barb_group.empty()
        if event.key == pygame.K_0:
            troop_group.add(Troop("barbarian", pygame.mouse.get_pos(), (10, 30)))
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            barb_group.add(Barb(pygame.mouse.get_pos()))
        if event.button == 3:
            test_group.add(Test(pygame.mouse.get_pos()))
    if event.type == pygame.MOUSEWHEEL:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        movex, movey = 0, 0
        keys = pygame.key.get_pressed()
        zoom = keys[pygame.K_LCTRL]
        zoom_factor = 1.1
        if event.y > 0:
            if not zoom:
                movey = 25
        elif event.y < 0:
            if zoom:
                zoom_factor = 0.9
            else:
                movey = -25
        elif event.x > 0 and not zoom:
            movex = -25
        elif event.x < 0 and not zoom:
            movex = 25
        if not zoom:
            for lst in all_entities:
                for entity in lst:
                    entity.rect.move_ip(movex, movey)
            for t in troop_group:
                t.rect.move_ip(movex, movey)
        else:
            adjust_for_zoom(zoom_factor, (mouse_x, mouse_y))
            test_adjust(zoom_factor, (mouse_x, mouse_y))

while running:
    for event in pygame.event.get():
        event_handler(event)

    clock.tick(60)  
    screen.fill(grey)
    for barb in barb_group:
        if barb.moving:
            barb.run()
            
    for t in troop_group:
        if t.moving:
            t.run(test_group)
        t.draw(screen)
    for group in all_entities:
        for entity in group:
            entity.draw()

    pygame.display.flip()

pygame.quit()