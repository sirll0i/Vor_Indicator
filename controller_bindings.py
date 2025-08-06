
import pygame

class ControllerHandler:
    def __init__(self, button_map=None, axis_callback=None, hat_callback=None):
        pygame.init()
        pygame.joystick.init()
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller connected: {self.joystick.get_name()}")
        else:
            print("No controller detected.")
        self.button_map = button_map or {}
        self.axis_callback = axis_callback
        self.hat_callback = hat_callback
        self.last_button_states = {}

    def poll(self):
        if not self.joystick:
            return
        pygame.event.pump()
        # Buttons
        for btn_idx, func in self.button_map.items():
            pressed = self.joystick.get_button(btn_idx)
            prev = self.last_button_states.get(btn_idx, False)
            if pressed and not prev:
                func()
            self.last_button_states[btn_idx] = pressed
        # Axes
        if self.axis_callback:
            axes = [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
            self.axis_callback(axes)
        # Hat
        if self.hat_callback and self.joystick.get_numhats() > 0:
            hat = self.joystick.get_hat(0)
            self.hat_callback(hat)
