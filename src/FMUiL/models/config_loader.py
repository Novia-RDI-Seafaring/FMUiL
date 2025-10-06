import yaml
from FMUiL.schema import ExperimentConfig, ExternalServerConfig
from pydantic import ValidationError
from pathlib import Path

class ExperimentLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.model = self.load_model()
    
    def load_file(self):
        try:
            with open(self.file_path) as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error in {self.file_path}: {e}")

    def load_model(self):
        data = self.load_file()
        # load as pydantic ExperimentConfig model
        try:
            return ExperimentConfig.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"Config does not match ExperimentConfig schema: {e}")

    def dump_json(self):
        return self.model.model_dump_json(by_alias=True, indent=2)

    def dump_dict(self):
        return self.model.model_dump(by_alias=True)

    def save_json(self, name: str):
        """
        Save the Pydantic model as JSON to a new file with the specified name.
        If file exists, adds (1), (2), etc. to the name.
        """
        # Create output path with .json extension
        base_path = Path(self.file_path).parent / f"{name}.json"
        output_path = self._get_unique_path(base_path)

        data = self.dump_json()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(data)

    def save_yaml(self, name: str):
        """
        Save the Pydantic model as YAML to a new file with the specified name.
        If file exists, adds (1), (2), etc. to the name.
        """
        # Create output path with .yaml extension
        base_path = Path(self.file_path).parent / f"{name}.yaml"
        output_path = self._get_unique_path(base_path)
        
        data = self.dump_dict()

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def _get_unique_path(self, base_path: Path) -> Path:
        """
        Get a unique file path by adding (1), (2), etc. if the file already exists.
        
        Args:
            base_path: The desired file path
            
        Returns:
            A unique file path that doesn't exist
        """
        if not base_path.exists():
            return base_path
        
        # Split the path into stem and suffix
        stem = base_path.stem
        suffix = base_path.suffix
        parent = base_path.parent
        
        counter = 1
        while True:
            new_path = parent / f"{stem}({counter}){suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

# external server
class ExternalServerLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.model = self.load_model()
    
    def load_file(self):
        try:
            with open(self.file_path) as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error in {self.file_path}: {e}")

    def load_model(self):
        data = self.load_file()
        # load as pydantic ExperimentConfig model
        try:
            return ExternalServerConfig.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"Config does not match ExperimentConfig schema: {e}")

    def dump_json(self):
        return self.model.model_dump_json(by_alias=True, indent=2)

    def dump_dict(self):
        return self.model.model_dump(by_alias=True)

    def save_json(self, name: str):
        """
        Save the Pydantic model as JSON to a new file with the specified name.
        If file exists, adds (1), (2), etc. to the name.
        """
        # Create output path with .json extension
        base_path = Path(self.file_path).parent / f"{name}.json"
        output_path = self._get_unique_path(base_path)

        data = self.dump_json()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(data)

    def save_yaml(self, name: str):
        """
        Save the Pydantic model as YAML to a new file with the specified name.
        If file exists, adds (1), (2), etc. to the name.
        """
        # Create output path with .yaml extension
        base_path = Path(self.file_path).parent / f"{name}.yaml"
        output_path = self._get_unique_path(base_path)
        
        data = self.dump_dict()

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def _get_unique_path(self, base_path: Path) -> Path:
        """
        Get a unique file path by adding (1), (2), etc. if the file already exists.
        
        Args:
            base_path: The desired file path
            
        Returns:
            A unique file path that doesn't exist
        """
        if not base_path.exists():
            return base_path
        
        # Split the path into stem and suffix
        stem = base_path.stem
        suffix = base_path.suffix
        parent = base_path.parent
        
        counter = 1
        while True:
            new_path = parent / f"{stem}({counter}){suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
