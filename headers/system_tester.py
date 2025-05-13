import asyncio
from headers.server_setup_dev import OPCUAFMUServerSetup
from headers.config_loader import DataLoaderClass
from asyncua import Client, ua
import os
from pathlib import Path
from colorama import Fore, Style
from headers import ops
from decimal import getcontext
import logging
from headers.connections import parse_connections # Connection
import time

logging.basicConfig(level=logging.INFO) # required to get messages printed out

getcontext().prec = 8

class TestSystem:
    def __init__(self, config_file:str, remote_servers:str = None) -> None:
        self.config = DataLoaderClass(config_file)
        self.remote_servers = self.construct_remote_servers(remote_servers)
        self.fmu_files = self.config.data["fmu_files"]
        self.tests     = self.config.data["tests"]
        self.base_port = 7000

        self.system_description = {}
        self.system_servers     = {}
        self.system_clients     = {}
        self.external_clients   = {}
        self.system_node_ids    = {} # this is meant to take in all of the systems node id's

        self.connections = None # description of system loop definition from test

    def construct_remote_servers(self, remote_servers):
        """
        remote_servers = path to directory with remote server definitions
        this function iterates through all of them and adds them to a dictionaty in a structured manner
        """
        server_dict = {}
        server_files = [os.path.join(remote_servers, i) for i in os.listdir(remote_servers)]

        for server_name in server_files:
            server_desription = DataLoaderClass(server_name).data
            print(server_desription)
            print(server_name)
            name = Path(server_name).stem
            server_dict[name] = server_desription
        
        return server_dict

    def fetch_appropriacte_client(self, client_name)->Client:
        if client_name in self.system_clients.keys():
            return self.system_clients[client_name]
        elif client_name in self.external_clients.keys():
            return self.external_clients[client_name]
        else:
            raise Exception(f"UNKNOWN CLIENT {client_name}")
    
    ########### SETTERS & GETTERS ########### 
    async def get_value(self, client_name: str, variable: ua.NodeId) -> None:
        client = self.fetch_appropriacte_client(client_name=client_name)
        node = client.get_node(variable)
        return await node.read_value() 

    async def write_value(self, client_name:str, variable:str, value:str)->None:
        """
            write value to specific node in the system
            clienet_name = client to desired server
        """
        node_id = self.system_node_ids[client_name][variable]
        client = self.fetch_appropriacte_client(client_name=client_name)
        node = client.get_node(node_id)
        await node.write_value(value)    

    async def get_system_values(self) -> dict:
        self.system_clients.keys()
        return
    
    async def run_system_updates(self, timestep):
        print(f"TIMESTEP = {timestep}, type {type(timestep)}")
        for key in self.system_clients.keys():
            print(f"updating {key} ")
            client = self.system_clients[key]
            print(f"CLIENT {client}")
            object_node = client.get_node(ua.NodeId(1, 1))
            await object_node.call_method(ua.NodeId(1, 2), str(float(timestep)))
        return
    
    ################### SYSTEM UPDATES ########################
    async def run_single_loop(self):
        """
        update loop, passing outputs from one fmu to another
        1) Updates fmu1 to get the most recent values
        2) For every I/O perform the value transfer

        *NOTE: the funciton performs transfer and updates both FMU and Server variable
        ________                      ________
        |      |*OUTPUT1 ====> INPUT1*|      |
        | fmu1 |*OUTPUT2 ====> INPUT2*| fmu2 |
        |______|*OUTPUT3 ====> INPUT3*|______|
        """
        
        for update in self.connections:
                
            print(f"\n\n\n node ids: {update.from_fmu} var = {update.from_var}")
            value_nodid = self.system_node_ids[update.from_fmu][update.from_var]
            value = await self.get_value(client_name= update.from_fmu, variable= value_nodid)

            await self.write_value(
                client_name = update.to_fmu,
                variable    = update.to_var,
                value       = value
            )
            
            print(f"passed {update.from_var} with {value}, to {update.from_var}, {update.to_var}")

    def check_time(self, sim_time, max_time):
        return sim_time >= max_time

    async def check_reading_conditions(self, conditions):
        """
        checks that the conditions required to start readings are met
        """
        for condition in conditions:
            
            print(f"\n\n\n criterea {condition} end \n\n\n")
            
            fmu_name = conditions[condition]["system_value"]["fmu"]
            variable_name = conditions[condition]["system_value"]["variable"]
            node = self.system_node_ids[fmu_name][variable_name]
            
            measured_value = self.system_clients[conditions[condition]["system_value"]["fmu"]].get_node(node)
            measured_value = await measured_value.read_value()

            print(f"checking {measured_value} {conditions[condition]["operator"]} {conditions[condition]["target"]}")
            eval_criterea = conditions[condition]["target"] 
            op            = conditions[condition]["operator"] 
            result        = ops[op](measured_value, eval_criterea) 
            variable      = conditions[condition]["system_value"]["variable"]

            if result:
                print(Fore.GREEN + f"condition  {variable} {op} {eval_criterea} PASSED \nwith value: {measured_value}")
            else:
                print(Fore.RED + f"condition {variable} {op} {eval_criterea} FAILED \nwith value: {measured_value}")
                return False

        return True

    ################################################
    ############### SYSTEM TESTS ###################
    ################################################
    
    async def run_multi_step_test(self, test: dict):
        """
        Executes the test while regulating time according to test["timing"]:
        - "simulation_time": advances time instantly
        - "real_time": waits so each step aligns with real wall-clock time
        """
        print(f"test time {test['stop_time']}")
        sim_time = 0.0
        simulation_status = True
        timestep = float(test["timestep"])  # assumed constant across system

        while simulation_status:
            start_wall_time = time.time()

            # Update all FMUs with one timestep into the future
            await self.run_system_updates(timestep=timestep)

            # Pass data between FMUs
            await self.run_single_loop()

            # Evaluation logic
            if await self.check_reading_conditions(test["start_readings_conditions"]):
                await self.check_outputs(test["evaluation"])

            # Time advancement
            sim_time += timestep

            if self.timing == "real_time":
                await self.regulate_timestep(start_time= start_wall_time, timestep= timestep)
            
            if self.check_time(sim_time, test["stop_time"]):
                simulation_status = False

    async def regulate_timestep(self, start_time: float, timestep: float):
        elapsed = time.time() - start_time
        sleep_duration = timestep - elapsed
        if sleep_duration > 0:
            await asyncio.sleep(sleep_duration)

    async def run_test(self, test: dict) -> None:
        """
        check_test_type
        call corresponding test
        """
        # reset and initialize system variables for every test
        await self.reset_system() 
        await self.initialize_system_variables(test=test)
        
        # parses system_loop section of the test and stores it to use it as the system loop 
        self.connections = parse_connections(test["system_loop"])
        # 
        await self.run_multi_step_test(test=test)

    async def reset_system(self) -> None:
        for client_name in self.system_clients:
            object_node = self.system_clients[client_name].get_node(ua.NodeId(1, 1))
            await object_node.call_method(ua.NodeId(1, 4))#, str(1)) # update fmu before updating values

    #######################################################################
    ################   CHECK SYSTEM OUTPUTS   #############################
    #######################################################################
    async def check_outputs(self, evaluation: dict[list[dict]]) -> None:
        """
        evaluation of system outputs, this function reads the "evaluation" section of the yaml file
        """
        for criterea in evaluation:
            evaluation_condition = evaluation[criterea]
            fmu_variable = evaluation_condition["system_value"]["fmu"]
            variable_name = evaluation_condition["system_value"]["variable"]
            
            node = self.system_node_ids[fmu_variable][variable_name]
            measured_value = self.system_clients[fmu_variable].get_node(node)
            measured_value = await measured_value.read_value()

            print(f"test for {fmu_variable}, {variable_name}")
            print(f"checking {measured_value} {evaluation_condition["operator"]} {evaluation_condition["target"]}")

            target_value = evaluation_condition["target"] 
            op = evaluation_condition["operator"] 
            
            # compare the two values
            evaluation_result = ops[op](measured_value, target_value)
            variable = evaluation[criterea]["system_value"]["variable"]

            if evaluation_result: print(Fore.GREEN + f"test {variable} {op} {evaluation_condition["target"]} = {evaluation_result} \n PASSED with value: {measured_value}")
            else:                 print(Fore.RED   + f"test {variable} {op} {evaluation_condition["target"]} = {evaluation_result} \n FAILED with value: {measured_value}")
            
            print(Style.RESET_ALL)

    #######################################################################
    ################   SYSTEM VARIABLE INIT   #############################
    #######################################################################
    async def initialize_system_variables(self, test:dict):
        self.timing = test["timing"]
        initial_system_state = test["initial_system_state"]
        for server in initial_system_state:
            for variable in initial_system_state[server]:
                object_node = self.system_clients[server].get_node(ua.NodeId(1, 1))
                update_values = {
                    "variable": variable,
                    "value": float(initial_system_state[server][variable])
                }
                print(f"values beeing updates {update_values}")
                await object_node.call_method(ua.NodeId(1, 3), str(update_values)) # update fmu before updating values

    ############################################################################
    #####################   FMU SERVERS INIT   #################################
    ############################################################################
    async def initialize_fmu_opc_servers(self):
        
        tasklist = []
        
        for fmu_file in self.fmu_files:
            print("intializing : ", fmu_file)
            self.base_port+=1
            
            server =  await OPCUAFMUServerSetup.async_server_init(
                fmu=fmu_file, 
                port=self.base_port
            )

            server_task = asyncio.create_task(server.main_loop())
            await server.server_started.wait()
            server.server_started.clear()

            self.system_servers[server.fmu.fmu_name] = server
            tasklist.append(server_task)

        return tasklist

    ###########################################################################
    #####################   INIT SYSTEM IDS   #################################
    ###########################################################################
    def gather_system_ids(self):
        for server_name in self.system_servers:
            self.system_node_ids[server_name] = self.system_servers[server_name].server_variable_ids

    ############################################################################
    #######################   CLIENTS INIT   ###################################
    ############################################################################
    async def creat_internal_clients(self):
        
        for server_name in self.system_servers:
            server = self.system_servers[server_name]
            client = Client(url=server.url)
            await client.connect()
            self.system_clients[server_name] = client
        
        print(f"system clients clients setup: {self.system_clients}")
        
    async def create_external_clients(self):
        
        for server in self.remote_servers:
            
            server_url = self.remote_servers[server]["url"]
            client = Client(url=server_url)
            await client.connect()
            self.external_clients[server] = client
            
    async def create_system_clients(self):
        await self.creat_internal_clients()
        await self.create_external_clients()

    ################################################################################
    ###########################   MAIN LOOP   ######################################
    ################################################################################
    async def main_testing_loop(self):
        
        # system initialization
        servers = await self.initialize_fmu_opc_servers()
        await self.create_system_clients()
        self.gather_system_ids()
        
        print(f"TESTS = {self.tests}, \n type {type(self.tests)} \n {self.tests.keys()} \n\n")        
        for test in self.tests:
            print("RUNNING TESTS")
            await self.run_test(self.tests[test])
            
        return await asyncio.gather(*servers)

    #################################################################################
    ########################   UTILITY FUNCTION   ###################################
    #################################################################################
    async def describe_system(self):
        tasklist = await self.initialize_fmu_opc_servers()
        for server_name in self.system_servers:
            self.system_description.update(self.system_servers[server_name].get_server_description())

        print(f"system description = {self.system_description}")
        for task in tasklist:
            await task
