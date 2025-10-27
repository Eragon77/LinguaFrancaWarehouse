from Tray import Tray
from Slot import Slot
class Platform:
    def __init__(self):
        self.curr_y=0.0
        self.speed_y=1.0
        self.extract_speed=0.5

        self.held_tray=None

    def is_holding_tray(self):
        return self.held_tray is not None
    
    def pick_up_from(self, slot:Slot):
        if self.is_holding_tray():
            return False
        tray_to_pick=slot.remove_tray()

        if tray_to_pick is None:
            print("Error: slot was empty")
            return False
        
        self.held_tray=tray_to_pick
        return True
    
    def place_into(self,slot:Slot):
        if not self.is_holding_tray():
            print("No tray to place")
            return False
        
        done=slot.add_tray(self.held_tray)

        if not done:
            print("Can't put into slot")
            return False
        
        self.held_tray=None
        return True
    
    #Tempo per arrivare al cassetto
    def calculate_y_move_time(self,target_y):
        d=abs(target_y-self.curr_y)
        t=d/self.speed_y
        self.curr_y=target_y
        return t
    
    #Calcola tempo di estrazione cassetto
    def calculate_x_move_time(self,target_x):
        d=abs(target_x)
        t=d/self.extract_speed
        return t