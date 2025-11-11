class Tray:
    # --- Physical Constants ---
    # These class attributes define the valid physical range for a tray's weight.
    # The controller (Lingua Franca) is expected to use these constants for validation.
    
    MIN_W = 2.960  # The weight of an empty tray.
    MAX_W = 4.960  # The maximum weight of a fully loaded tray.

    def __init__(self, weight=None):
        # --- Fixed Physical Dimensions ---
        # These dimensions are constant for every instance of a tray.
        self.length = 2.134
        self.height = 0.16725
        self.width = 0.83
        
        # --- State ---
        # Sets the tray's initial weight.
        # If no specific weight is provided,
        # it defaults to the minimum (empty) weight.
        self.weight = weight if weight is not None else self.MIN_W
    
    # --- (Getters) ---

    def get_weight(self):
        return self.weight
    
    def get_length(self):
        return self.length

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width