from warehouse_platform import Platform
from slot import Slot
from tray import Tray

class Warehouse:
    X_LEFT = -0.7
    X_RIGHT = 0.7
    SLOT_HEIGHT = 0.16725
    NUM_ROWS = 20 

    def __init__(self):
        Tray._next_id = 1 

            
        # --- Physical Components ---
        self.platform = Platform()
        self.storage_slots = [] 
        self.queued_slots = []
        self.in_view_slot = None 


        # --- Initialize all slot positions ---
        for i in range(self.NUM_ROWS):
            y_pos = i * self.SLOT_HEIGHT

            # Left Column (Storage)
            left_id = f"storage_L_{i}"
            # Added slot_type="storage"
            left_slot = Slot(slot_id=left_id, x=self.X_LEFT, y=y_pos, slot_type="storage")
            self.storage_slots.append(left_slot)

            # Right Column (Mixed)
            if i < 3: # Rows 0-2 (Queue)
                slot_id = f"queue_{i}"
                # Added slot_type="queue"
                new_slot = Slot(slot_id=slot_id, x=self.X_RIGHT, y=y_pos, slot_type="queue")
                self.queued_slots.append(new_slot)
            
            elif i == 3: # Row 3 (Bay)
                slot_id = "in_view"
                # Added slot_type="bay"
                new_slot = Slot(slot_id=slot_id, x=self.X_RIGHT, y=y_pos, slot_type="bay")
                self.in_view_slot = new_slot
            
            else: # Rows 4-19 (Storage)
                slot_id = f"storage_R_{i}"
                # Added slot_type="storage"
                new_slot = Slot(slot_id=slot_id, x=self.X_RIGHT, y=y_pos, slot_type="storage")
                self.storage_slots.append(new_slot)

        try:
            # --- Initialize Trays: They get sequential IDs 1, 2, 3, 4, 5 ecc ecc ---
            
            tray1 = Tray(weight=3.5)
            self.get_slot_by_id("storage_L_0").add_tray(tray1)
            
            tray2 = Tray(weight=2.9)
            self.get_slot_by_id("storage_L_5").add_tray(tray2)

            tray3=Tray(weight=2.6)
            self.get_slot_by_id("storage_R_7").add_tray(tray3)
            
            tray4 = Tray(weight=3.0)
            self.get_slot_by_id("storage_L_10").add_tray(tray4)

            tray5 = Tray(weight=3.1)
            self.get_slot_by_id("storage_R_15").add_tray(tray5)

            tray6 = Tray(weight=2.0)
            self.get_slot_by_id("queue_0").add_tray(tray6)
            
            print("Initialized Warehouse with sample trays.")
        
        except AttributeError as e:
            print(f"Error during warehouse initialization: {e}")

    def has_tray(self, tray_id: int | str) -> bool:
        """Check whether a tray with the given ID exists anywhere in the warehouse."""
        tid = int(tray_id) 
        for slot in self._get_all_slots():
            if slot.tray and slot.tray.tray_id == tid:
                return True
        return False

    def get_slot_at(self, x: float, y: float) -> Slot | None:
        for slot in self._get_all_slots():
            if abs(slot.x - x) < 0.01 and abs(slot.y - y) < 0.01:
                return slot
        return None

    def _get_all_slots(self):
        """Helper to return one single list of all slots."""
        # Combines all slot lists into one for easy searching
        all_slots = self.storage_slots + self.queued_slots
        if self.in_view_slot:
            all_slots.append(self.in_view_slot)
        return all_slots

    def get_slot_by_id(self, slot_id: str):
        """Finds and returns a slot object from its ID string."""
        for slot in self._get_all_slots():
            if slot.slot_id == slot_id:
                return slot
        return None # Controller must handle if ID is not found

    # --- State Methods for the Controller ---
    
    def get_occupied_queue_slot(self)->Slot | None:
        """
        Returns the first occupied queue slot.
        If none are occupied, returns None.
        """
        for slot in self.queued_slots:
            if slot.tray is not None:
                return slot
        return None
        
    def get_occupied_bay_slot(self)->Slot | None:
        """
        Returns the occupied bay slot (in_view_slot) if a tray is present.
        Returns None otherwise.
        This is the source slot for SEND_BACK_TRAY.
        """
        if self.in_view_slot and self.in_view_slot.tray is not None:
            return self.in_view_slot
        return None

    def get_tray_bay_slot(self):
        """
        Returns the slot used for extracting trays to the bay (the 'in_view' slot).
        This slot is where the platform leaves the tray for visual inspection or manual removal.
        """
        return self.in_view_slot
    

    @property
    def tray_in_bay(self) -> int:
        """
        Returns the ID of the tray currently in the bay, or 0 if it's empty.
        """
        if self.in_view_slot and self.in_view_slot.tray:
            return self.in_view_slot.tray.tray_id
        return 0
    