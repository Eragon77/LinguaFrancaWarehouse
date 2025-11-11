from tray import Tray
class Slot:
    def __init__(self, position_id: str, x: float, y: float):
        # --- State: Location & ID ---
        # Unique coordinates and identifier for this specific slot.
        self.x = x
        self.y = y
        self.position_id = position_id
        
        # --- State: Fixed Physical Dimensions ---
        # Defines the physical size of the slot itself.
        self.length = 2.134
        self.height = 0.16725
        self.width = 0.835

        # --- State: Dynamic Contents ---
        # Holds the Tray object if occupied, otherwise None.
        self.tray = None

    def __repr__(self):
        #shows the slot's ID and status.
        status = "Full" if self.tray else "Empty"
        return f"<Slot ID: '{self.position_id}' ({status})>"

    def add_tray(self, tray_to_add: Tray):
        """
        Attempts to place a Tray into this slot.
        Returns False if the slot is already occupied.
        """
        if self.tray is not None:
            return False  # Slot is full
        
        self.tray = tray_to_add
        # TODO: repr tray
        return True
    
    def remove_tray(self):
        """
        Attempts to remove and return the Tray from this slot.
        Returns None if the slot is already empty.
        """
        if self.tray is None:
            return None  #  Slot is empty
        
        tray_removed = self.tray
        self.tray = None
        return tray_removed