import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Set window size and title
size = (500, 500)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Compass with Airplane Needle")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)

# Font setup
font = pygame.font.SysFont("Arial", 18)
font_big = pygame.font.SysFont("Arial", 28, bold=True)

# Load airplane image
# ✅ Make sure airplane.png is in the same folder and points up
airplane_img = pygame.image.load("airplane.png").convert_alpha()
airplane_img = pygame.transform.smoothscale(airplane_img, (660, 660))

# Clock and rotation angle
clock = pygame.time.Clock()
angle = 0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear screen
    screen.fill(BLACK)

    # Center of compass
    center = (size[0] // 2, size[1] // 2)
    compass_radius = 200

    # Draw rotating compass rose
    for deg in range(0, 360, 10):
        rotated_deg = deg + angle
        rad = math.radians(rotated_deg)

        # Tick positions
        x1 = center[0] + math.cos(rad) * (compass_radius - 10)
        y1 = center[1] + math.sin(rad) * (compass_radius - 10)
        x2 = center[0] + math.cos(rad) * compass_radius
        y2 = center[1] + math.sin(rad) * compass_radius

        pygame.draw.line(screen, WHITE, (x1, y1), (x2, y2), 2)

        # Degree labels every 30°
        if deg % 30 == 0:
            label = str(deg)
            text_surface = font.render(label, True, WHITE)
            tx = center[0] + math.cos(rad) * (compass_radius - 30) - text_surface.get_width() / 2
            ty = center[1] + math.sin(rad) * (compass_radius - 30) - text_surface.get_height() / 2
            screen.blit(text_surface, (tx, ty))

    # Draw NEWS (cardinal directions)
    cardinal_dirs = [("N", 0), ("E", 90), ("S", 180), ("W", 270)]
    for label, deg in cardinal_dirs:
        rotated_deg = deg + angle
        rad = math.radians(rotated_deg)
        text_surface = font_big.render(label, True, WHITE)
        tx = center[0] + math.cos(rad) * (compass_radius - 50) - text_surface.get_width() / 2
        ty = center[1] + math.sin(rad) * (compass_radius - 50) - text_surface.get_height() / 2
        screen.blit(text_surface, (tx, ty))

    # Draw outer compass circle
    pygame.draw.circle(screen, GRAY, center, compass_radius, 2)

    # Draw fixed airplane needle (PNG image)
    airplane_rect = airplane_img.get_rect(center=center)
    screen.blit(airplane_img, airplane_rect)

    # Refresh display
    pygame.display.flip()

    # Rotate compass
    angle += 1
    angle %= 360

    clock.tick(30)

pygame.quit()
sys.exit()

