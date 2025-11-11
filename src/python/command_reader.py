import yaml
import os

def load_commands(file_name: str):
    """
    Loads a list of commands from a YAML file located in the /utils/ directory.
    """
    
    # 1. Find the path of this file (utils.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Go up two levels to find the project root
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # 3. Create the full path to the YAML file in the /utils/ folder
    file_path = os.path.join(project_root, "utils", file_name)

    print(f"Attempting to load commands from: {file_path}")

    try:
        with open(file_path, 'r') as f:
            commands = yaml.safe_load(f) # Use the yaml library
            
            if commands is None:
                print("WARNING: Command file is empty.")
                return []
                
            # Reverse the list. This allows using .pop()
            # to read commands in the order they appear in the file.
            commands.reverse()
            return commands
            
    except FileNotFoundError:
        print(f"ERROR: Command file not found at {file_path}")
        return []
    except Exception as e:
        print(f"ERROR: Failed to read or parse YAML file: {e}")
        return []