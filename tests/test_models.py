import os
from machine_data_model.builder.data_model_builder import DataModelBuilder

"""Test to validate models"""
def test_all_models_are_valid():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.abspath(os.path.join(current_dir, "../models"))
    
    assert os.path.exists(models_dir), f"Models directory not found: {models_dir}"
    
    yaml_files = [f for f in os.listdir(models_dir) if f.endswith(".yml")]
    assert len(yaml_files) > 0, "No YAML files found in the models directory!"
    
    for filename in yaml_files:
        file_path = os.path.join(models_dir, filename)
        try:
            model = DataModelBuilder().get_data_model(file_path)
            assert model is not None, f"The loaded model {filename} is empty or null"
        except Exception as e:
            raise AssertionError(f"Validation error in file {filename}: {e}")