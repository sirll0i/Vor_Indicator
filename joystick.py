import pygame
import sys

def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick detected. Please connect your controller and restart.")
        sys.exit()

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Controller detected: {joystick.get_name()}")

    num_buttons = joystick.get_numbuttons()
    num_axes = joystick.get_numaxes()
    num_hats = joystick.get_numhats()

    print(f"\n[Info] Buttons: {num_buttons} | Axes: {num_axes} | D-Pads/Hats: {num_hats}\n")
    print("Press ESC or close the window to exit.\n")

    last_buttons = [0] * num_buttons
    last_axes = [0.0] * num_axes
    last_hats = [(0, 0)] * num_hats

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        # Check button changes
        for i in range(num_buttons):
            val = joystick.get_button(i)
            if val != last_buttons[i]:
                state = "PRESSED" if val else "RELEASED"
                print(f"[Button {i}] {state}")
                last_buttons[i] = val

        # Check axis changes (thresholded for noise)
        for i in range(num_axes):
            val = joystick.get_axis(i)
            if abs(val - last_axes[i]) > 0.05:
                print(f"[Axis {i}] Value: {val:.2f}")
                last_axes[i] = val

        # Check hat (D-Pad) changes
        for i in range(num_hats):
            val = joystick.get_hat(i)
            if val != last_hats[i]:
                print(f"[D-Pad/Hat {i}] Value: {val}")
                last_hats[i] = val

        clock.tick(30)

if __name__ == "__main__":
    main()
