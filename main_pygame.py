import pygame, math, json, os, sys

# --- Configuration ---
SCREEN_W, SCREEN_H = 1280, 720
FOV = math.pi / 3
HALF_FOV = FOV / 2
NUM_RAYS = 160
MAX_DEPTH = 20
DELTA_ANGLE = FOV / NUM_RAYS
DIST = NUM_RAYS / (2 * math.tan(HALF_FOV))
PROJ_COEFF = 3 * DIST * 64
SCALE = SCREEN_W // NUM_RAYS
PLAYER_SPEED = 0.05

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Alternate Reality: Modern Demo")

# --- Load assets ---
def load_img(path):
    return pygame.image.load(path).convert()

img_floor = load_img("assets/images/floor.png")
img_wall_stone = load_img("assets/images/wall_stone.png")
img_wall_wood = load_img("assets/images/wall_wood.png")
img_wall_shop = load_img("assets/images/wall_shop.png")
img_door = load_img("assets/images/door.png")
img_sky_day = load_img("assets/images/sky_day.png")
img_sky_night = load_img("assets/images/sky_night.png")

# Load map
with open("data/map.txt") as f:
    world_map = [list(line.strip()) for line in f.readlines()]
MAP_W, MAP_H = len(world_map[0]), len(world_map)
TILE_SIZE = 1

# Establishments
with open("data/establishments.json") as f:
    establishments = json.load(f)

# --- Player ---
player_x, player_y = 2.5, 2.5
player_angle = 0
day_mode = True
in_inventory = False
in_establishment = None
menu_index = 0

# --- Utilities ---
def mapping(a, b): return int(a), int(b)

def get_texture(cell):
    if cell == "#": return img_wall_stone
    if cell == "t": return img_wall_wood
    if cell == "s": return img_wall_shop
    if cell == "b": return img_wall_shop
    if cell == "g": return img_wall_shop
    if cell == "h": return img_wall_shop
    if cell == "d": return img_door
    return img_wall_stone

# --- Raycasting ---
def ray_casting(px, py, pa):
    walls = []
    ox, oy = px, py
    xm, ym = math.cos(pa), math.sin(pa)
    for ray in range(NUM_RAYS):
        angle = pa - HALF_FOV + ray * DELTA_ANGLE
        sin_a, cos_a = math.sin(angle), math.cos(angle)
        for depth in range(1, MAX_DEPTH * 64):
            x = ox + depth * cos_a / 64
            y = oy + depth * sin_a / 64
            if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W:
                cell = world_map[int(y)][int(x)]
                if cell != ".":
                    depth *= math.cos(pa - angle)
                    proj_height = PROJ_COEFF / (depth + 0.0001)
                    texture = get_texture(cell)
                    walls.append((depth, proj_height, ray, texture))
                    break
    return walls

# --- Drawing ---
def draw_3d(walls):
    sky = img_sky_day if day_mode else img_sky_night
    sky_scaled = pygame.transform.scale(sky, (SCREEN_W, SCREEN_H // 2))
    floor_scaled = pygame.transform.scale(img_floor, (SCREEN_W, SCREEN_H // 2))
    screen.blit(sky_scaled, (0, 0))
    screen.blit(floor_scaled, (0, SCREEN_H // 2))
    for depth, proj_height, ray, texture in walls:
        col = texture.subsurface(0, 0, 1, 64)
        col = pygame.transform.scale(col, (SCALE, int(proj_height)))
        screen.blit(col, (ray * SCALE, SCREEN_H//2 - proj_height//2))

def draw_map_overlay():
    surf = pygame.Surface((MAP_W*8*2, MAP_H*8*2), pygame.SRCALPHA)
    surf.fill((40, 40, 40, 180))
    for y, row in enumerate(world_map):
        for x, c in enumerate(row):
            if c != ".":
                rect = pygame.Rect(x*16, y*16, 16, 16)
                pygame.draw.rect(surf, (150,150,150,200), rect)
                if c in establishments:
                    pygame.draw.text = pygame.font.SysFont("DejaVuSans", 12)
                    t = pygame.draw.text.render(c, True, (255,255,255))
                    surf.blit(t, (x*16+4, y*16+2))
    px, py = player_x*16, player_y*16
    pygame.draw.circle(surf, (255,0,0), (int(px), int(py)), 5)
    screen.blit(surf, (SCREEN_W//2 - surf.get_width()//2, SCREEN_H//2 - surf.get_height()//2))

def draw_compass():
    radius = 50
    cx, cy = 80, SCREEN_H//2
    pygame.draw.circle(screen, (200,200,200), (cx, cy), radius, 2)
    dirx = cx + radius * math.sin(player_angle)
    diry = cy - radius * math.cos(player_angle)
    pygame.draw.line(screen, (255,0,0), (cx, cy), (dirx, diry), 3)
    font = pygame.font.SysFont("DejaVuSans", 14, bold=True)
    for d, label in zip([0, math.pi/2, math.pi, 3*math.pi/2], ["N","E","S","W"]):
        lx = cx + (radius+10) * math.sin(d)
        ly = cy - (radius+10) * math.cos(d)
        text = font.render(label, True, (200,200,200))
        rect = text.get_rect(center=(lx, ly))
        screen.blit(text, rect)

def draw_establishment(name, menu_idx):
    img = pygame.image.load(f"assets/interiors/{name}.png").convert()
    img = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
    screen.blit(img, (0, 0))
    font = pygame.font.SysFont("DejaVuSans", 28)
    menu = establishments[name]["menu"]
    for i, item in enumerate(menu):
        color = (255,255,0) if i == menu_idx else (255,255,255)
        txt = font.render(f"{i+1}) {item}", True, color)
        screen.blit(txt, (100, 100 + i*40))

# --- Main Loop ---
clock = pygame.time.Clock()
show_map = False
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if in_establishment:
                if event.key == pygame.K_ESCAPE:
                    in_establishment = None
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    pass
            else:
                if event.key == pygame.K_m:
                    show_map = not show_map
                elif event.key == pygame.K_t:
                    day_mode = not day_mode
                elif event.key == pygame.K_i:
                    in_inventory = not in_inventory

    keys = pygame.key.get_pressed()
    if not in_establishment:
        if keys[pygame.K_w]:
            player_x += math.cos(player_angle) * PLAYER_SPEED
            player_y += math.sin(player_angle) * PLAYER_SPEED
        if keys[pygame.K_s]:
            player_x -= math.cos(player_angle) * PLAYER_SPEED
            player_y -= math.sin(player_angle) * PLAYER_SPEED
        if keys[pygame.K_a]:
            player_angle -= 0.05
        if keys[pygame.K_d]:
            player_angle += 0.05

    screen.fill((0,0,0))

    if in_establishment:
        draw_establishment(in_establishment, menu_index)
    elif in_inventory:
        font = pygame.font.SysFont("DejaVuSans", 36)
        screen.blit(font.render("Inventory (empty)", True, (255,255,255)), (SCREEN_W//2 - 150, SCREEN_H//2))
    else:
        walls = ray_casting(player_x, player_y, player_angle)
        draw_3d(walls)
        if show_map: draw_map_overlay()
        draw_compass()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
