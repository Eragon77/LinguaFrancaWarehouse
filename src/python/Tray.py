class Tray:
    MIN_W = 2.960
    MAX_W = 4.960

    def __init__(self, weight=None):
        self.length = 2.134
        self.height = 0.16725
        self.width = 0.83
        
        self.weight = self.MIN_W 

        if self.weight_ok(weight):
            self.weight = weight

    def weight_ok(self, weight):
        if weight is None:
            return False
        return self.MIN_W <= weight <= self.MAX_W
