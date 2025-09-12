from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

# ----- EXTERNAL SERVERS -----
class ExternalServerConfig(BaseModel):
    pass

# ----- SIMULATION SERVER -----
class ServerConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fmu_files: List[str] = Field(
        default=[],
        description=(
            "List of paths to .fmu models to be simulated. "
            "Example: ['fmus/WaterTankSystem.fmu', 'fmus/TankLevel_PI.fmu']"
        ),
    )
    external_servers: List[str] = Field(
        default=[],
        description=(
            "List of paths to .yaml external server configuration files. "
            "Example: ['servers/example_server.yaml']"
        ),
    )

    @field_validator("fmu_files", mode="before")
    @classmethod
    def check_fmu_extension(cls, v):
        if isinstance(v, list):
            for item in v:
                if not isinstance(item, str) or not item.lower().endswith(".fmu"):
                    raise ValueError(f"Invalid file extension: {item!r} must end with '.fmu'")
        return v


class InitialStateConfig(BaseModel):
    pass


class Conditions(BaseModel):
    expression: str = Field(..., description="Example: 'TankLevel_PI.CV_PumpCtrl_out > 0.01'")


class MapIO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    _from: str = Field(..., alias="from", description="from output")
    _to: str = Field(..., alias="to", description="to input")


class ScenarioConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    experiment_name: str = Field(..., alias="test_name", description="Name of the simulation experiment.")
    timestep: float = Field(default=1.0, description="Simulation timestep.")
    timing: Literal["real_time", "simulation_time"] = Field(default="simulation_time", description="Timing mode.")
    stop_time: float = Field(default=10.0, description="Simulation stop time (seconds).")
    initial_system_state: InitialStateConfig = Field(..., description="Define timestep and initial conditions.")

    start_reading_conditions: List[Conditions] = Field(
        ...,
        alias="start_readings_conditions",
        description="Logging starts when any condition is met.",
    )

    system_loop: List[MapIO] = Field(
        ...,
        description=(
            "The system loop defines which inputs and outputs are connected. "
            "Example: from: TankLevel_PI.CV_PumpCtrl_out | to: WaterTankSystem.CV_PumpCtrl_in"
        ),
    )

    evaluation: List[Conditions] = Field(
        ...,
        description="When condition is met, these values are logged and return true/false.",
    )