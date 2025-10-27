from Tray import Tray
class Slot:
    def __init__(self,position_id:str,x:float,y:float):
        self.x=x
        self.y=y
        self.position_id=position_id
        self.length = 2.134
        self.height = 0.16725
        self.width = 0.835

        self.tray=None

    def __repr__(self):
        status = "Full" if self.tray else "Empty"
        return f"<Slot ID: '{self.position_id}' ({status})>"


    def add_tray(self,tray_to_add:Tray):
            if self.tray is not None:
                return False; 
            self.tray=tray_to_add
        #TODO: funzione per stampare info sul tray
            return True
     
    def remove_tray(self):
         if self.tray is None:
             return None
         tray_removed=self.tray
         self.tray=None
         return tray_removed

