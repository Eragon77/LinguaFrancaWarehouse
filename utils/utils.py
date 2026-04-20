import yaml
import os

def load_commands(file_name: str):
    """
    Loads a list of YAML commands.
    """
    
    # 1. Finds path of this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Build path for YAML file
    file_path = os.path.join(current_dir, file_name)

    print(f"[UTILS] Attempting to load commands from: {file_path}")

    try:
        with open(file_path, 'r') as f:
            commands = yaml.safe_load(f)
            
            if commands is None:
                print("[UTILS] WARNING: Command file is empty.")
                return []
                
            commands.reverse()
            return commands
            
    except FileNotFoundError:
        print(f"[UTILS] ERROR: Command file not found at {file_path}")
        return []
    except Exception as e:
        print(f"[UTILS] ERROR: Failed to read or parse YAML file: {e}")
        return []