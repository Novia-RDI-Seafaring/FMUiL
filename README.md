# fmu-opcua-test-platform

# ongoing task:


# tasks:

add real time option

add logging

separate tests into different files

improve logging on screen

update reading_conditions, and evaluation



# test definition


    tests:
        test_name:

            test_description: "a description of the test"

            initial_system_state:
                fmu_name:
                    timestep: 0.1 # seconds
                    variable_01: 1 
                    variable_02: 2
                    variable_03: 4
                    variable_04: 54

            start_readings_conditions:  # will be improved to "fmu.variable operator value"
                condition_01: {system_value: 
                    {
                    fmu: LOC_CNTRL_v2_customPI, 
                    variable: OUTPUT_control_valve_position
                    }, 
                    operator: ">", 
                    target: 0.20 }
            
            system_loop: # describes 1 copmlete system cycle
                - from: fmu.variable_name
                    to: fmu.variable_name
                
            evaluation"
                evaluation: 
                    eval_1: {system_value: {
                        fmu: LOC_CNTRL_v2_customPI, 
                        variable: OUTPUT_control_valve_position}, 
                        operator: "<", 
                        target: 0.1 }


simply loop after first fmu inputs

loop:
    first inputs = defaults

    first outputs = second input

    second out = first in



alllow multiple of the same fmu by adding id's to the end

# system

System Diagram

<img src="./readme_resources/LOC.drawio.svg"/>

FMU architecture and IOs

<img src="./readme_resources/system_diagram.png"  />


