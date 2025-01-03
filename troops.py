import pygame
import math
import config
import heapq
from helpers import is_positive, troop_info_init, round_to_tiles, rect_distance, pathfinder, troop_round_tiles

    
class Troop(pygame.sprite.Sprite):
    def __init__(self, name: str, start_pos: tuple[int, int], map):
        super().__init__()
        self.name = name
        self.game_map = map
        troop_info_init(self, name, config.troop_info, config.img_dict)
        size = map.og_tile_width * self.sizex * config.global_zoom, map.og_tile_height * self.sizey * config.global_zoom
        self.rect = pygame.rect.Rect((0, 0), size)
        self.rect.center = start_pos
        self.movex_timer = self.movey_timer = self.attack_timer = pygame.time.get_ticks()
        self.timex = self.timey = 0
        self.move_signs = [0, 0] #up/down, left/right
        self.moving = not len(map.non_wall_buildings) == 0
        self.attacking = False
        self.attackers = pygame.sprite.Group()
        self.movex = self.movey = (map.tile_width // 5)
        self.og_move = self.movex, self.movey
        self.target = self.main_target = None
        self.target_rect = None
        self.tile_idx = troop_round_tiles(start_pos, self.game_map)
        self.tile = self.game_map.all_tiles_list[self.tile_idx]
        self.tile_offsetx = self.rect.centerx - self.tile.rect.centerx 
        self.tile_offsety = self.rect.centery - self.tile.rect.centery 
        self.health_bar = HealthBar(self, map.tile_width)
        self.color = config.yellow
        self.target_radius = 0
    
    def update_size(self):
        size = self.game_map.tile_width * self.sizex, self.game_map.tile_height * self.sizey
        self.rect.width, self.rect.height = size
    
    def set_offsets(self):
        self.tile_idx = troop_round_tiles(self.rect.center, self.game_map)
        self.tile = self.game_map.all_tiles_list[self.tile_idx]
        self.tile_offsetx = self.rect.centerx - self.tile.rect.centerx 
        self.tile_offsety = self.rect.centery - self.tile.rect.centery 

    def adjust_for_zoom(self, zoom_factor):
        self.update_size()
        self.rect.centerx = self.tile.rect.centerx + (self.tile_offsetx * zoom_factor)
        self.rect.centery = self.tile.rect.centery + (self.tile_offsety * zoom_factor) 
        self.movex = (self.game_map.tile_width // 5) * self.move_signs[0]
        self.movey = (self.game_map.tile_width // 5) * self.move_signs[1]
        if self.target:
            new_radius = self.radius * config.global_zoom if self.path_target == "Wall" else 0
            self.main_target_rect = self.main_target.rect.inflate(new_radius, new_radius)
            self.target_rect = self.target[-1].rect.inflate(new_radius, new_radius)
        self.health_bar.zoom_update()

    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, config.black, self.rect, int(1 * config.global_zoom))

    def shift(self, x, y):
        self.rect.move_ip(x, y)
        if self.target:
            self.main_target_rect.center = self.main_target.rect.center
            self.target_rect.center = self.target[-1].rect.center
        self.health_bar.shift()

    def in_building_range(self):
        for building in self.game_map.non_wall_buildings:
            if building.agressive and (self.name != 'balloon' or building.name != 'Cannon'):
                dis = rect_distance(self.rect, building.rect)
                if dis <= building.damage_radius:
                    if not building.target:
                        building.target = self
                        self.attackers.add(building)
                    elif self not in building.wait_list and self != building.target:
                        building.wait_list.add(self)
                elif building in self.attackers:
                    building.target = None
                    self.attackers.remove(building)
    
    def valid_target(self, building):
        return not building.name == 'Wall'

    def calculate_target(self, group):
        dis_list = []
        self.target = []
        counter = 0
        self.tile_idx = troop_round_tiles(self.rect.center, self.game_map)
        for building in group:
            if self.valid_target(building):
                dis, *path = pathfinder(self.game_map, self.tile_idx, building, 
                                        config.MAP_SIZE + 2, self)
                heapq.heappush(dis_list, (dis, counter, (path, building)))
            counter += 1
        _, _, temp = heapq.heappop(dis_list)
        path, self.main_target = temp
        if len(path) == 1:
            self.target_rect = self.rect
            self.path_target = None
            return
        while path[1:]:
            self.target.append(self.game_map.all_tiles_list[path.pop(1)])
        self.path_target = self.target[-1].building
        new_radius = self.radius * config.global_zoom if self.path_target == "Wall" else 0
        self.main_target_rect = self.main_target.rect.inflate(new_radius, new_radius)
        self.target_rect = self.target[-1].rect.inflate(new_radius, new_radius)
        self.calculate_movement()
        self.movex_timer = self.movey_timer = pygame.time.get_ticks()
    
    def calculate_movement(self):
        centerx, centery = self.rect.center
        self.movex = self.movey = self.game_map.tile_width // 5
        self.current_target = self.target.pop(0) if len(self.target) > 1 else self.target[-1]
        target_centerx, target_centery = self.current_target.rect.center
        adjacent = target_centerx - centerx
        opposite = target_centery - centery
        self.move_signs = is_positive(adjacent), is_positive(opposite)
        angle = math.atan2(opposite, adjacent)
        cos_angle, sin_angle = math.cos(angle), math.sin(angle)
        self.timex = abs(self.speed/cos_angle) if cos_angle != 0 else float('inf')
        self.timey = abs(self.speed/sin_angle) if sin_angle != 0 else float('inf')
        self.movex *= self.move_signs[0]
        self.movey *= self.move_signs[1]
        self.moving = True

    def run(self, main_group, group):
        if not group:
            self.moving = False
            return 0
        if not self.target or not self.main_target in group or (self.path_target and not self.path_target in main_group):
            self.calculate_target(group)
        if self.target_rect.colliderect(self.rect) or self.target_rect.colliderect(self.rect):
            self.moving = False
            self.attacking = True
            self.attack_timer = pygame.time.get_ticks()
            self.attack_target = self.target[-1].building if self.path_target else self.main_target
            self.attack_idx = self.target[-1].idx if self.path_target else 0
            self.troop_idx = round_to_tiles(self.rect.center, 1, self.game_map)
            self.attack_target.attackers.add(self)
            self.in_building_range()
            return 0
        elif self.current_target.rect.colliderect(self.rect) or self.current_target.rect.colliderect(self.rect):
            self.calculate_movement()

        current_time = pygame.time.get_ticks()
        if current_time - self.movex_timer >= self.timex:
            self.rect.move_ip(self.movex, 0)
            self.movex_timer = pygame.time.get_ticks()
            self.in_building_range()
            self.health_bar.shift()
        if current_time - self.movey_timer >= self.timey:
            self.rect.move_ip(0, self.movey)
            self.movey_timer = pygame.time.get_ticks()
            self.in_building_range()
            self.health_bar.shift()

    def attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.attack_timer >= self.attack_speed:
            self.attack_target.health -= self.damage
            self.attack_target.health_bar.update_bar()
            self.attack_timer = current_time
            if self.attack_target.health <= 0:
                self.attack_target.destroy()

    def dead(self):
        self.kill()

class Barb(Troop):
    def __init__(self, start_pos, map):
        super().__init__("barbarian", start_pos, map)

class Archer(Troop):
    def __init__(self, start_pos, map):
        super().__init__("archer", start_pos, map)
        self.color = config.purple
        self.target_radius = 4

    def attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.attack_timer >= self.attack_speed:
            self.game_map.projs.add(Projectile(self.attack_target, self.rect.center, self.damage, self.game_map))
            self.attack_timer = current_time
            self.attack_target.health_bar.update_bar()
            if self.attack_target.health <= 0:
                self.attack_target.destroy()

class Giant(Troop):
    def __init__(self, start_pos, map):
        super().__init__("giant", start_pos, map)
        self.color = config.brown
    
    def valid_target(self, building):
        if self.game_map.defensive:
            return building.agressive
        return True
    
class Goblin(Troop):
    def __init__(self, start_pos, map):
        super().__init__("goblin", start_pos, map)
        self.color = config.green
    
    def valid_target(self, building):
        if self.game_map.resources:
            return building.resources
        return True
    
    def attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.attack_timer >= self.attack_speed:
            if self.attack_target.resources:
                self.attack_target.health -= self.damage
            self.attack_target.health_bar.update_bar()
            self.attack_target.health -= self.damage
            self.attack_timer = current_time
            if self.attack_target.health <= 0:
                self.attack_target.destroy()

class WallBreaker(Troop):
    def __init__(self, start_pos, map):
        super().__init__("wall_breaker", start_pos, map)
        self.color = config.grey
    
    def attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.attack_timer >= self.attack_speed:
            self.splash(self.attack_idx)
            self.attack_timer = current_time
            self.dead()

    def deal_damage(self, building):
        if building.name == "Wall":
            building.health -= self.damage * 39
        building.health -= self.damage
        building.health_bar.update_bar()
        if building.health <= 0:
            building.destroy()

    def splash(self, tile_idx):
        x, y = tile_idx % config.MAP_SIZE, tile_idx // config.MAP_SIZE
        buildings = set()
        for i in range(-1, 2):
            for j in range(-1, 2):
                temp_x, temp_y = x + i, y + j
                if 0 <= temp_x < config.MAP_SIZE and 0 <= temp_y < config.MAP_SIZE:
                    idx = temp_x + temp_y * config.MAP_SIZE
                    building = self.game_map.tile_list[idx].building
                    if building and building not in buildings:
                        buildings.add(building)
                        self.deal_damage(building)

class Balloon(Troop):
    def __init__(self, start_pos, map):
        super().__init__("balloon", start_pos, map)
        self.color = config.red
        self.target_radius = 0
        self.flying = True
    
    def valid_target(self, building):
        return Giant.valid_target(self, building)
    
    def deal_damage(self, building):
        building.health -= self.damage
        self.attack_target.health_bar.update_bar()
        if building.health <= 0:
            building.destroy()
    
    def attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.attack_timer >= self.attack_speed:
            WallBreaker.splash(self, self.troop_idx)
            self.attack_timer = current_time
    

class HealthBar:
    def __init__(self, entity, tile_size):
        self.entity = entity
        self.full_health = self.entity.health
        self.size_x = min(max(entity.rect.width - tile_size, tile_size*2), tile_size*3)
        self.size_y = tile_size / 5
        self.rect = pygame.rect.Rect((0, 0), (self.size_x, self.size_y))
        self.secondary_rect = pygame.rect.Rect((0, 0), (self.size_x, self.size_y))
        self.rect.center = self.entity.rect.midtop
        self.secondary_rect.midleft = self.rect.midleft

    def zoom_update(self):
        tile_size = self.entity.game_map.tile_width
        self.rect.width = min(max(self.entity.rect.width - tile_size, tile_size*2), tile_size*3)
        self.rect.height = tile_size / 5
        self.secondary_rect.width = self.rect.width * (self.entity.health / self.full_health)
        self.secondary_rect.height = self.rect.height
        self.shift()
    
    def draw(self, screen):
        pygame.draw.rect(screen, config.black, self.rect, 0, 20)
        pygame.draw.rect(screen, config.purple, self.secondary_rect, 0, 20)

    def shift(self):
        self.rect.center = self.entity.rect.midtop
        self.secondary_rect.midleft = self.rect.midleft

    def at_full_health(self):
        return self.entity.health == self.full_health
    
    def update_bar(self):
        self.secondary_rect.width = max(0, self.rect.width * (self.entity.health / self.full_health))

class Projectile(pygame.sprite.Sprite):
    def __init__(self, target: Troop, pos: tuple[int, int], damage: int, map):
        super().__init__()
        self.target = target
        self.game_map = map
        self.damage = damage
        self.speed = 10
        self.size = map.tile_width / 5
        self.rect = pygame.rect.Rect((0, 0), (self.size, self.size))
        self.rect.center = pos
        self.recalculate_target()
        self.movex_timer = self.movey_timer = pygame.time.get_ticks()

    def recalculate_target(self):
        self.movex = self.movey = 2
        centerx, centery = self.rect.center
        target_centerx, target_centery = self.target.rect.center
        adjacent = target_centerx - centerx
        opposite = target_centery - centery
        self.move_signs = is_positive(adjacent), is_positive(opposite)
        angle = math.atan2(opposite, adjacent)
        cos_angle, sin_angle = math.cos(angle), math.sin(angle)
        self.timex = abs(self.speed/cos_angle) if cos_angle != 0 else float('inf')
        self.timey = abs(self.speed/sin_angle) if sin_angle != 0 else float('inf')
        self.movex *= self.move_signs[0]
        self.movey *= self.move_signs[1]
    
    def draw(self, screen):
        pygame.draw.rect(screen, config.black, self.rect)
        if (not self.target or (not self.target in self.game_map.troops and 
                                not self.target in self.game_map.buildings)):
            self.kill()
            return
        if self.target.rect.colliderect(self.rect):
            self.target.health -= self.damage
            self.target.health_bar.update_bar()
            self.kill()
            return
        self.recalculate_target()
        current_time = pygame.time.get_ticks()
        if current_time - self.movex_timer >= self.timex:
            self.rect.move_ip(self.movex * config.global_zoom, 0)
            self.movex_timer = pygame.time.get_ticks()
        if current_time - self.movey_timer >= self.timey:
            self.rect.move_ip(0, self.movey * config.global_zoom)
            self.movey_timer = pygame.time.get_ticks()

    def shift(self, x, y):
        self.rect.move_ip(x, y)

    def update_size(self):
        size = self.game_map.tile_width / 5
        self.rect.width = self.rect.height = size
    
    def set_offsets(self):
        self.tile_idx = round_to_tiles(self.rect.center, 1, self.game_map)
        self.tile = self.game_map.tile_list[self.tile_idx]
        self.tile_offsetx = self.rect.centerx - self.tile.rect.centerx 
        self.tile_offsety = self.rect.centery - self.tile.rect.centery 

    def adjust_for_zoom(self, zoom_factor):
        self.update_size()
        self.rect.centerx = self.tile.rect.centerx + (self.tile_offsetx * zoom_factor)
        self.rect.centery = self.tile.rect.centery + (self.tile_offsety * zoom_factor) 
        
        