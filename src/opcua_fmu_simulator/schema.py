from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pathlib import Path
import yaml

# ----- EXTERNAL SERVERS -----
class ExternalServerConfig(BaseModel):
    pass

# ----- SIMULATION SERVER -----
class Edge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    from_: str = Field(alias="from")
    to: str = Field(description="The signal/parameter to connect to")

# Per-FMU initial config (requires timestep, allows extra keys like SP_WaterLevel_in: 10)
class InitialModelConfig(BaseModel):
    model_config = ConfigDict(extra="allow")  # accept arbitrary signal/param fields
    timestep: float = Field(description="This has to be defined for every fmu")

# The "test" section in your YAML
class TestConfig(BaseModel):
    test_name: str = Field(description="Scenario name for logs")
    timestep: float = Field(description="seconds, communication timestep")
    timing: Literal["simulation_time", "real_time"] = Field(description="simulation_time or real_time")
    stop_time: float = Field(description="seconds")
    save_logs: bool = Field(description="true/false")

    initial_system_state: Dict[str, InitialModelConfig] = Field(description="Define timestep and initial conditions")
    
    # Fields that are actually in the YAML under test section
    start_readings_conditions: Dict[str, str] = Field(description="Logging starts, when this condition is met")
    system_loop: List[Edge] = Field(description="The system loop is made according to the block diagram")
    evaluation: Dict[str, str] = Field(description="These values are logged and they also return true/false depending if the condition is satisfied")

# Top-level config
class ExperimentConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    fmu_files: List[str] = Field(description="List of FMU files")
    external_servers: List[str] = Field(description="List of external servers")
    test: TestConfig = Field(description="The test section in your YAML")
    