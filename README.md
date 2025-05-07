# fmu-opcua-test-platform


# current:



UPdate single loop upate so that the system updates outside of that function

the funciton should only perform IOs no updates, 


# real time application 

sleep till stepsize is met
loop timestep = 1 sec, if loop takes 0.2 sleep for 0.8
raise exception if system time is more than timestep

make tests as files = one test is one file not all in one 


# dev notes

try making parent in function calls the server itself, then we only need to pass in the variable

## tasks

universal update loop: update the whole system evey timestep, each component updates based on its internal ts and we make the passes also

3) state machines:
    give initial and final system state, check whether or not it was reached in a given time window

4) add to value:
    when and what: user defines under which conditions the value is added in a filed called "value modifications"


## done

minor: add setters and getters to the server itself and clean it up a bit 
1) universal clock


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


3) distinguish between internal and external clients


5) add manual testing mode where delays are always equal to the system time



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


