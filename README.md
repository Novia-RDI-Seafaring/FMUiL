<p align="center">
  <a href="https://novia.fi"><img src="./readme_resources/opcua_fmu_logo.png" alt="OPCUA-FMU" width="200">
</a>
</p>

<p align="center">
    <b>OPC-UA and FMU Simulator</b> <br />
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

# OPCUA-FMU Simulator
**Table of content**
- [1. Features](#features)
- [2. Installation](#installation)
- [3. Configurations](#configurations)
    - [3.1. Test configuration](#test-configuration)
    - [3.2. External servers](#external-servers)
- [4.Example usage](#example-usage)
- [5. Other](#other)
    - [5.1. Main contributors](#main-contributors)
    - [5.2. Citation](#citation)
    - [5.3. License](#license)
    - [5.4. Acknowledgements](#acknowledgements)

## Features
- **Simulate FMU models** with OPC-UA communicaiton.
- **Connect external OPC-UA servers**. This allwows FMU models to simulated together with thrid-party hardware and software.
- **Manage tests and violation monitoring** for simulation scenarios.

## Installation

  pip create -n opcua_fmu_environment python=3.13.2

  pip install -r requirements.txt

  cd .\OPCUA-FMU-simulator-package\

  python -m build ; pip install .

## running examples

for the tests to run, test01 and test02 will be performed without any additional setup, simply by running main.py:

    python main.py

for test03 to also run you will need to run the remote server under test_servers:

  terminal 1:
    
    python test_servers/server_description01.yaml

  terminal 2:

    python main.py

# Configurations
Examples of how to configure the simulation tests and external OPC-UA servers.

## Test configuration

    fmu_files:[
      "path01 to your fmu",
      "path01 to your fmu"
      ]

    external_servers: [
                      "path01 to your external server yaml description",
                      "path02 to your external server yaml description",
                      "path03 to your external server yaml description"
                      ]

    test:
      test_name: "a unique test name"
      timestep: 1.2 # in seconds
      timing:  "simulation_time" or "real_time" 
      stop_time: 100.0 # duration of the test 
      save_logs: true # boolean
      test_description: "a description of the test"

      initial_system_state:
        opcua_object01_name:
          opcua_object_variable1: "desired initial value"
          opcua_object_variable2: "desired initial value"
          opcua_object_variable3: "desired initial value"

        opcua_object02_name:
          opcua_object02_variable1: "desired initial value"

      start_readings_conditions:
        condition_name: "object_name.variable operator value"
        # example_condition: "fmu_fuel_tank.fuel_level > 20"
        # the object and variable have to be part of a created or external server 
        # operators supported: '+' '-' '<' '<=' '>' '>='

      system_loop: # difinision of system cycle 
        - from: source_object.source_variable
          to:   target_object.target_variable
        
        - from: source_object.source_variable
          to:   target_object.target_variable

      ################# evaluation #################
      evaluation: 
        eval_1: "object.value < 11.1"
        eval_2: "object.value > 20"

## External Servers

the system enables its users to use external servers along side with their FMU based OPCUA servers.

#### Adding an external server

  1) server definition: create a .yaml file with the description of your server.
  Example server definition:

    url: opc.tcp://localhost:5000/opcua/server/ #server url

    # object definition, used objects/variables must be specified
    objects:
      object_name_01:
        vairable_name_01: 
          id: 4
          ns: 5
          name: "vairable_01"
      
        vairable_name_02: 
          name: "vairable_02"
      
        vairable_name_03: 
          id: 4
          ns: 5
    
  - url has to correspond to the server
  - variables can be with (id, namespace) and/or their name, for most applications and to avoid error it is recommended to use ((id, namespace))

  2) to add the server to the system you need to add the path of the config file to your test definition  `external_servers: ["path to yaml description"]`.


NOTES: external servers are treated as OPCUA servers, as a result hardware can also be used with this system. 


# Logging

The system logs all data required to evaluate a tests performance when the flag `save_logs: true`. The saved values are the following:
 
test_name: given name of the test under `test_name:` flag 

evaluation_name: name of the evaluation metric defined in the test.

evaluation_function: "object.vairable < 11.1"

measured_value: value of the vairable during the time of the test

test_result: boolean true or false

system_timestamp: system time at the time of the test


# Example usage
## System

The example comprises of two fmu collectively describing a lube oil cooling system, with one acting as a regualtor valve and the other the system.

System Diagram

<img src="./readme_resources/LOC.drawio.svg"/>

FMU architecture and IOs

<img src="./readme_resources/system_diagram.png"  />


TESTS/TEST02.taml represents an appropriate test file for this system:

    fmu_files: # list of fmu files || Model description Names:LOC_CNTRL_v2_customPI, LOC_SYSTEM
  ["FMUs/LOC_CNTRL_custom_linux.fmu",
   "FMUs/LOC_SYSTEM_linux.fmu"]

external_servers: []

test:
  test_name: test_01
  timestep: 0.5    # seconds, communication timestep
  timing: "simulation_time" # simulation_time or real_time 
  stop_time: 400.0 # seconds 
  save_logs: true
  initial_system_state:
    
    LOC_CNTRL_v2_customPI:
      timestep: 0.5
      SETPOINT_temperature_lube_oil: 70
      INPUT_temperature_lube_oil: 65
    
    LOC_SYSTEM:
      timestep: 0.5
      INPUT_temperature_cold_circuit_inlet: 40
      INPUT_massflow_cold_circuit: 35
      INPUT_engine_load_0_1: 1
      INPUT_control_valve_position: 0

  start_readings_conditions: 
    condition_01: "LOC_SYSTEM.OUTPUT_temperature_lube_oil > 65"

  system_loop: 
    - from: LOC_CNTRL_v2_customPI.OUTPUT_control_valve_position
      to:   LOC_SYSTEM.INPUT_control_valve_position
    
    - from: LOC_SYSTEM.OUTPUT_temperature_lube_oil
      to:   LOC_CNTRL_v2_customPI.INPUT_temperature_lube_oil   

  ################# evaluation #################
  evaluation: 
    eval_1: "LOC_SYSTEM.OUTPUT_temperature_lube_oil < 80"
    eval_2: "LOC_CNTRL_v2_customPI.OUTPUT_control_valve_position < 1.01"
    eval_3: "LOC_SYSTEM.OUTPUT_massflow_cold_circuit < 80"
    eval_4: "LOC_SYSTEM.OUTPUT_temperature_cold_circuit_outlet < 80"




## Main Contributors
- **Domitrios Bouzoulas**, Novia UAS. 
    -  *CRediT*: Conceptualization, Methodology, Software, Validation
- **Kristian Klemets**, University of Turku.
    -  *CRediT*: Conceptualization, Methodology, Software, Validation
- **Mikael Manngård**, Novia UAS.
    -  *CRediT*: Conceptualization, Supervision

## Citation
If you use this package in your research, please cite it using the following BibTeX entry:

```bibtex
@misc{OPCUA-FMU-Simulator,
  author = {Dimitrios Bouzoulas, Kristian Klemets, Mikael Manngård},
  title = {OPCUA-FMU Simulator},
  year = {2025},
  howpublished = {\url{https://github.com/Novia-RDI-Seafaring/fmu-opcua-test-platform}},
}
```

## Further development notes

- User interface addition
- System tester takes as input the log file after the test has been performed and compares it to existing "correct" log file looking for differences.



## License
This package is licensed under the MIT License license. See the [LICENSE](./LICENSE) file for more details.

## Acknowledgements
This work was done in the Business Finland funded project [Virtual Sea Trial](https://virtualseatrial.fi)

