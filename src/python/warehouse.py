from warehouse_platform import Platform
from slot import Slot
from tray import Tray

class Warehouse:
    X_LEFT = -0.835
    X_RIGHT = 0.835
    SLOT_HEIGHT = 0.16725
    NUM_ROWS = 20 

    def __init__(self):
        # --- Physical Components ---
        self.platform = Platform()
        self.storage_slots = [] 
        self.queued_slots = []
        self.in_view_slot = None 

        # --- Controller State ---
        # A flag the LF controller will use to see if a task is running.
        self.is_busy = False

        # --- Initialize all slot positions ---
        for i in range(self.NUM_ROWS):
            y_pos = i * self.SLOT_HEIGHT

            # Left Column (Storage)
            left_id = f"storage_L_{i}"
            left_slot = Slot(position_id=left_id, x=self.X_LEFT, y=y_pos)
            self.storage_slots.append(left_slot)

            # Right Column (Mixed)
            if i < 3: # Rows 0-2 (Queue)
                slot_id = f"queue_{i}"
                new_slot = Slot(position_id=slot_id, x=self.X_RIGHT, y=y_pos)
                self.queued_slots.append(new_slot)
            
            elif i == 3: # Row 3 (In View)
                slot_id = "in_view"
                new_slot = Slot(position_id=slot_id, x=self.X_RIGHT, y=y_pos)
                self.in_view_slot = new_slot
            
            else: # Rows 4-9 (Storage)
                slot_id = f"storage_R_{i}"
                new_slot = Slot(position_id=slot_id, x=self.X_RIGHT, y=y_pos)
                self.storage_slots.append(new_slot)


        try:
            tray1 = Tray(weight=3.5)
            self.get_slot_by_id("storage_L_0").add_tray(tray1)
            

            tray2 = Tray(weight=2.9)
            self.get_slot_by_id("storage_L_5").add_tray(tray2)

            tray3=Tray(weight=2.6)
            self.get_slot_by_id("storage_R_7").add_tray(tray3)

            print("Initialized Warehouse with sample trays.")
        
        except AttributeError as e:
            print(f"Error during warehouse initialization: {e}")


    def _get_all_slots(self):
        """Helper to return one single list of all slots."""
        # Combines all slot lists into one for easy searching
        all_slots = self.storage_slots + self.queued_slots
        if self.in_view_slot:
            all_slots.append(self.in_view_slot)
        return all_slots

    def get_slot_by_id(self, slot_id: str):
        """Finds and returns a slot object from its ID string."""
        for slot in self.get_all_slots():
            if slot.position_id == slot_id:
                return slot
        return None # Controller must handle if ID is not found

    # --- State Methods for the Controller ---

    def is_ready(self):
        """Allows the LF controller to check if the warehouse is busy."""
        return not self.is_busy

    def set_busy(self):
        """Allows the LF controller to mark the warehouse as busy."""
        self.is_busy = True

    def set_idle(self):
        """Allows the LF controller to mark the warehouse as ready."""
        self.is_busy = False
    
    def find_empty_storage_slot(self):
        """
        Finds the first available empty slot in the storage.
        Returns None if no empty slot is found.
        """
        for slot in self.storage_slots:
            if slot.tray is None:
                return slot
        
        return None
    
    def get_slot_by_tray_id(self, tray_id: str):
        """
        Finds and returns the slot containing the tray with the given ID.
        Returns None if no such tray is found.
        """
        for slot in self._get_all_slots():
            if slot.tray and slot.tray.tray_id == tray_id:
                return slot
        
        return None
    
    def get_empty_queue_slot(self)->Slot | None:
        """
        Checks if all the queue slots are empty.
        If they are, returns the first queue slot.
        """
        for slot in self.queued_slots:
            if slot.tray is not None:
                return None
        return self.queued_slots[0]
    
    def get_occupied_queue_slot(self)->Slot | None:
        """
        Returns the first occupied queue slot.
        If none are occupied, returns None.
        """
        for slot in self.queued_slots:
            if slot.tray is not None:
                return slot
        return None
    