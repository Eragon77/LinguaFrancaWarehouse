from Platform import Platform
from Slot import Slot
from Tray import Tray

class Warehouse:
    def __init__(self):
        X_LEFT = -0.835
        X_RIGHT = 0.835
        SLOT_HEIGHT = 0.16725
        NUM_ROWS = 10 

        self.storage_slots = [] 
        self.queued_slots = []
        self.in_view_slot = None 

        for i in range(NUM_ROWS):
            y_pos = i * SLOT_HEIGHT

            # Colonna 1 (Sinistra): Solo Storage
            left_id = f"storage_L_{i}"
            left_slot = Slot(position_id=left_id, x=X_LEFT, y=y_pos)
            self.storage_slots.append(left_slot)

            # Colonna 2 (Destra): Queue+Storage
    
            if i < 3: # Righe 0->2
                slot_id = f"queue_{i}"
                new_slot = Slot(position_id=slot_id, x=X_RIGHT, y=y_pos)
                self.queued_slots.append(new_slot)
            
            elif i == 3: # Riga 3
                slot_id = "in_view"
                new_slot = Slot(position_id=slot_id, x=X_RIGHT, y=y_pos)
                self.in_view_slot = new_slot
            
            else: # Righe 4->9
                slot_id = f"storage_R_{i}"
                new_slot = Slot(position_id=slot_id, x=X_RIGHT, y=y_pos)
                self.storage_slots.append(new_slot)