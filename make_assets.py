import pygame, os, math, random

pygame.init()
os.makedirs("assets/images", exist_ok=True)

# Utility: gradient fill
def gradient(surface, top, bottom):
    w, h = surface.get_size()
    for y in range(h):
        ratio = y / h
        r = int(top[0]*(1-ratio) + bottom[0]*ratio)
        g = int(top[1]*(1-ratio) + bottom[1]*ratio)
        b = int(top[2]*(1-ratio) + bottom[2]*ratio)
        pygame.draw.line(surface, (r,g,b), (0,y), (w,y))

# Wall / floor generators
def make_floor():
    surf = pygame.Surface((64,64))
    for y in range(64):
        for x in range(64):
            c = 100 + int(20*math.sin(x/4)+10*math.cos(y/4))
            surf.set_at((x,y),(c,c,c))
    pygame.image.save(surf, "assets/images/floor.png")

def make_wall_stone():
    surf = pygame.Surface((64,64))
    gradient(surf, (90,90,100), (60,60,70))
    for _ in range(100):
        x, y = random.randint(0,63), random.randint(0,63)
        surf.set_at((x,y), (50,50,50))
    pygame.image.save(surf, "assets/images/wall_stone.png")

def make_wall_wood():
    surf = pygame.Surface((64,64))
    gradient(surf, (120,90,60), (90,60,40))
    for _ in range(10):
        x = random.randint(0,63)
        pygame.draw.line(surf, (80,60,40), (x,0), (x,63), 1)
    pygame.image.save(surf, "assets/images/wall_wood.png")

def make_wall_shop():
    surf = pygame.Surface((64,64))
    gradient(surf, (160,160,180), (120,120,140))
    pygame.draw.rect(surf, (200,200,210), (8,8,48,48), 1)
    pygame.image.save(surf, "assets/images/wall_shop.png")

def make_door():
    surf = pygame.Surface((64,64))
    gradient(surf, (70,50,30), (40,30,20))
    pygame.draw.rect(surf, (90,70,50), (24,16,16,32))
    pygame.image.save(surf, "assets/images/door.png")

def make_sky():
    surf = pygame.Surface((64,64))
    gradient(surf, (100,150,220), (180,210,255))
    pygame.image.save(surf, "assets/images/sky_day.png")

    surf2 = pygame.Surface((64,64))
    gradient(surf2, (10,10,30), (40,40,60))
    pygame.image.save(surf2, "assets/images/sky_night.png")

if __name__ == "__main__":
    make_floor()
    make_wall_stone()
    make_wall_wood()
    make_wall_shop()
    make_door()
    make_sky()
    print("✅ Generated base textures in assets/images/")
