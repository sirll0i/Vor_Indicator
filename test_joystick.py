import pygame
import sys

print("Testing joystick detection...")
print("=" * 50)

# Initialize pygame and joystick module
pygame.init()
pygame.joystick.init()

# Check for joysticks
joystick_count = pygame.joystick.get_count()
print(f"Number of joysticks detected: {joystick_count}")

if joystick_count == 0:
    print("\nNo joysticks detected!")
    print("\nTroubleshooting tips:")
    print("1. Make sure your controller is plugged in")
    print("2. Check Windows Device Manager for controller")
    print("3. Try a different USB port")
    print("4. Install controller drivers if needed")
else:
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        
        print(f"\nJoystick {i}:")
        print(f"  Name: {joystick.get_name()}")
        print(f"  Number of axes: {joystick.get_numaxes()}")
        print(f"  Number of buttons: {joystick.get_numbuttons()}")
        print(f"  Number of hats: {joystick.get_numhats()}")

print("\nPress any key to exit...")
input()
