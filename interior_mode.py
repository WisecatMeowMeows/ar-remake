# interior_mode.py
import os
import pygame

ASSET_INT_DIR = os.path.join("assets", "interiors")

def draw_interior(screen, est_type, menu_idx, font_med, font_small, est_defs, res_x, res_y):
    """
    Draw an interior scene with a legible, semi-transparent menu box.

    Parameters (must match your call site):
      - screen: pygame display surface
      - est_type: string, establishment type (e.g. "tavern", "shop")
      - menu_idx: currently highlighted menu index (int)
      - font_med: pygame Font to render menu items
      - font_small: pygame Font for hint text
      - est_defs: dict loaded from data/establishments.json
      - res_x, res_y: screen resolution ints
    """
    # Draw background interior image if present, otherwise dark background
    img_path = os.path.join(ASSET_INT_DIR, f"{est_type}.png")
    if os.path.exists(img_path):
        try:
            img = pygame.image.load(img_path).convert()
            img = pygame.transform.smoothscale(img, (res_x, res_y))
            screen.blit(img, (0, 0))
        except Exception:
            screen.fill((30, 30, 30))
    else:
        screen.fill((30, 30, 30))

    # Locate the menu for this interior type
    menu = None
    for k, v in est_defs.items():
        if v.get("type") == est_type:
            menu = v.get("menu", [])
            break
    if not menu:
        menu = ["(No actions available)"]

    # Filter out any literal Exit/Esc items so only numbered actions remain
    menu = [m for m in menu if "exit" not in m.lower() and "esc" not in m.lower()]

    # --- Menu box geometry ---
    box_w = min(600, res_x - 160)            # don't exceed screen
    box_h = max(120, 60 + len(menu) * 46)    # room for items
    box_x = 60                               # distance from left edge
    box_y = 120                              # distance from top

    # Draw semi-transparent rounded-ish rectangle as menu background
    overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))  # mostly opaque dark background for legibility
    # subtle border
    pygame.draw.rect(overlay, (220, 220, 220, 30), overlay.get_rect(), 2)
    screen.blit(overlay, (box_x, box_y))

    # Draw menu items inside the box
    item_x = box_x + 24
    item_y = box_y + 16
    for i, item in enumerate(menu):
        color = (255, 215, 0) if i == menu_idx else (255, 255, 255)
        text_surf = font_med.render(f"{i+1}) {item}", True, color)
        screen.blit(text_surf, (item_x, item_y + i * 46))

    # Draw ESC hint at the bottom of the menu box (inside the box)
    hint_text = "Press ESC to exit"
    hint_surf = font_small.render(hint_text, True, (200, 200, 200))
    hint_x = box_x + 16
    hint_y = box_y + box_h - 34
    screen.blit(hint_surf, (hint_x, hint_y))

    # Optionally: small title of establishment at top of box
    title = est_type.replace("_", " ").title()
    title_surf = font_med.render(title, True, (240,240,240))
    # center title above the menu
    tx = box_x + (box_w - title_surf.get_width()) // 2
    ty = box_y - 36
    screen.blit(title_surf, (tx, ty))



""" old version
import os
import pygame

ASSET_INT_DIR = os.path.join("assets", "interiors")

def draw_interior(screen, est_type, menu_idx, font_med, font_small, est_defs, res_x, res_y):
    #Draw the establishment interior and menu with a translucent background overlay.
    
    # Load background image if available
    img_path = os.path.join(ASSET_INT_DIR, f"{est_type}.png")
    if os.path.exists(img_path):
        img = pygame.image.load(img_path).convert()
        img = pygame.transform.smoothscale(img, (res_x, res_y))
        screen.blit(img, (0, 0))
    else:
        screen.fill((30, 30, 30))

    # Find menu items for this establishment type
    menu = None
    for k, v in est_defs.items():
        if v.get("type") == est_type:
            menu = v.get("menu", [])
            break
    if not menu:
        menu = ["(No actions available)"]

    # Remove "exit"/"esc" text entries
    menu = [m for m in menu if "exit" not in m.lower() and "esc" not in m.lower()]

    # Create translucent background overlay for the menu
    overlay = pygame.Surface((res_x, res_y), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Draw menu options
    for i, item in enumerate(menu):
        color = (255, 215, 0) if i == menu_idx else (255, 255, 255)
        text = font_med.render(f"{i + 1}) {item}", True, color)
        screen.blit(text, (80, 140 + i * 46))

    # Draw ESC hint line
    hint = font_small.render("Press ESC to exit", True, (200, 200, 200))
    screen.blit(hint, (80, res_y - 80))

"""