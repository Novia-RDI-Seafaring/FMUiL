from typing import List, Literal, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pathlib import Path
import yaml

class CustomVariable(BaseModel):
    id: Optional[int] = Field(
        None, description="Numeric identifier of the OPC UA variable."
    )
    ns: Optional[int] = Field(
        None, description="Namespace index for the OPC UA variable."
    )
    name: Optional[str] = Field(
        None, description="Fully qualified OPC UA variable name (e.g., 'ns=5;i=4')."
    )

class ExternalServerConfig(BaseModel):
    url: str = Field(
        ..., description="OPC UA server endpoint URL (e.g., 'opc.tcp://host:port/path')."
    )
    objects: Dict[str, Dict[str, CustomVariable]] = Field(
        ..., description="Mapping of OPC UA objects by name. Each object has arbitrary variables."
    )

# ----- SIMULATION SERVER -----
class Edge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    from_: str = Field(alias="from", description="An output from an fmu that is connected to an input")
    to: str = Field(description="An input from an fmu that is connected to an output")

# Per-FMU initial config (requires timestep, allows extra keys like SP_WaterLevel_in: 10)
class InitialModelConfig(BaseModel):
    model_config = ConfigDict(extra="allow")  # accept arbitrary signal/param fields
    timestep: float = Field(description="Individual FMUs timestep")

# Evaluation section
class EvaluationCriteria(BaseModel):
    condition: str = Field(description="The condition to be evaluated, e.g., WaterTankSystem.PV_WaterLevel_out < 11.1")
    enabled: bool = Field(default=True, description="Whether the evaluation is performed")

# The "experiment" section in your YAML
class TestConfig(BaseModel):
    experiment_name: str = Field(description="Experiment name")
    timestep: float = Field(description="Communication timestep in seconds, e.g., when FMU's exchange data")
    timing: Literal["simulation_time", "real_time"] = Field(description="simulation_time performs simulations as fast as possible, real_time simulates in real time")
    stop_time: float = Field(description="stop time for the simulation in seconds")
    initial_system_state: Dict[str, InitialModelConfig] = Field(
        description=
            (
            "Initial configuration for each FMU in the system.\n"
            "Each FMU entry may define its own timestep, inputs, and parameters.\n"
            "Example: a key is defined as\n"
            "PI_controller: {\n"
            "  timestep: 0.1,\n"
            "  input: 1,\n"
            "  Kp: 1,\n"
            "  Ki: 0.2\n"
            "}\n"
            "Note: Parameter names must match the FMU model definition."
            )
        )
    
    # Fields that are actually in the YAML under test section
    start_evaluating_conditions: Optional[Dict[str, str]] = Field(default=None, description="Evaluating starts, when these condition are met")
    system_loop: List[Edge] = Field(description="Defines how fmus and opc objects are connected")
    evaluation: Optional[dict[str, EvaluationCriteria]] = Field(description= "Evaluation criteria for the system. Each key identifies the test criterion name.")
    logging: List[str] = Field(description="List of simulation variable names to be logged. Example: WaterTankSystem.PV_WaterLevel_out")

# Top-level config
class ExperimentConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    fmu_files: List[str] = Field(description="List of relative FMU filepaths, example: fmus/WaterTankSystem.fmu")
    external_servers: List[str] = Field(description="List of relative filepaths to external server configuration file, example: servers/example_server.yaml")
    experiment: TestConfig = Field(description="The experiment section in your configuration file")



    