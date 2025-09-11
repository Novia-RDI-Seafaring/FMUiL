import yaml

class DataLoaderClass:
    def __init__(self, file_path):
        self.data = self.load_file(file_path= file_path)

    def load_file(self, file_path):
        try:
            with open(file_path) as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error in {file_path}: {e}")