class Tray:
    # --- System Counter for Unique ID ---
    _next_id = 1

    # --- Physical Constants ---
    MIN_W = 2.960  # The weight of an empty tray.
    MAX_W = 4.960  # The maximum weight of a fully loaded tray.

    def __init__(self, weight=None):
        # 1. Assign unique ID and increment the counter
        self.tray_id = Tray._next_id
        Tray._next_id += 1

        # --- Fixed Physical Dimensions ---
        self.length = 1.62
        self.height = 0.16725
        self.width = 0.7

        self.weight = weight if weight is not None else self.MIN_W

    @property
    def is_full(self) -> bool:
        """A tray is considered full if its weight is greater than the empty weight + a small margin of error."""
        return self.weight > (self.MIN_W + 0.01)

    # --- (Getters) ---
    def get_tray_id(self):
        return self.tray_id

    def get_weight(self):
        return self.weight

    def get_length(self):
        return self.length

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def __repr__(self):
        """String representation of the tray"""
        return f"<Tray ID: {self.tray_id}, Weight: {self.weight:.3f}>"
