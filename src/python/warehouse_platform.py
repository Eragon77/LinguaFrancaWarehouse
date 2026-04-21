from slot import Slot


class Platform:
    def __init__(self):
        # Stores the current vertical and horizontal position of the platform.
        self.curr_x = 0.0
        self.curr_y = 0.0

        # Holds the Tray object if the platform is carrying one, otherwise None.
        self.held_tray = None

        self.speed_y = 0.2  # Movement speed along the Y-axis
        self.extract_speed = 0.15  # Movement speed for X-axis (extraction)

    def is_holding_tray(self):
        """Checks if the platform is currently holding a tray."""
        return self.held_tray is not None

    def pick_up_from(self, slot: Slot):
        """
        Attempts to pick up a tray from a given slot.
        This is an instantaneous state change.
        Returns False if the platform is already full or the slot is empty.
        """
        if self.is_holding_tray():
            return False  # Platform is already holding something

        try:
            tray_to_pick = slot.remove_tray()
            self.held_tray = tray_to_pick
            return True
        except ValueError:
            return False

    def place_into(self, slot: Slot):
        """
        Attempts to place the held tray into a given slot.
        This is an instantaneous state change.
        Returns False if the platform is empty or the slot is full.
        """
        if not self.is_holding_tray():
            return False  # Platform is empty

        try:
            slot.add_tray(self.held_tray)
            self.held_tray = None
            return True
        except ValueError:
            return False

    def update_y_position(self, target_y: float):
        """
        Moves the platform towards target_y by one time-step increment.
        Assuming LF calls this every 50ms (0.05 seconds).
        """
        dt = 0.05
        step = self.speed_y * dt

        if abs(target_y - self.curr_y) <= step:
            self.curr_y = target_y
        elif target_y > self.curr_y:
            self.curr_y += step
        else:
            self.curr_y -= step

        return True

    def update_x_position(self, target_x: float):
        """
        Moves the platform towards target_x by one time-step increment.
        Assuming LF calls this every 50ms (0.05 seconds).
        """
        dt = 0.05  # 50 msec
        step = self.extract_speed * dt

        if abs(target_x - self.curr_x) <= step:
            self.curr_x = target_x
        elif target_x > self.curr_x:
            self.curr_x += step
        else:
            self.curr_x -= step

        return True
