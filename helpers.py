import math
import config
import heapq

def is_positive(num: int):
    if num == 0:
        return 0
    elif num > 0:
        return 1
    return -1


def min_index(lst):
    min_idx = 0
    min_val = lst[0]
    for i, val in enumerate(lst[1:]):
        if val < min_val:
            min_val = val
            min_idx = i + 1
    return min_idx


def building_info_init(self, name, building_info, img_dict):
    self.info = building_info[name]
    self.building_size = int(self.info['sizex'])
    self.health = float(self.info['health'])
    self.agressive = bool(int(self.info['agressive']))
    if self.agressive:
        self.damage = float(self.info['damage'])
        self.damage_time = int(self.info['damage_time'])
        self.damage_radius = float(self.info['damage_radius'])
    self.gold = int(self.info['resources_g'])
    self.elixar = int(self.info['resources_e'])
    self.img = img_dict[name].convert_alpha()
    self.og_img = self.img


def troop_info_init(self, name, troop_info, img_dict):
    self.info = troop_info[name]
    self.health = float(self.info['health'])
    self.damage = float(self.info['damage'])
    self.speed = int(self.info['speed'])
    self.radius = int(self.info['radius'])
    self.attack_speed = int(self.info['attack_speed'])
    self.sizex = float(self.info['sizex'])
    self.sizey = float(self.info['sizey'])
    self.img = img_dict[name].convert_alpha()
    self.og_img = self.img


def round_to_tiles(mouse_pos: tuple[int, int], size: int, map):
    start_x, start_y = map.tile_list[0].rect.topleft
    mouse_x, mouse_y = mouse_pos
    mouse_x -= start_x
    mouse_y -= start_y
    tile_size = map.tile_width
    i, j = (mouse_x // tile_size, mouse_y // tile_size)
    i = max((size - 1) // 2, min(i, config.MAP_SIZE - (size + 2) // 2))
    j = max((size - 1) // 2, min(j, config.MAP_SIZE - (size + 2) // 2))
    return i + j * config.MAP_SIZE


def troop_round_tiles(mouse_pos: tuple[int, int], map):
    start_x, start_y = map.all_tiles_list[0].rect.topleft
    mouse_x, mouse_y = mouse_pos
    mouse_x -= start_x
    mouse_y -= start_y
    tile_size = map.tile_width
    i, j = (mouse_x // tile_size, mouse_y // tile_size)
    maximum = (config.MAP_SIZE + 2) - 3 // 2
    if i < 0 or i > maximum or j < 0 or j > maximum:
        return -1
    return i + j * (config.MAP_SIZE + 2)


def rect_distance(rect1, rect2):
    x, y = rect1.center
    x2, y2 = rect2.center
    return math.sqrt((x - x2)**2 + (y - y2)**2)


def heuristic(a, b, map_size):
    ax, ay = a % map_size, a // map_size
    bx, by = b % map_size, b // map_size
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

def pathfinder(game_map, start, building, map_size, troop) -> list[int]:
    directions = [
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]
    targets = [tile.main_idx for tile in building.building_tiles]
    open_set = []
    wall_set = []
    walls = set()
    game_grid = game_map.all_tiles_list
    wall_amount = game_map.wall_amount
    name = troop.name
    heapq.heappush(open_set, (0, start))
    g_score = {start: 0}
    z_score = {start: float('inf')}
    f_score = {start: float('inf')}
    came_from = {}
    distance = 0
    step_costs = {1: 1.0, 2: 1.414}
    if name == 'balloon':
        new_size = building.size - 2
        temp = []
        for j in range(new_size):
            row_start = building.size + 1 + (building.size * j)
            for i in range(new_size):
                temp.append(targets[row_start + i])
        targets = temp

        

    while open_set:
        _, current = heapq.heappop(open_set)
        wall_breaker_check = name == 'wall_breaker' and len(walls) == wall_amount and wall_amount > 0
        if (name != "wall_breaker" or wall_amount == 0) and z_score[current] <= troop.target_radius:
            path = []
            while current in came_from:
                path.append(current)
                distance += 1.0
                current = came_from[current]
            path.append(start)
            path.append(distance)
            return path[::-1]
        if wall_breaker_check:
            break
        current_row, current_col = current // map_size, current % map_size
        for dx, dy in directions:
            nx, ny = current_col + dx, current_row + dy
            if 0 <= nx < map_size and 0 <= ny < map_size:
                neighbor = nx + (ny * map_size)
                
                step_cost = step_costs[2 if dx != 0 and dy != 0 else 1]
                tentative_g_score = g_score[current] + step_cost
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    g_score[neighbor] = tentative_g_score
                    closest_target = min(targets, key=lambda t: heuristic(neighbor, t, map_size))
                    dis = heuristic(neighbor, closest_target, map_size)
                    f_score[neighbor] = tentative_g_score + dis
                    z_score[neighbor] = dis
                    came_from[neighbor] = current
                    if game_grid[neighbor].building and game_grid[neighbor].building.name == 'Wall':
                        if not name == "balloon":
                            heapq.heappush(wall_set, (f_score[neighbor], neighbor))
                            walls.add(neighbor)
                            continue
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    
    _, result = heapq.heappop(wall_set)
    path = []
    while result in came_from:
        path.append(result)
        distance += 1.0
        result = came_from[result]
    path.append(start)
    distance += 10.5
    path.append(distance)
    return path[::-1]
