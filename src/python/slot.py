from tray import Tray


class Slot:
    def __init__(self, slot_id: str, x: float, y: float, slot_type: str = "storage"):
        # Unique coordinates and identifier for this specific slot.
        self.x = x
        self.y = y
        self.slot_id = slot_id
        self.slot_type = slot_type

        # Defines the physical size of the slot
        self.length = 1.62
        self.height = 0.16725
        self.width = 0.7

        # Holds the Tray object if occupied, otherwise None.
        self.tray = None

    def __repr__(self):
        status = "Full" if self.tray else "Empty"
        return f"<Slot ID: '{self.slot_id}' ({status})>"

    def add_tray(self, tray_to_add: Tray):
        """
        Attempts to place a Tray into this slot.
        Returns False if the slot is already occupied.
        """
        if self.tray is not None:
            raise ValueError(
                f"Slot {self.slot_id} is already occupied by Tray {self.tray.tray_id}"
            )  # Slot is full

        self.tray = tray_to_add
        return True

    def remove_tray(self):
        """
        Attempts to remove and return the Tray from this slot.
        Returns None if the slot is already empty.
        """
        if self.tray is None:
            raise ValueError(f"Slot {self.slot_id} is already empty.")

        tray_removed = self.tray
        self.tray = None
        return tray_removed
