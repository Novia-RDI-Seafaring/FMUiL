import yaml

class DataLoaderClass:
    def __init__(self, file_path):
        self.data = self.load_file(file_path= file_path)

    def load_file(self, file_path):
        with open(file_path) as file:
            return yaml.safe_load(file)