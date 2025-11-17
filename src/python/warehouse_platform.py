from tray import Tray
from slot import Slot

class Platform:
    def __init__(self):
        # --- State: Position ---
        # Stores the current vertical and horizontal position of the platform.
        self.curr_x = 0.0
        self.curr_y = 0.0

        # --- State: Contents ---
        # Holds the Tray object if the platform is carrying one, otherwise None.
        self.held_tray = None

        # --- Physical Constants ---
        # The controller (Lingua Franca) will read these values 
        # to calculate movement times.
        self.speed_y = 0.3          # Movement speed along the Y-axis
        self.extract_speed = 0.15    # Movement speed for X-axis (extraction)

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
        
        tray_to_pick = slot.remove_tray()

        if tray_to_pick is None:
            return False  # Slot was empty
        
        self.held_tray = tray_to_pick
        return True
    
    def place_into(self, slot: Slot):
        """
        Attempts to place the held tray into a given slot.
        This is an instantaneous state change.
        Returns False if the platform is empty or the slot is full.
        """
        if not self.is_holding_tray():
            return False  # Platform is empty
        
        done = slot.add_tray(self.held_tray)

        if not done:
            return False  # Slot was full
        
        self.held_tray = None
        return True
    
    def update_y_position(self, new_y: float):
        """
        A setter for the controller to update the platform's
        position after a move action is complete.
        """
        self.curr_y = new_y

    def update_x_position(self, new_x: float):
        """
        A setter for the controller to update the platform's
        position after an extract action is complete.
        """
        self.curr_x = new_x