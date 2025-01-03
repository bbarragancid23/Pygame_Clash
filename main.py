import pygame
import ctypes
import config
from building import Map, HotBar
from event_handlers import BuildingMode, AttackingMode

ctypes.windll.user32.SetProcessDPIAware()
pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
font = pygame.font.SysFont("Arial", 26)

def create_map(size: int):
    result = [[(i + j) % 2 for j in range(size)] for i in range(size)]
    result.insert(0, [-1 for _ in range(size + 2)])
    for row in result[1:]:
        row.insert(0, -1)
        row.append(-1)
    result.append([-1 for _ in range(size + 2)])
    return result

beginning_map = create_map(config.MAP_SIZE)
game_map = Map(beginning_map)
tile_group = game_map.all_tiles
building_group = game_map.buildings
non_wall_building_group = game_map.non_wall_buildings
troop_group = pygame.sprite.Group()
game_map.troops = troop_group
proj_group = pygame.sprite.Group()
game_map.projs = proj_group
all_entities = [tile_group, building_group, troop_group, proj_group]
troops_n_buildings = [building_group, troop_group]

def adjust_for_zoom(zoom_factor, mouse_pos):
    temp = config.global_zoom
    config.global_zoom *= zoom_factor
    if config.global_zoom > 7 or config.global_zoom < 0.9:
        config.global_zoom = temp
    else:
        for troop in troop_group:
            troop.set_offsets()
        for proj in proj_group:
            proj.set_offsets()
        game_map.zoom_tiles(zoom_factor, mouse_pos)
        for troop in troop_group:
            troop.adjust_for_zoom(zoom_factor)
        for proj in proj_group:
            proj.adjust_for_zoom(zoom_factor)

running = True

buildings_list = ['Gold_Mine', 'Town_Hall', 'Wall', 'Cannon', 'Elixar_Collector', 'Archer_Tower']
build_hotbar = HotBar(buildings_list, font)
troops_list = ["barbarian", "archer", "giant", "goblin", "wall_breaker", 'balloon']
troop_hotbar = HotBar(troops_list, font)

building_mode = BuildingMode(game_map, build_hotbar, screen)
attacking_mode = AttackingMode(game_map, troop_hotbar, troop_group)
building = True
attacking = False
        

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_TAB:
                building = not building
                attacking = not attacking
                if not attacking:
                    troop_group.empty()
                    for building in game_map.buildings_list:
                        building.remove()
                    game_map.buildings_list.clear()
                    game_map.defensive = 0
                    game_map.resources = 0
                else:
                    for troop in config.troop_inventory:
                        config.troop_inventory[troop] = config.og_troop_inventory[troop]
                    if attacking_mode.current_troop:
                        attacking_mode.current_troop.selected = False
                        attacking_mode.current_troop = None
        if building:
            building_mode.event_handler(event)
        elif attacking:
            attacking_mode.event_handler(event)
        if event.type == pygame.MOUSEWHEEL:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            movex, movey = 0, 0
            move_amount = 40
            keys = pygame.key.get_pressed()
            zoom = keys[pygame.K_LCTRL]
            zoom_factor = 1.1
            if event.y > 0:
                if not zoom:
                    movey = move_amount
            elif event.y < 0:
                if zoom:
                    zoom_factor = 0.9
                else:
                    movey = -move_amount
            elif event.x > 0 and not zoom:
                movex = -move_amount
            elif event.x < 0 and not zoom:
                movex = move_amount
            if not zoom:
                for lst in all_entities:
                    for entity in lst:
                        entity.shift(movex, movey)
            else:
                adjust_for_zoom(zoom_factor, (mouse_x, mouse_y))

    screen.fill(config.background)
    game_map.draw(screen)
    if building and building_mode.building:
        building_mode.building.hover(screen)
    for troop in troop_group:
        troop.draw(screen)
        if troop.moving:
            troop.run(building_group, non_wall_building_group)
        if troop.attacking:
            troop.attack()
    for list in troops_n_buildings:
        for entity in list:
            if entity.health < entity.health_bar.full_health:
                entity.health_bar.draw(screen)
    build_hotbar.draw(screen) if building else troop_hotbar.draw(screen)
    pygame.display.flip()

pygame.quit()
