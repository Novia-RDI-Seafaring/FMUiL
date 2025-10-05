from typing import List, Literal, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pathlib import Path
import yaml

# ----- EXTERNAL SERVERS -----
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

class SampleOpcObject(BaseModel):
    custom_variable: CustomVariable = Field(
        ..., description="First custom variable for this OPC UA object."
    )
    custom_variable2: CustomVariable = Field(
        ..., description="Second custom variable for this OPC UA object."
    )

class ExternalServerConfig(BaseModel):
    url: str = Field(
        ..., description="OPC UA server endpoint URL (e.g., 'opc.tcp://host:port/path')."
    )
    objects: Dict[str, SampleOpcObject] = Field(
        ..., description="Mapping of OPC UA objects by name."
    )

# ----- SIMULATION SERVER -----
class Edge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    from_: str = Field(alias="from")
    to: str = Field(description="The signal/parameter to connect to")

# Per-FMU initial config (requires timestep, allows extra keys like SP_WaterLevel_in: 10)
class InitialModelConfig(BaseModel):
    model_config = ConfigDict(extra="allow")  # accept arbitrary signal/param fields
    timestep: float = Field(description="This has to be defined for every fmu")

# Evaluation section
class EvaluationCriteria(BaseModel):
    condition: str = Field(description="The condition to be evaluated")
    enabled: bool = Field(default=True, description="Whether the evaluation is performed")

# The "test" section in your YAML
class TestConfig(BaseModel):
    experiment_name: str = Field(description="Scenario name for logs")
    timestep: float = Field(description="seconds, communication timestep")
    timing: Literal["simulation_time", "real_time"] = Field(description="simulation_time or real_time")
    stop_time: float = Field(description="seconds")
    initial_system_state: Dict[str, InitialModelConfig] = Field(description="Define timestep and initial conditions")
    
    # Fields that are actually in the YAML under test section
    start_evaluating_conditions: Optional[Dict[str, str]] = Field(default=None, description="Evluating starts, when this condition is met")
    system_loop: List[Edge] = Field(description="The system loop is made according to the block diagram")
    evaluation: dict[str, EvaluationCriteria] = Field(description="These values are logged and they also return true/false depending if the condition is satisfied")
    logging: List[str] = Field(description="These values are logged and they also return true/false depending if the condition is satisfied")

# Top-level config
class ExperimentConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    fmu_files: List[str] = Field(description="List of FMU files")
    external_servers: List[str] = Field(description="List of external servers")
    experiment: TestConfig = Field(description="The test section in your YAML")



    