import heapq

def heuristic(a, b, grid_size):
    ax, ay = a % grid_size, a // grid_size
    bx, by = b % grid_size, b // grid_size
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

def a_star(grid, grid_size, start, target):
    directions = [
        (1, 0), (-1, 0), (0, 1), (0, -1), 
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]
    
    open_set = []
    wall_set = []
    heapq.heappush(open_set, (0, start))  # Priority queue (f-score, node)
    g_score = {start: 0}
    f_score = {start: heuristic(start, target, grid_size)}
    came_from = {}
    distance = 0

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == target:
            path = []
            while current in came_from:
                path.append(current)
                distance += heuristic(current, came_from[current], grid_size)
                current = came_from[current]
            path.append(start)
            path.append(distance)
            return path[::-1]

        current_row, current_col = current // grid_size, current % grid_size
        for dx, dy in directions:
            nx, ny = current_col + dx, current_row + dy
            if 0 <= nx < grid_size and 0 <= ny < grid_size:
                neighbor = nx + (ny * grid_size)
                
                step_cost = ((dx ** 2 + dy ** 2) ** 0.5)
                tentative_g_score = g_score[current] + step_cost

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, target, grid_size)
                    came_from[neighbor] = current
                    if grid[neighbor] == 1:  # Obstacle
                        heapq.heappush(wall_set, (f_score[neighbor], neighbor))
                        continue
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    
    _, result = heapq.heappop(wall_set)
    path = []
    while result in came_from:
        path.append(result)
        distance += heuristic(result, came_from[result], grid_size)
        result = came_from[result]
    path.append(start)
    distance += 10.5
    path.append(distance)
    return path[::-1] # No path found

grid_size = 10
grid = [
    0, 1, 0, 0, 0, 0, 0, 0, 1, 0,
    0, 1, 1, 1, 1, 1, 0, 1, 1, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 0, 0, 0, 0, 0, 1, 1,
    1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 0, 0, 0, 1,
    1, 1, 1, 1, 1, 1, 0, 0, 1, 0,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
]

start = 10  # Top-left corner (0, 0)
target = 99  # Bottom-right corner (9, 9)

path = a_star(grid, grid_size, start, target)

if path:
    print(path)
    dis, *path = path
    print(f"Path found with distance: {dis} tiles:")
    for p in path:
        row, col = p // grid_size, p % grid_size
        print(f"({row}, {col})")
else:
    print("No path found")

def a_star_minimize_walls(grid, grid_size, start, target):
    directions = [
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]

    open_set = []
    heapq.heappush(open_set, (0, 0, 0, start))  # (walls_broken, path_cost, heuristic, node)
    g_score = {start: 0}
    walls_broken = {start: 0}
    came_from = {}

    while open_set:
        current_walls, current_cost, _, current = heapq.heappop(open_set)

        if current == target:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1], walls_broken[target]

        current_row, current_col = current // grid_size, current % grid_size
        for dx, dy in directions:
            nx, ny = current_col + dx, current_row + dy
            if 0 <= nx < grid_size and 0 <= ny < grid_size:
                neighbor = nx + (ny * grid_size)
                new_walls_broken = current_walls + (1 if grid[neighbor] == 1 else 0)
                step_cost = ((dx ** 2 + dy ** 2) ** 0.5)
                tentative_g_score = g_score[current] + step_cost

                if (neighbor not in g_score or
                        new_walls_broken < walls_broken.get(neighbor, float('inf')) or
                        (new_walls_broken == walls_broken.get(neighbor) and tentative_g_score < g_score[neighbor])):
                    g_score[neighbor] = tentative_g_score
                    walls_broken[neighbor] = new_walls_broken
                    priority = (new_walls_broken, tentative_g_score + heuristic(neighbor, target, grid_size))
                    heapq.heappush(open_set, (new_walls_broken, tentative_g_score, priority[1], neighbor))
                    came_from[neighbor] = current

    return None, None  # No path found

path, total_walls_broken = a_star_minimize_walls(grid, grid_size, start, target)

if path:
    print(f"Path found with {total_walls_broken} walls broken:")
    for p in path:
        row, col = p // grid_size, p % grid_size
        print(f"({row}, {col})")
else:
    print("No path found")