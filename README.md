# fmu-opcua-test-platform



# dev notes

## tasks
1) universal clock
3) state machines
4) add to value

## in progress

2) zero order hold, signals hold their value constant until changed
goal: make the fmus work with a universal time
for example fmu1 has a timestep of 0.5 seconds while fmu2 has a step of t=1sec

we have a universal clock and timestep

it should loop around the whole thing and whenever enough time has passed we update our values

solution:

every server should have 
- server time
- fmu time
- receive system time

through these we can get the time from the system and update server time
then we check if (server time - fmu time >= step) if that's true we make a step to the fmu 

to do this we'll be calling the fmu step function while passing in the server time variable




## done






# test definition


    tests:
        test_name:
            test_type: 

            test_description: "a description of the test"

            initial_system_state:

            start_readings_conditions:

            system_loop:

    



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


