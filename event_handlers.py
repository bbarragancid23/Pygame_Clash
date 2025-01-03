import pygame
from building import Map, HotBar, TempBuilding
import troops
from helpers import round_to_tiles, troop_round_tiles
import config

class BuildingMode:
    def __init__(self, game_map: Map, hotbar: HotBar, screen):
        self.offset_x = self.offset_y = self.tile_idx = 0
        self.test_size = 1
        self.game_map = game_map
        self.hotbar = hotbar
        self.drag = self.quick_wall_add = self.quick_wall_remove = False
        self.building_name = ''
        self.temp_building_info = []
        self.screen = screen
    
    def event_handler(self, event):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_x += self.offset_x
        mouse_y += self.offset_y
        self.building_idx = round_to_tiles((mouse_x, mouse_y), 1, self.game_map)
        self.building = self.game_map.tile_list[self.building_idx].building
        test = troop_round_tiles((mouse_x, mouse_y), self.game_map)
        self.tile_idx = round_to_tiles((mouse_x, mouse_y), self.test_size, self.game_map)
        mouse_pos = mouse_x, mouse_y
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_0:
                print(test, self.game_map.all_tiles_list[test].test(self.screen))
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for tile in self.hotbar.tiles:
                    if tile.rect.collidepoint(mouse_pos) and tile.name and tile.available:
                        if tile.name == "Wall":
                            self.wall_tile = tile
                        self.test_size = tile.building_size
                        self.building_name = tile.name
                        self.tile_idx = round_to_tiles((mouse_x, mouse_y), self.test_size, self.game_map)
                        self.game_map.update_map(self.tile_idx, self.test_size, self.building_name, False)
                        self.drag = True
                        break
                if self.building and not self.drag:
                    center_pos = self.building.center_tile.rect.center
                    self.offset_x = center_pos[0] - mouse_x
                    self.offset_y = center_pos[1] - mouse_y
                    mouse_x += self.offset_x
                    mouse_y += self.offset_y
                    self.drag = True
                    self.test_size = self.building.size
                    self.building_name = self.building.name
                    self.temp_building_info = [self.building.center_tile.idx, self.test_size, self.building_name]
                    self.game_map.temp_building = TempBuilding(self.building.name, self.building.tiles, 
                                                               self.building.center_tile)
                    self.game_map.buildings_list.remove(self.building)
                    self.building.remove()
                    self.tile_idx = round_to_tiles((mouse_x, mouse_y), self.test_size, self.game_map)
                    self.game_map.update_map(self.tile_idx, self.test_size, self.building_name, False)

                elif self.game_map.check_wall_adjacency(self.building_idx) and self.wall_tile.available and not self.drag:
                    self.test_size = 1
                    self.building_name = "Wall"
                    self.game_map.update_map(self.building_idx, self.test_size, self.building_name, True)
                    self.drag = True
                    self.quick_wall_add = True 

            elif event.button == 3:
                if self.building:
                    if self.building.name == 'Wall':
                        self.quick_wall_remove = True
                        self.drag = True
                    self.game_map.buildings_list.remove(self.building)
                    self.building.remove()
                    
        if event.type == pygame.MOUSEMOTION:
            if self.drag and self.tile_idx != self.game_map.current_tile_idx:
                self.game_map.normal_map()
                if self.quick_wall_add and not self.building:
                    if self.wall_tile.available and self.game_map.check_wall_adjacency(self.building_idx):
                        self.game_map.update_map(self.tile_idx, self.test_size, self.building_name, True)
                    else:
                        self.drag = False
                        self.quick_wall_add = False
                elif self.quick_wall_remove:
                    if self.building and self.building.name == 'Wall':
                        self.game_map.buildings_list.remove(self.building)
                        self.building.remove()
                        self.building = None
                elif not self.hotbar.hotbar_rect.collidepoint(mouse_pos):
                    self.game_map.update_map(self.tile_idx, self.test_size, self.building_name, False)
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.drag:
                self.drag = False
                self.game_map.temp_building = None
                self.offset_x = self.offset_y = 0
                self.game_map.normal_map()
                if (self.game_map.valid_placing and not self.hotbar.hotbar_rect.collidepoint(mouse_pos) 
                    and not self.quick_wall_add):
                    self.game_map.update_map(self.tile_idx, self.test_size, self.building_name, True)
                elif self.temp_building_info:
                    self.game_map.update_map(self.temp_building_info[0], self.temp_building_info[1], 
                                             self.temp_building_info[2], True)
                self.temp_building_info.clear()
                self.quick_wall_add = False
            if event.button == 3 and self.drag:
                self.quick_wall_remove = False
                self.drag = False
                if self.building:
                    self.game_map.buildings_list.remove(self.building)
                    self.building.remove()
                self.game_map.normal_map()

class AttackingMode:
    def __init__(self, game_map, hotbar, group):
        self.game_map = game_map
        self.hotbar = hotbar
        self.group = group
        self.tile_height = self.game_map.tile_height
        self.current_troop = None

    def make_troop(self, name, mouse_pos):
        if name == "barbarian":
            return troops.Barb(mouse_pos, self.game_map)
        elif name == "archer":
            return troops.Archer(mouse_pos, self.game_map)
        elif name == 'giant':
            return troops.Giant(mouse_pos, self.game_map)
        elif name == 'goblin':
            return troops.Goblin(mouse_pos, self.game_map)
        elif name == 'wall_breaker':
            return troops.WallBreaker(mouse_pos, self.game_map)
        elif name == 'balloon':
            return troops.Balloon(mouse_pos, self.game_map)

    def event_handler(self, event):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.building_idx = round_to_tiles((mouse_x, mouse_y), 1, self.game_map)
        self.building = self.game_map.tile_list[self.building_idx].building
        test = troop_round_tiles((mouse_x, mouse_y), self.game_map)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_0:
                print(self.game_map.all_tiles_list[test].main_idx)
        if event.type == pygame.MOUSEBUTTONDOWN:
            tile_idx = troop_round_tiles((mouse_x, mouse_y), self.game_map)
            tile = self.game_map.all_tiles_list[tile_idx]
            hotbar_hover = self.hotbar.hotbar_rect.collidepoint((mouse_x, mouse_y))
            if event.button == 1:
                for tile in self.hotbar.tiles:
                    if tile.rect.collidepoint((mouse_x, mouse_y)) and tile.name and tile.available:
                        if self.current_troop:
                            self.current_troop.selected = False
                        self.current_troop = tile
                        tile.selected = True
                        hotbar_hover = True
                if tile_idx >= 0 and not tile.placed and not hotbar_hover and self.current_troop:
                    if self.current_troop.available:
                        name = self.current_troop.name
                        self.group.add(self.make_troop(name, (mouse_x, mouse_y)))
                        config.troop_inventory[name] -= 1
