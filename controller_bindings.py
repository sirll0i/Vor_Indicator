import pygame

class ControllerHandler:
    """
    Handles polling a single controller (joystick/gamepad) and maps buttons,
    hats (D-pad), and axis changes to user-defined callback functions.

    button_map: dict {button_index: callback}
    axis_callback: function(axes_list)
    hat_callback: function((x, y))
    """
    def __init__(self, button_map=None, axis_callback=None, hat_callback=None):
        pygame.init()
        pygame.joystick.init()
        self.joystick = None

        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"[Controller] Connected: {self.joystick.get_name()}")
        else:
            print("[Controller] No controller detected.")

        self.button_map = button_map or {}
        self.axis_callback = axis_callback
        self.hat_callback = hat_callback

        self.last_button_states = {}
        self.last_hat_state = (0, 0)

    def poll(self):
        """
        Should be called frequently (e.g. from a GUI timer/loop).
        Detects button press (rising edge), hat (D-pad) changes, and always returns all axes.
        """
        if not self.joystick:
            return

        pygame.event.pump()  # Update joystick state

        # --- BUTTONS ---
        for btn_idx, callback in self.button_map.items():
            try:
                pressed = self.joystick.get_button(btn_idx)
            except IndexError:
                continue
            prev = self.last_button_states.get(btn_idx, False)
            # Edge detect: call callback ONLY when button transitions up -> down
            if pressed and not prev:
                if callable(callback):
                    callback()
            self.last_button_states[btn_idx] = pressed

        # --- HAT (D-Pad) ---
        if self.hat_callback and self.joystick.get_numhats() > 0:
            hat = self.joystick.get_hat(0)
            if hat != self.last_hat_state:
                if callable(self.hat_callback):
                    self.hat_callback(hat)
                self.last_hat_state = hat

        # --- AXES ---
        if self.axis_callback:
            axes = [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
            self.axis_callback(axes)
