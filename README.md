<p align="center">
  <a href="https://github.com/Novia-RDI-Seafaring/opcua-fmu-simulator"><img src="./public/FMUiL.svg" alt="FMUiL" width="200">
</a>
</p>


<p align="center">
    <b>Functional Mock-up Unit in the loop (FMUiL)</b> <br />
    Perform X-in-the-Loop (XiL) simulation tests with FMU simulation models and communication over OPC-UA.
</p>

<p align="center">
  <a href="https://www.novia.fi/" target="_blank">
      Novia UAS
  </a>|
  <a href="https://www.utu.fi/en" target="_blank">
      University of Turku
  </a>|
  <a href="https://www.virtualseatrial.fi/" target="_blank">
      Research Project
  </a>|
  <a href="mailto:mikael.manngard@novia.fi?subject=MCP-FMI:">Contact</a>

</p>
<p align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python Version">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/github/license/Novia-RDI-Seafaring/FMU-OPCUA-TEST-PLATFORM" alt="License: MIT">
  </a>
  <a href="https://www.businessfinland.fi/">
    <img src="https://img.shields.io/badge/Funded%20by-Business%20Finland-blue" alt="Funded by Business Finland">
  </a>
</p>

# FMUiL
**Table of content**
- [1. Features](#features)
- [2. Installation](#installation)
- [3. Configure experiments](#configure-experiments)
    - [3.1. Experiment configuration](#experiment-configuration)
    - [3.2. External servers](#external-servers)
- [4. Run experiments](#run-experiments)
- [5. Examples](#example-usage)
- [6. Contributing](#contributing)
- [7. Other](#other)
    - [7.1. Main contributors](#main-contributors)
    - [7.2. Citation](#citation)
    - [7.3. License](#license)
    - [7.4. Acknowledgements](#acknowledgements)

## Features
- **Simulate FMU models** with OPC-UA communicaiton.
- **Connect external OPC-UA servers**. This allwows FMU models to simulated together with thrid-party hardware and software.
- **Manage tests and violation monitoring** for simulation scenarios.


## Installation

### Prerequisites
- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Quick Setup with uv (Recommended)

1. **Install uv** (if not already installed):
   ```powershell
   # Windows PowerShell
   irm https://astral.sh/uv/install.ps1 | iex
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/Novia-RDI-Seafaring/opcua-fmu-simulator.git
   cd opcua-fmu-simulator
   ```

3. **Install the project and all dependencies**:
   ```bash
   uv sync
   ```

   This single command will:
   - Create a virtual environment automatically
   - Install all required dependencies
   - Install the OPCUA-FMU-Simulator package in editable mode
   - Create a lock file for reproducible installs

4. **Activate the virtual environment** (if needed):
   ```powershell
   # Windows
   .venv\Scripts\Activate.ps1
   
   # Linux/macOS
   source .venv/bin/activate
   ```
  
# Configure experiments

## Experiment configuration
The experiment file allows users to configure the following parameters:

- **FMUs** included in the simulation  
- **External OPC UA servers** used  
- **Test parameters:**  
  - Test name  
  - Communication timestep  
  - Simulation or real-time mode  
  - Simulation stop time
  - experiment description  
- **Initial system inputs** for all FMUs and external servers  
- **Conditions for start evaluation**  
- **System loop definition** (from-to)  
- **Simulation evaluation criteria**
  - condition
  - enabled
- **Logged values** 


**Example configuration file:**

```yaml
    fmu_files:  [  
                "path01 to your fmu",
                "path02 to your fmu",
                "path03 to your fmu"
                ]

    external_servers: [
                      "path01 to your external server yaml description",
                      "path02 to your external server yaml description",
                      "path03 to your external server yaml description"
                      ]

    experiment:
      experiment_name: "a unique test name"
      timestep: 0.5                             # Communication timestep in seconds
      timing:  "simulation_time" or "real_time" # As fast as possible or real time
      stop_time: 100.0                          # Duration of the test 
      test_description: "a description of the test"

      initial_system_state:
        FMU_Model_Name:
          FMU_input_name1: "desired initial value"
          FMU_input_name2: "desired initial value"
          FMU_parameter_name1: "desired initial value"
          FMU_parameter_name2: "desired initial value"

        example_server:
          opcua_object01_variable1: "desired initial value"

      start_readings_conditions:
        condition_name: "FMU_Model_Name.FMU_input_name1 > 10"
        # the object and variable have to be part of a created or external server 
        # operators supported: '+' '-' '<' '<=' '>' '>='
        # Evaluation starts when this condition(s) is met, can be empty to always evaluate

      system_loop: # definition how the systems are connected 
        - from: source_object.source_variable
          to:   target_object.target_variable
        
        - from: source_object.source_variable
          to:   target_object.target_variable

      evaluation: # Evaluation criteria, will log true/false depending if the condition is met
        eval_1: 
          condition: "fmu1.value < 11.1"
          enabled: true
        eval_2: 
          condition: "fmu2.value < 11.1"
          enabled: false

      logging:
        ["fmu.variable","opc.variable"]
```

## External Servers

The FMUiL allows users to integrate external servers alongside their FMUs. These servers are specified in the configuration file under the external server section using the server description file. To add an server, create a `.yaml` file describing your server.  

**Example server definition:**

```yaml
    url: opc.tcp://localhost:4840/opcua/server/ #server url

    # object definition, used objects/variables must be specified
    objects:
      object_name_01:
        variable_name_01: 
          id: 4
          ns: 5
          name: "variable_01"
      
        variable_name_02: 
          name: "variable_02"
      
        variable_name_03: 
          id: 4
          ns: 5
```  
 
Set `url` to match the server address. Specify variables using OPC UA node id and namespace or their BrowseNames. Include the server in your simulation by adding the YAML file path in your test definition:
```yaml
external_servers: ["path/to/server_description.yaml"]
```


## Run experiments
Experiments are defined as `.yaml` files and are located by default in the `/experiments` folder. 
You can change this folder using the `-d` or `--experiments-dir` option.

During development, you can run experiments using the provided `uv` scripts. Once the package is installed, you can use the `fmuil` command directly. 

### Run all experiments
Run every experiment file in the default `/experiments` folder:

```powershell
uv run fmuil run-all
```

If your experiments are in a different folder, specify the path using the -d or --experiments-dir option:

```powershell
uv run fmuil -d "path/to/experiments" run-all
```

After installation (when fmuil is available as a system command):
```powershell
fmuil run-all
# or
fmuil -d "path/to/experiments" run-all
```
### Run specific experiments
To run a specific experiment, use the `run` command and provide the experiment file name:

```powershell
uv run fmuil run "exp1_water_tank.yaml"
```
If your experiments are in a different folder, specify the path using the -d or --experiments-dir option:

```powershell
uv run fmuil -d "path/to/experiments" run "exp1_water_tank.yaml"
```

After installation:

``` powershell
fmuil run "exp1_water_tank.yaml"
# or
fmuil -d "path/to/experiments" run "exp1_water_tank.yaml"
```
### Options

It is possible to define the port number, from which the server creation starts. Default is `7500`.
```powershell
--port 1234
# or
-p 1234
```

# How to log results
FMUiL supports conditional evaluation of FMU variables, which starts when specified start_evaluating_conditions are met. Each evaluation rule can be enabled or disabled.

Traditional logging allows recording FMU or server variables by adding them to the logging list in the experiment YAML.


## Evaluation

FMUiL supports conditional logging, referred to as evaluation, which begins only when specific start conditions are met.
The start_evaluating_conditions block can define zero or more logical expressions that determine when test evaluations should start. Once any of these conditions become true, the system begins evaluating and logging results.

Each evaluation rule is defined under the evaluation section and can be individually enabled or disabled using the enabled flag.

All logged evaluation data is saved to: `logs/timestamp/experiment_name/evaluation.csv` and consist of:
 
- `experiment_name`: Given name of the experiment under experiment_name 
- `evaluation_name`: Name of the evaluation metric defined in the test
- `evaluation_function`: Evaluation function defined in the configuration
- `measured_value`: Value of the variable during the time of the test
- `experiment_result`: Boolean value if the condition is met
- `system_timestamp`: system time at the time of the evaluation 
> **NOTE:** Evaluation only works for FMU variables. For external variables use logging.

## Logging

It is also possible to use traditional variable logging. This is done by adding `FMU.Variable` to the logging list in the experiment file, e.q.

```yaml
# General
logging:
  ["fmu.variable", "server.node"]
# from example 3:
logging:
  ["gain.output","example_server.my_opc_variable"]
```
This will create an `values.csv` in `logs/timestamp/experiment_name/` that contains:

- `experiment_name`: Given name of the experiment under experiment_name 
- `System`: Name of the FMU or server
- `Variable`: Name of the variable
- `Value`: Value of the variable 
- `Time`: Simulation time 

# Examples
This package is shipped with three examples that showcases some of the functionality of the package. More information about individual examples can be found in `/examples`. To get an comprehensive look how to package works, please take a look at the WaterTankSystem example. 

To run all the examples you can run:
```powershell
uv run fmuil run-all
```
This should run all the examples, except the `exp3_external_server.yaml`, which needs an external server from `/experiments/servers/example_server.py`. It uses the default `experiments` folder as the source for the experiment files. These examples can also be run individually straight from the `examples` folder:

WaterTankSystem:
```powershell
uv run fmuil -d "examples\Watertanksystem" run "exp1_water_tank.yaml"
``` 
Lube oil cooling:

```powershell
uv run fmuil -d "examples\Lube oil cooling" run "exp2_loc.yaml"
``` 
External server example:

```powershell
uv run fmuil -d "examples\External server" run "exp3_external_server.yaml"
``` 

# Contributing

We welcome contributions! Please follow these steps:

- Fork the repository  
- Create a new feature branch
- Make your changes
- Commit your changes with clear commit messages. We recommend following the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.
- Push your branch and create a pull request

# Other
## Main Contributors
- **Domitrios Bouzoulas**, Novia UAS. 
    -  *CRediT*: Conceptualization, Methodology, Software, Validation
- **Kristian Klemets**, University of Turku.
    -  *CRediT*: Conceptualization, Methodology, Software, Validation
- **Mikael Manngård**, Novia UAS.
    -  *CRediT*: Conceptualization, Supervision
- **Jari Böling**, Novia UAS.
    -  *CRediT*: Supervision

## Citation
If you use this package in your research, please cite it using the following BibTeX entry:

```bibtex
@misc{FMUiL,
  author = {Kristian Klemets, Dimitrios Bouzoulas, Mikael Manngård},
  title = {FMUiL: Functional Mock-Up Units In the Loop},
  year = {2025},
  howpublished = {\url{https://github.com/Novia-RDI-Seafaring/FMUiL}},
}
```

## License
This package is licensed under the MIT License license. See the [LICENSE](./LICENSE) file for more details.

## Acknowledgements
This work was done in the Business Finland funded project [Virtual Sea Trial](https://virtualseatrial.fi)
 
