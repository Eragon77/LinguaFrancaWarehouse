import os
from machine_data_model.data_model import DataModel

def test_model():
    # Setup paths
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(root_dir, "models", "Warehouse.yml")
    
    if not os.path.exists(yaml_path):
        print(f"File not found: {yaml_path}")
        return

    try:
        # Load model
        model = DataModel(yaml_path)
        print(f"Model: {model.root.name} loaded.\n")

        print("Nodes found:")
        for path, node in model.nodes.items():
            print(f" - {path} ({type(node).__name__})")

    except AttributeError:
        _recursive_print(model.root)
    except Exception as e:
        print(f"Error: {e}")

def _recursive_print(node, level=0):
    print("  " * level + f"-> {node.name}")
    for child in getattr(node, 'children', []):
        _recursive_print(child, level + 1)

if __name__ == "__main__":
    test_model()