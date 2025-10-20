import pygame, os, random, math

pygame.init()
os.makedirs("assets/interiors", exist_ok=True)

WIDTH, HEIGHT = 640, 360

def painterly_bg(top, bottom, texture=True):
    """Create a subtle painterly gradient background."""
    surf = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(top[0]*(1-ratio) + bottom[0]*ratio)
        g = int(top[1]*(1-ratio) + bottom[1]*ratio)
        b = int(top[2]*(1-ratio) + bottom[2]*ratio)
        pygame.draw.line(surf, (r,g,b), (0,y), (WIDTH,y))
    if texture:
        for _ in range(1000):
            x, y = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1)
            shade = random.randint(-10, 10)
            c = surf.get_at((x,y))
            nc = (max(0,min(255,c.r+shade)), max(0,min(255,c.g+shade)), max(0,min(255,c.b+shade)))
            surf.set_at((x,y), nc)
    return surf

def add_text(surf, text):
    """Draw centered title text."""
    font = pygame.font.SysFont("DejaVuSans", 48, bold=True)
    text_surf = font.render(text, True, (255,255,255))
    rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
    surf.blit(text_surf, rect)
    return surf

def save_scene(name, top, bottom):
    surf = painterly_bg(top, bottom)
    add_text(surf, name.title())
    pygame.image.save(surf, f"assets/interiors/{name}.png")

if __name__ == "__main__":
    scenes = {
        "tavern": ((90,50,40), (40,20,15)),
        "shop": ((120,120,130), (60,60,70)),
        "bank": ((50,80,50), (20,40,20)),
        "guild": ((100,70,40), (40,30,20)),
        "healer": ((180,180,200), (100,100,130)),
        "dungeon": ((30,30,40), (10,10,15))
    }

    for name, colors in scenes.items():
        save_scene(name, colors[0], colors[1])

    print("✅ Painterly interiors created in assets/interiors/")
