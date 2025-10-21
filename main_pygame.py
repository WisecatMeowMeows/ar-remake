#!/usr/bin/env python3
"""
main_pygame.py - Alternate Reality Modern v0.6 unified runner

Features:
- Stepped first-person view (90° turns, 1 tile per step)
- Raycast-style wall renderer with textured columns (simple)
- Circular compass on left
- Enlarged translucent map overlay (16px tiles) toggled with M
- Inventory overlay toggled with I
- Day/night toggle with T (changes sky)
- Establishment interiors (keyboard menu) and actions that affect persistent stats
- Persistent player stats via player_data.py (data/player.json)
- Toast messages that fade over 2 seconds
"""

import os
import math
import time
import json
import pygame
from player_data import load_player, save_player, modify_stat
from interior_mode import draw_interior
#import interior_mode

# ---------------- Configuration ----------------
RES_X, RES_Y = 1280, 720
FOV_DEG = 90
FOV = math.radians(FOV_DEG)
HALF_FOV = FOV / 2.0
NUM_RAYS = 160
MAX_DEPTH = 40.0
DELTA_ANGLE = FOV / NUM_RAYS
SCALE = RES_X // NUM_RAYS
PROJ_COEFF = 3 * (NUM_RAYS / (2 * math.tan(HALF_FOV))) * 64
TILE = 64  # texture tile size for sampling
MAP_TILE_PIX = 16  # map overlay pixel size per tile (2x)
STEP_SIZE = 1  # stepped movement: 1 tile per step
TURN_ANGLE = math.pi / 2  # 90 degrees

# ---------------- Pygame init ----------------
pygame.init()
screen = pygame.display.set_mode((RES_X, RES_Y))
pygame.display.set_caption("Alternate Reality: Modern v0.6")
clock = pygame.time.Clock()
font_small = pygame.font.SysFont("DejaVuSans", 16)
font_med = pygame.font.SysFont("DejaVuSans", 20)
font_big = pygame.font.SysFont("DejaVuSans", 28)

# ---------------- Assets ----------------
ASSET_IMG_DIR = os.path.join("assets", "images")
ASSET_INT_DIR = os.path.join("assets", "interiors")
DATA_DIR = "data"
MAP_PATH = os.path.join(DATA_DIR, "map.txt")
EST_PATH = os.path.join(DATA_DIR, "establishments.json")

#global variables (a no-no)
est_type = "tavern"


def safe_load_texture(name, fallback_color=(150,150,150)):
    for ext in (".png", ".jpg", ".ppm"):
        p = os.path.join(ASSET_IMG_DIR, name + ext)
        if os.path.exists(p):
            try:
                img = pygame.image.load(p).convert()
                return pygame.transform.smoothscale(img, (TILE, TILE))
            except Exception:
                pass
    # fallback plain surface
    s = pygame.Surface((TILE, TILE))
    s.fill(fallback_color)
    return s

tex_floor = safe_load_texture("floor", (180,180,190))
tex_wall_stone = safe_load_texture("wall_stone", (200,200,200))
tex_wall_wood = safe_load_texture("wall_wood", (170,140,100))
tex_wall_shop = safe_load_texture("wall_shop", (190,185,180))
tex_door = safe_load_texture("door", (130,90,60))
tex_sky_day = safe_load_texture("sky_day", (135,206,235))
tex_sky_night = safe_load_texture("sky_night", (20,30,60))

# ---------------- Map & Establishments ----------------
if not os.path.exists(MAP_PATH):
    raise FileNotFoundError(f"Missing map file at {MAP_PATH}")

with open(MAP_PATH, "r") as f:
    world_map = [list(line.rstrip("\n")) for line in f.readlines()]
MAP_H = len(world_map)
MAP_W = len(world_map[0]) if MAP_H>0 else 0

if os.path.exists(EST_PATH):
    with open(EST_PATH, "r") as f:
        est_defs = json.load(f)
else:
    est_defs = {}

# try to find player start marked with '@', else center
start_x = start_y = None
for y,row in enumerate(world_map):
    for x,ch in enumerate(row):
        if ch == "@":
            start_x, start_y = x + 0.5, y + 0.5
            world_map[y][x] = "."  # clear marker
            break
    if start_x is not None:
        break
if start_x is None:
    start_x = MAP_W//2 + 0.5
    start_y = MAP_H//2 + 0.5

# ---------------- Player state ----------------
player = load_player()  # persistent stats dict
px, py = start_x, start_y
p_angle = -math.pi/2  # facing north by default

day_mode = True
show_map = False
show_inventory = False
in_est = None   # establishment type string when inside
est_menu_index = 0

# Toasts: list of dicts {text, start, duration}
toasts = []

def add_toast(text, duration=2.0):
    toasts.append({"text": text, "start": time.time(), "dur": duration})

# ---------------- Helpers ----------------
def is_blocking(tx, ty):
    if tx < 0 or ty < 0 or tx >= MAP_W or ty >= MAP_H:
        return True
    ch = world_map[int(ty)][int(tx)]
    return ch == "#"

def get_texture_for(ch):
    # map characters to textures (case-insensitive)
    c = ch.upper() if ch else ""
    if c == "#":
        return tex_wall_stone
    if c == "W" or c == "T":  # wooden/tavern
        return tex_wall_wood
    if c == "S" or c == "B" or c == "G" or c == "H":
        return tex_wall_shop
    if c == "D":
        return tex_door
    return tex_wall_stone

# ---------------- Raycasting ----------------
def cast_rays(px, py, pa):
    rays = []
    start_ang = pa - HALF_FOV
    for r in range(NUM_RAYS):
        ray_ang = start_ang + r * DELTA_ANGLE
        sin_a = math.sin(ray_ang)
        cos_a = math.cos(ray_ang)
        depth = 0.0
        hit_ch = None
        hit_x = hit_y = 0.0
        while depth < MAX_DEPTH:
            depth += 0.05
            cx = px + cos_a * depth
            cy = py + sin_a * depth
            ix, iy = int(cx), int(cy)
            if ix < 0 or iy < 0 or ix >= MAP_W or iy >= MAP_H:
                hit_ch = "#"
                break
            ch = world_map[iy][ix]
            if ch != ".":
                hit_ch = ch
                hit_x, hit_y = cx, cy
                break
        if hit_ch is None:
            hit_ch = "."
        # correct fish-eye
        depth_corr = depth * math.cos(pa - ray_ang)
        if depth_corr <= 0: depth_corr = 0.0001
        proj_h = min(int((TILE * RES_Y) / (depth_corr * 160)), RES_Y*2)
        # fractional hit for texture x
        frac = 0.0
        if hit_ch != ".":
            if abs(hit_x - int(hit_x)) > abs(hit_y - int(hit_y)):
                frac = hit_x - int(hit_x)
            else:
                frac = hit_y - int(hit_y)
            frac = abs(frac)
        rays.append({"depth": depth_corr, "proj_h": proj_h, "ray": r, "ch": hit_ch, "frac": frac})
    return rays

# ---------------- Drawing ----------------
def draw_sky_and_floor():
    # sky occupies top 1/3
    sky_tex = tex_sky_day if day_mode else tex_sky_night
    sky_h = RES_Y // 3
    # tile sky across width
    t_w = sky_tex.get_width()
    for x in range(0, RES_X, t_w):
        screen.blit(sky_tex, (x, 0), area=pygame.Rect(0,0,t_w,sky_h))
    # floor - tile from mid to bottom
    for y in range(RES_Y//2, RES_Y, TILE):
        for x in range(0, RES_X, TILE):
            screen.blit(tex_floor, (x, y))

def draw_walls(rays):
    x_off = (RES_X - NUM_RAYS * SCALE) // 2

    # Step 1: collect nearest visible ray per establishment
    nearest_hits = {}
    for i, rd in enumerate(rays):
        ch = rd["ch"]
        if ch and ch != "." and ch.lower() in est_defs:
            depth = rd["depth"]
            if ch not in nearest_hits or depth < nearest_hits[ch]["depth"]:
                nearest_hits[ch] = {"ray_index": i, "depth": depth, "rd": rd}

    # Step 2: draw walls normally
    for i, rd in enumerate(rays):
        depth = rd["depth"]
        ph = rd["proj_h"]
        ch = rd["ch"]
        frac = rd["frac"]
        tex = get_texture_for(ch)
        tx = int(frac * TILE) % TILE
        try:
            col = tex.subsurface(tx, 0, 1, TILE)
        except Exception:
            col = pygame.Surface((1, TILE))
            col.fill((150,150,150))
        col = pygame.transform.smoothscale(col, (SCALE, max(1, ph)))

        x = x_off + i * SCALE
        y = (RES_Y // 2) - ph // 2
        screen.blit(col, (x, y))

        # Step 3: draw establishment names once, directly on nearest visible wall (fade + large close-up)
        for ch, info in nearest_hits.items():
            rd = info["rd"]
            i = info["ray_index"]
            ph = rd["proj_h"]
            depth = rd["depth"]
            x = x_off + i * SCALE
            y = (RES_Y // 2) - ph // 2

            est = est_defs[ch.lower()]
            name = est.get("name") if isinstance(est, dict) else None
            if not name:
                name = est.get("type") if isinstance(est, dict) else ch

            # Fade and scale logic
            fade = max(0.1, min(1.0, 1.8 - depth / 6.0))        # close = opaque
            alpha = int(255 * fade)
            scale_factor = max(0.8, min(2.5, 3.0 - depth / 2.5))  # large close up, small far away

            #Render base text surfaces
            label_surf = font_small.render(name, True, (255, 255, 255))
            shadow_surf = font_small.render(name, True, (0, 0, 0))

            # Scale text
            if scale_factor != 1.0:
                new_size = (int(label_surf.get_width() * scale_factor),
                            int(label_surf.get_height() * scale_factor))
                label_surf = pygame.transform.smoothscale(label_surf, new_size)
                shadow_surf = pygame.transform.smoothscale(shadow_surf, new_size)

            label_surf.set_alpha(alpha)
            shadow_surf.set_alpha(alpha)

            # Position the text roughly at mid-height of wall
            label_x = x + (SCALE - label_surf.get_width()) // 2
            label_y = (RES_Y // 2) - (ph // 4)  # around mid-level of wall

            screen.blit(shadow_surf, (label_x + 2, label_y + 2))
            screen.blit(label_surf, (label_x, label_y))



def draw_compass():
    cx, cy = 60, RES_Y//2
    rad = 48
    pygame.draw.circle(screen, (30,30,30), (cx,cy), rad)
    pygame.draw.circle(screen, (80,80,80), (cx,cy), rad, 3)
    labels = [("N",0),("E",90),("S",180),("W",270)]
    for lab,deg in labels:
        ang = math.radians(deg) - math.pi/2
        lx = cx + int(math.cos(ang)*(rad-18))
        ly = cy + int(math.sin(ang)*(rad-18))
        t = font_med.render(lab, True, (220,220,220))
        tw, th = t.get_size()
        screen.blit(t, (lx - tw//2, ly - th//2))
    # pointer
    deg = math.degrees(p_angle) + 90
    ang = math.radians(deg-90)
    px_line = cx + int(math.cos(ang)*(rad-28))
    py_line = cy + int(math.sin(ang)*(rad-28))
    pygame.draw.line(screen, (255,215,60), (cx,cy), (px_line,py_line), 4)
    pygame.draw.circle(screen, (255,215,60), (px_line,py_line), 6)

def draw_map_overlay():
    scale = MAP_TILE_PIX
    map_w = MAP_W * scale
    map_h = MAP_H * scale
    mx = (RES_X - map_w)//2 + 80  # slight right shift to avoid compass
    my = (RES_Y - map_h)//2
    bg = pygame.Surface((map_w+8, map_h+8), pygame.SRCALPHA)
    bg.fill((30,30,30,180))
    screen.blit(bg, (mx-4, my-4))
    font_m = pygame.font.SysFont("DejaVuSans", 12)
    for y in range(MAP_H):
        for x in range(MAP_W):
            ch = world_map[y][x]
            rect = (mx + x*scale, my + y*scale, scale, scale)
            if ch == "#":
                pygame.draw.rect(screen, (40,40,40), rect)
            elif ch in ("W","t","T"):
                pygame.draw.rect(screen, (120,85,50), rect)
            elif ch in ("S","s"):
                pygame.draw.rect(screen, (90,140,140), rect)
            elif ch in ("D","d"):
                pygame.draw.rect(screen, (110,70,40), rect)
            else:
                pygame.draw.rect(screen, (200,200,200), rect)
            # establishment letters
            letter = None
            if ch in ("t","T"): letter = "T"
            if ch in ("s","S"): letter = "S"
            if ch in ("b","B"): letter = "B"
            if ch in ("g","G"): letter = "G"
            if ch in ("h","H"): letter = "H"
            if ch in ("d","D"): letter = "D"
            if letter:
                t = font_m.render(letter, True, (255,255,255))
                tx = mx + x*scale + (scale - t.get_width())//2
                ty = my + y*scale + (scale - t.get_height())//2
                screen.blit(t, (tx, ty))
    # player marker centered in tile
    ppx = mx + (int(px) * scale) + (scale // 2) 
    ppy = my + (int(py) * scale) + (scale // 2) 
    pygame.draw.circle(screen, (255,255,255), (ppx, ppy), max(3, scale//3))

def draw_inventory():
    w, h = 420, 260
    sx, sy = (RES_X - w)//2, (RES_Y - h)//2
    surf = pygame.Surface((w,h), pygame.SRCALPHA)
    surf.fill((20,20,20,200))
    pygame.draw.rect(surf, (200,200,200), (0,0,w,h), 2)
    lines = ["Inventory:", "", "• Rusty Sword", "• Leather Tunic", "• 3 Gold Coins", "• Apple", "", "Press I or ESC to close"]
    for i,l in enumerate(lines):
        surf.blit(font_med.render(l, True, (230,230,230)), (16, 16 + i*28))
    screen.blit(surf, (sx, sy))

def draw_hud_stats():
    # white text on translucent dark background at top-left
    lines = [
        f"Health: {player.get('health',0)}",
        f"Stamina: {player.get('stamina',0)}",
        f"Charisma: {player.get('charisma',0)}",
        f"Gold: {player.get('gold',0)}"
    ]
    w = 220
    h = 12 + 22 * len(lines)
    surf = pygame.Surface((w,h), pygame.SRCALPHA)
    surf.fill((10,10,10,180))
    for i,l in enumerate(lines):
        surf.blit(font_small.render(l, True, (255,255,255)), (8, 6 + i*22))
    screen.blit(surf, (10, 10))

def draw_toasts():
    now = time.time()
    for t in toasts[:]:
        elapsed = now - t["start"]
        if elapsed > t["dur"]:
            toasts.remove(t)
            continue
        alpha = int(255 * (1 - elapsed / t["dur"]))
        msg_surf = font_med.render(t["text"], True, (255,255,255))
        toast_bg = pygame.Surface((msg_surf.get_width()+20, msg_surf.get_height()+10), pygame.SRCALPHA)
        toast_bg.fill((0,0,0, int(200 * (alpha/255))))
        toast_bg.blit(msg_surf, (10,5))
        toast_bg.set_alpha(alpha)
        screen.blit(toast_bg, (RES_X//2 - toast_bg.get_width()//2, 80))

# ---------------- Establishment handling ----------------
def enter_est_from_char(ch):
    # ch is map char - lookup in est_defs
    key = ch.lower()
    if key in est_defs:
        return est_defs[key].get("type")
    return None

def draw_est_interior(est_type, menu_idx):
    img_path = os.path.join(ASSET_INT_DIR, f"{est_type}.png")
    if os.path.exists(img_path):
        img = pygame.image.load(img_path).convert()
        img = pygame.transform.smoothscale(img, (RES_X, RES_Y))
        screen.blit(img, (0, 0))
    else:
        screen.fill((30, 30, 30))

    # find menu from est_defs
    menu = None
    for k, v in est_defs.items():
        if v.get("type") == est_type:
            menu = v.get("menu", [])
            break
    if not menu:
        menu = ["(No actions available)"]

    # remove any literal 'Exit' or 'Esc' items from the menu text
    menu = [m for m in menu if "exit" not in m.lower() and "esc" not in m.lower()]

    # draw menu items
    for i, item in enumerate(menu):
        color = (255, 215, 0) if i == menu_idx else (255, 255, 255)
        text = font_med.render(f"{i + 1}) {item}", True, color)
        screen.blit(text, (80, 140 + i * 46))

    # hint line for ESC
    hint = font_small.render("Press ESC to exit", True, (200, 200, 200))
    screen.blit(hint, (80, RES_Y - 80))

def apply_est_action(est_type, idx):
    # find action text and map to effects
    # returns toast text
    global player
    menu = None
    for k,v in est_defs.items():
        if v.get("type") == est_type:
            menu = v.get("menu", [])
            break
    if not menu or idx < 0 or idx >= len(menu):
        return None
    action = menu[idx].lower()
    if "drink" in action:
        if player.get("gold",0) >= 1:
            modify_stat(player, "stamina", +5)
            modify_stat(player, "gold", -1)
            save_player(player)
            return "You drink and feel refreshed."
        else:
            return "Not enough gold to drink."
    if "eat" in action:
        if player.get("gold",0) >= 2:
            modify_stat(player, "health", +5)
            modify_stat(player, "gold", -2)
            save_player(player)
            return "You eat a satisfying meal."
        else:
            return "Not enough gold to eat."
    if "sing" in action:
        modify_stat(player, "charisma", +1)
        save_player(player)
        return "Your song raises your spirits."
    if "buy" in action and "round" in action:
        if player.get("gold",0) >= 5:
            modify_stat(player, "gold", -5)
            modify_stat(player, "charisma", +2)
            save_player(player)
            return "You buy a round — cheers!"
        else:
            return "Not enough gold for a round."
    # default placeholder
    return f"You chose: {menu[idx]}"

# ---------------- Movement helpers (stepped) ----------------
def step_forward():
    global px, py, in_est
    nx = int(px + math.cos(p_angle) * STEP_SIZE + 1e-9)
    ny = int(py + math.sin(p_angle) * STEP_SIZE + 1e-9)
    if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
        ch = world_map[ny][nx]
        if ch == ".":
            px = nx + 0.5
            py = ny + 0.5
        elif ch.lower() in est_defs:
            et = enter_est_from_char(ch)
            if et:
                return et
    return None

def step_backward():
    global px, py
    nx = int(px - math.cos(p_angle) * STEP_SIZE + 1e-9)
    ny = int(py - math.sin(p_angle) * STEP_SIZE + 1e-9)
    if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
        if world_map[ny][nx] == ".":
            px = nx + 0.5
            py = ny + 0.5

# ---------------- Main Loop ----------------
move_forward = False
move_backward = False
move_cooldown = 0.2  # seconds per tile
move_timer = 0.0

running = True
while running:
    dt = clock.tick(60) / 1000.0

    # ---- event handling
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            save_player(player)
            running = False

        elif ev.type == pygame.KEYDOWN:
            if in_est:
                if ev.key == pygame.K_ESCAPE:
                    in_est = None
                elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    idx = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2, pygame.K_4:3}[ev.key]
                    toast = apply_est_action(in_est, idx)
                    if toast:
                        add_toast(toast, duration=2.0)
            else:
                if ev.key == pygame.K_ESCAPE:
                    save_player(player)
                    running = False
                elif ev.key in (pygame.K_w, pygame.K_UP):
                    move_forward = True
                    move_timer = 0.0  # reset immediately
                    entered = step_forward()  # first step happens instantly
                    if entered:
                        in_est = entered
                elif ev.key in (pygame.K_s, pygame.K_DOWN):
                    move_backward = True
                    move_timer = 0.0
                    step_backward()
                elif ev.key in (pygame.K_a, pygame.K_LEFT):
                    p_angle -= TURN_ANGLE
                elif ev.key in (pygame.K_d, pygame.K_RIGHT):
                    p_angle += TURN_ANGLE
                elif ev.key == pygame.K_m:
                    show_map = not show_map
                elif ev.key == pygame.K_i:
                    show_inventory = not show_inventory
                elif ev.key == pygame.K_t:
                    day_mode = not day_mode

        elif ev.type == pygame.KEYUP:
            if ev.key in (pygame.K_w, pygame.K_UP):
                move_forward = False
                move_timer = 0.0
            elif ev.key in (pygame.K_s, pygame.K_DOWN):
                move_backward = False
                move_timer = 0.0

    # Continuous movement — only active while key held
    if move_forward or move_backward:
        move_timer += dt
        if move_timer >= move_cooldown:
            move_timer = 0.0
            if move_forward:
                entered = step_forward()
                if entered:
                    in_est = entered
            elif move_backward:
                step_backward()
    else:
        move_timer = 0.0



    # render
    screen.fill((0,0,0))
    if in_est:
        #draw_est_interior(in_est, est_menu_index)
        #draw_interior(screen, est_type, menu_idx, font_med, font_small, est_defs, RES_X, RES_Y)
        draw_interior(screen, in_est, est_menu_index, font_med, font_small, est_defs, RES_X, RES_Y)
        draw_toasts()
        draw_hud_stats()
    else:
        draw_sky_and_floor()
        rays = cast_rays(px, py, p_angle)
        draw_walls(rays)
        draw_hud_stats()
        draw_toasts()
        draw_compass()
        if show_map:
            draw_map_overlay()
        if show_inventory:
            draw_inventory()

    pygame.display.flip()

# save and quit
save_player(player)
pygame.quit()
