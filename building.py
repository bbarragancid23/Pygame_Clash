import pygame
import math
import config
from helpers import building_info_init, rect_distance, min_index, troop_info_init
from troops import HealthBar, Projectile

class Tile(pygame.sprite.Sprite):
    def __init__(self, num: int, center_pos: tuple[int, int], size: tuple[int, int], idx: int, main_idx: int):
        super().__init__()
        self.num = num
        if self.num == 1:
            self.color = config.lighter_green
        elif self.num == 0:
            self.color = config.darker_green
        elif self.num == 2:
            self.color = config.red
        elif self.num == -1:
            self.color = config.dark_green
        else:
            self.color = config.tinted
        self.surf = pygame.Surface(size, pygame.SRCALPHA)
        self.surf.fill(self.color)
        self.og_color = self.color
        self.rect = pygame.rect.Rect((0, 0), size)
        self.og_size = size
        self.rect.center = center_pos
        self.og_num = num
        self.placed = False
        self.building = None
        self.buildings = []
        self.idx = idx
        self.main_idx = main_idx

    def update_size(self):
        size = (self.og_size[0] * config.global_zoom, self.og_size[1] * config.global_zoom)
        self.rect.width, self.rect.height = int(size[0]), int(size[1])
        self.surf = pygame.transform.scale(self.surf, self.rect.size)
        return self.rect.width, self.rect.height
    
    def draw(self, screen):
        self.surf.fill(self.og_color)
        screen.blit(self.surf, self.rect)
        if self.num > 1:
            self.surf.fill(self.color)
            screen.blit(self.surf, self.rect)

    def shift(self, x, y):
        self.rect.move_ip(x, y)
    
    def update_color(self, num: int):
        if num == 1:
            self.color = config.lighter_green
        elif num == 0:
            self.color = config.darker_green
        elif num == 2:
            self.color = config.red
            return 0
        elif num == 4:
            self.color = config.tinted
        elif num == 3:
            self.color = config.very_tinted
        self.num = num
    
    def reset_color(self):
        if not self.placed:
            self.update_color(self.og_num)
        elif self.building:
            self.update_color(3)
        else:
            self.update_color(4)

class HotBarTile(Tile):
    def __init__(self, name, center_pos, size, font):
        super().__init__(3, center_pos, size, -1, -1)
        self.name = name
        self.available = False
        if name:
            if name in config.building_info:
                building_info_init(self, name, config.building_info, config.img_dict)
                self.inventory = config.building_inventory
            else:
                troop_info_init(self, name, config.troop_info, config.img_dict)
                self.inventory = config.troop_inventory
            self.img = pygame.transform.scale(self.img, self.og_size)
            self.amount = self.inventory[self.name]
            self.font = font
            self.text_surface = font.render(str(self.amount), True, config.white)
            self.text_pos = list(self.rect.midtop)
            self.text_pos[0] += (self.rect.width / 4)
            self.available = True
            self.selected = False
        
    def draw(self, screen):
        super().draw(screen)
        if self.name:
            if self.amount != self.inventory[self.name]:
                self.amount = self.inventory[self.name]
                self.text_surface = self.font.render(str(self.amount), True, config.white)
                self.available = False if self.amount <= 0 else True
            screen.blit(self.img, self.rect)
            screen.blit(self.text_surface, self.text_pos)
            if not self.available or self.selected:
                super().draw(screen)


class Building(pygame.sprite.Sprite):
    def __init__(self, name: str, tiles: list[Tile], center_tile: Tile, map):
        super().__init__()
        self.tiles = tiles
        self.building_tiles = []
        self.game_map = map
        self.size = int(math.sqrt(len(tiles))) - 2
        self.name = name
        self.og_name = self.name
        building_info_init(self, name, config.building_info, config.img_dict)
        self.tile_size = self.tiles[self.size + 3].rect.width
        for tile in tiles:
            if tile:
                if tile.num == 3 and not tile.building:
                    tile.building = self
                    tile.placed = True
                    self.building_tiles.append(tile)
                tile.buildings.append(self)
        self.resources = False
        if self.gold or self.elixar:
            self.resources = True
            map.resources += 1
        self.total_size = (self.tile_size * self.size, self.tile_size * self.size)
        self.img = pygame.transform.scale(self.img, self.total_size)
        self.rect = pygame.rect.Rect(self.tiles[self.size + 3].rect.topleft, self.total_size)
        self.center_tile = center_tile
        self.attackers = pygame.sprite.Group()
        self.health_bar = HealthBar(self, self.tile_size)
        self.destoryed = False
        config.building_inventory[name] -= 1
        if self.agressive:
            self.og_damage_radius = self.damage_radius
            self.damage_radius = self.og_damage_radius * self.tile_size
            self.target = None
            self.wait_list = pygame.sprite.Group()
            self.timer = pygame.time.get_ticks()
            map.defensive += 1
        elif self.name == 'Wall':
            map.wall_amount += 1
    
    def hover(self, screen):
        pygame.draw.rect(screen, config.black, self.rect, 2)

    def draw(self, screen):
        if not self.destoryed:
            screen.blit(self.img, self.rect)
        if self.agressive and self.target:
            self.attack()

    def shift(self, x, y):
        self.rect.move_ip(x, y)
        self.health_bar.shift()
    
    def zoom_update(self):
        self.tile_size = self.tiles[self.size + 3].rect.width
        self.total_size = (self.tile_size * self.size, self.tile_size * self.size)
        self.img = self.og_img
        self.img = pygame.transform.scale(self.img, self.total_size)
        self.rect = pygame.rect.Rect(self.tiles[self.size + 3].rect.topleft, self.total_size)
        if self.agressive:
            self.damage_radius = self.og_damage_radius * self.tile_size
        self.health_bar.zoom_update()
    
    def remove(self):
        for tile in self.tiles:
            if tile:
                tile.buildings.remove(self)
                if tile.building == self:
                    tile.building = None
                if not tile.buildings:
                    tile.placed = False
                tile.reset_color()
        if not self.destoryed:
            if self.agressive:
                self.game_map.defensive -= 1
            elif self.resources:
                self.game_map.resources -= 1
            elif self.name == "Wall":
                self.game_map.wall_amount -= 1
        self.kill()
        config.building_inventory[self.og_name] += 1
    
    def destroy(self):
        for troop in self.attackers:
            troop.target = troop.target_rect = None
            troop.main_target = troop.main_target_rect = None
            troop.attacking = False
            if self.game_map.non_wall_buildings:
                troop.moving = True
        self.destoryed = True
        if self.agressive:
            self.game_map.defensive -= 1
        if self.resources:
            self.game_map.resources -= 1
        if self.name == "Wall":
            self.game_map.wall_amount -= 1
        self.name = None
        self.kill()

    def attack(self):
        if self.target.health <= 0:
            self.target.dead()
            self.target = None
            if self.wait_list:
                dis_list = [rect_distance(troop.rect, self.rect) for troop in self.wait_list]
                self.target = self.wait_list.sprites()[min_index(dis_list)]
                self.wait_list.remove(self.target)
                self.target.attackers.add(self)
        else:
            current_timer = pygame.time.get_ticks()
            if current_timer - self.timer >= self.damage_time:
                self.timer = current_timer
                self.game_map.projs.add(Projectile(self.target, self.rect.center, self.damage, self.game_map))


class TempBuilding(pygame.sprite.Sprite):
    def __init__(self, name, tiles, center_tile):
        building_info_init(self, name, config.building_info, config.img_dict)
        self.tiles = tiles
        self.size = int(math.sqrt(len(tiles))) - 2
        self.tile_size = self.tiles[self.size + 3].rect.width
        self.total_size = (self.tile_size * self.size, self.tile_size * self.size)
        self.img = pygame.transform.scale(self.img, self.total_size)
        self.rect = pygame.rect.Rect(self.tiles[self.size + 3].rect.topleft, self.total_size)
        self.center_tile = center_tile
    
    def draw(self, screen):
        screen.blit(self.img, self.rect)
    
    def remove(self):
        self.kill()

    def update_position(self, tiles):
        self.tiles = tiles
        self.rect = pygame.rect.Rect(self.tiles[self.size + 3].rect.topleft, self.total_size)


class Map:
    def __init__(self, map: list[list[int]]):
        self.map = map
        self.tile_width = self.tile_height = math.ceil(config.HEIGHT / len(self.map))
        self.og_tile_width = self.og_tile_height = self.tile_width
        self.tile_size = self.tile_width, self.tile_height
        self.tiles = pygame.sprite.Group()
        self.all_tiles = pygame.sprite.Group()
        self.buildings = pygame.sprite.Group()
        self.buildings_list = self.buildings.sprites()
        self.non_wall_buildings = pygame.sprite.Group()
        x = (config.WIDTH - config.HEIGHT + self.tile_width) / 2
        y = self.tile_height / 2
        counter = 0
        main_counter = 0 
        for row in self.map:
            for col in row:
                temp = Tile(col, (x, y), self.tile_size, counter, main_counter)
                if col != -1:
                    self.tiles.add(temp)
                    counter += 1
                self.all_tiles.add(temp)
                x += self.tile_width
                main_counter += 1
            y += self.tile_height
            x = (config.WIDTH - config.HEIGHT + self.tile_width) / 2
        self.tile_list = self.tiles.sprites()
        self.all_tiles_list = self.all_tiles.sprites()
        self.current_tile_idx = -1
        self.current_tile = None
        self.current_size = -1
        self.valid_placing = True
        self.temp_building = None
        self.defensive = 0
        self.resources = 0
        self.wall_amount = 0
    
    def draw(self, screen):        
        for tile in self.all_tiles:
            tile.draw(screen)
        for building in self.buildings:
            building.draw(screen)
        for proj in self.projs:
            proj.draw(screen)
        if self.temp_building:
            self.temp_building.draw(screen)

    def zoom_tiles(self, zoom_factor, mouse_pos):
        leftest_tile = self.all_tiles_list[0]
        dx = (leftest_tile.rect.centerx - mouse_pos[0]) * zoom_factor
        dy = (leftest_tile.rect.centery - mouse_pos[1]) * zoom_factor
        leftest_tile.rect.center = (mouse_pos[0] + dx, mouse_pos[1] + dy)
        self.tile_width, self.tile_height = leftest_tile.update_size()
        self.size = self.tile_width, self.tile_height
        left_tile = leftest_tile
        for i, tile in enumerate(self.all_tiles_list[1:], 1):
            tile.update_size()
            if i % (config.MAP_SIZE + 2) == 0:                
                tile.rect.midtop = leftest_tile.rect.midbottom
                leftest_tile = tile
                left_tile = leftest_tile
            else:
                tile.rect.midleft = left_tile.rect.midright
                left_tile = tile
                
        for building in self.buildings:
            building.zoom_update()

    def update_tiles(self, tile_idx: int, name: str, placing: bool):
        offset = (self.full_size - 1) // 2 if self.full_size % 2 != 0 else (self.full_size - 2) // 2
        start_pos = tile_idx - (config.MAP_SIZE * offset) - offset
        building_start = start_pos + 1 + config.MAP_SIZE
        left_flag = building_start % config.MAP_SIZE == 0
        right_flag = building_start % config.MAP_SIZE == config.MAP_SIZE - self.full_size + 2
        self.valid_placing = True
        new_building = []
        for i in range(self.full_size):
            for j in range(self.full_size):
                new_idx = start_pos + j + (config.MAP_SIZE * i)
                left_over = left_flag and new_idx % config.MAP_SIZE == config.MAP_SIZE - 1
                right_over = right_flag and new_idx % config.MAP_SIZE == 0
                if 0 <= new_idx < len(self.tile_list) and not left_over and not right_over:
                    tile = self.tile_list[new_idx]
                    if 0 < i < self.full_size - 1 and 0 < j < self.full_size - 1:
                        new_building.append(tile)
                        if tile.building:
                            set_num = 2
                            self.valid_placing = False
                        else:
                            set_num = 3
                        if not name:
                            if tile.buildings and not tile.building:
                                tile.update_color(4)
                            tile.reset_color()
                        else:
                            tile.update_color(set_num)
                    else:
                        if placing:
                            tile.placed = True
                        if name and tile.num != 3 and tile.num != 2:
                            tile.update_color(4)
                        elif tile.num != 2:
                            tile.reset_color()
                        new_building.append(tile)
                else:
                    new_building.append(None)

        if name:
            if placing:
                temp = Building(name, new_building, self.tile_list[tile_idx], self)
                self.buildings.add(temp)
                self.buildings_list.append(temp)
                if name != "Wall":
                    self.non_wall_buildings.add(temp)
            elif not self.temp_building:
                self.temp_building = TempBuilding(name, new_building, self.tile_list[tile_idx])
            else:
                self.temp_building.update_position(new_building)
    
    def update_map(self, tile_idx: int, size: int, name: str, placing: bool):
        self.current_tile = self.tile_list[tile_idx]
        self.current_size = size
        self.full_size = size + 2
        self.current_tile_idx = tile_idx
        self.update_tiles(tile_idx, name, placing)

    def normal_map(self):
        self.update_tiles(self.current_tile_idx, None, False)

    def check_wall_adjacency(self, tile_idx):
        temp = [1, -1, config.MAP_SIZE, -config.MAP_SIZE]
        for num in temp:
            new_idx = tile_idx + num
            if num == -1 and tile_idx % config.MAP_SIZE == 0:
                continue
            elif num == 1 and tile_idx % config.MAP_SIZE - 1 == 0:
                continue
            if new_idx >= 0 and new_idx < config.MAP_SIZE**2:
                temp_building = self.tile_list[new_idx].building
                if temp_building and temp_building.name == "Wall":
                    return True
        return False

class HotBar:
    def __init__(self, items: list[str], font):
        self.items = items
        self.amount_items = len(items)
        self.hotbar_size = config.HEIGHT, config.HEIGHT / 8
        self.tile_size = config.HEIGHT / 7, config.HEIGHT / 9 
        self.tile_spacing = config.HEIGHT / 6, config.HEIGHT / 8
        self.hotbar_surf = pygame.Surface(self.hotbar_size, pygame.SRCALPHA)
        self.hotbar_surf.fill(config.tinted)
        self.left = math.ceil((config.WIDTH - config.HEIGHT) / 2)
        self.top = math.ceil(config.HEIGHT - (config.HEIGHT / 8))
        self.hotbar_rect = pygame.rect.Rect((self.left, self.top), self.hotbar_size)
        tile_startx = self.left + (self.tile_spacing[0] / 2)
        tile_starty = self.top + (self.tile_spacing[1] / 2)
        self.tiles = pygame.sprite.Group()
        for i in range(6):
            if i < self.amount_items:
                self.tiles.add(HotBarTile(items[i], (tile_startx, tile_starty), self.tile_size, font))
            else:
                self.tiles.add(HotBarTile(None, (tile_startx, tile_starty), self.tile_size, font))
            tile_startx += self.tile_spacing[0]
    
    def draw(self, screen):
        screen.blit(self.hotbar_surf, self.hotbar_rect)
        for tile in self.tiles:
            tile.draw(screen)
