import asyncio
from headers.server_setup_dev import OPCUAFMUServerSetup
from headers.config_loader import DataLoaderClass
from asyncua import Client, ua
import asyncua
import sys
from colorama import Fore, Back, Style
from headers import ops


class TestSystem:
    def __init__(self, config_file:str) -> None:
        self.config = DataLoaderClass("TESTS/system_config.yaml")
        self.fmu_files = self.config.data["fmu_files"]
        self.tests     = self.config.data["tests"]        
        self.base_port = 7000

        self.system_description = {}
        self.system_servers     = {}
        self.system_clients     = {}

    ########### SETTERS & GETTERS ########### 
    async def get_value(self, client_name: str, variable: str) -> None:
        node = self.system_clients[client_name].get_node(variable)
        return await node.read_value() 

    async def write_value(self, client_name:str, variable:str, value:str)->None:
        """
            write value to specific node in the system
            clinet_name = client to desired server
        """
        node_id = self.system_servers[client_name].server_variable_ids[variable]
        node_to = self.system_clients[client_name].get_node(node_id)        
        await node_to.write_value(value)    


    ################### SYSTEM UPDATES ########################
    async def run_single_loop(self, test_loops:dict):
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

        for obj in test_loops:
            
            # doing 1 update to the object fmu
            client = self.system_clients[obj]

            # update fmu before updating values
            object_node = client.get_node(ua.NodeId(1, 1))
            await object_node.call_method(ua.NodeId(1, 2), 1) 
            print(f"updated {obj}, client {client}")
            # updating I/Os after system update
            for io_update in test_loops[obj]:
                
                # Read the value we want to pass to the next fmu server
                value = await self.get_value(client_name= obj, variable= self.system_servers[obj].server_variable_ids[io_update["variable_output"]])

                # write value to other server
                await self.write_value(
                    client_name = io_update["object_input"],
                    variable    = io_update["variable_input"],
                    value       = value
                )

                print(f"passed {value}, to {io_update["object_input"]},{io_update["variable_input"]}")

    def check_time(self, sim_time, max_time):
        return sim_time >= max_time

    async def check_reading_conditions(self, conditions):
        for condition in conditions:
            print(f"criterea {condition} end")
            node = self.system_servers[conditions[condition]["system_value"]["fmu"]].server_variable_ids[conditions[condition]["system_value"]["variable"]]
            measured_value = self.system_clients[conditions[condition]["system_value"]["fmu"]].get_node(node)
            measured_value = await measured_value.read_value()

            print(f"checking {measured_value} {conditions[condition]["operator"]} {conditions[condition]["target"]}")
            eval_criterea = conditions[condition]["target"] 
            op =conditions[condition]["operator"] 
            result = ops[op](measured_value, eval_criterea)
            

            variable = conditions[condition]["system_value"]["variable"]

            if result:
                print(Fore.GREEN + f"test  {variable} {op} {eval_criterea} PASSED \nwith value: {measured_value}")
            else:
                print(Fore.RED + f"test {variable} {op} {eval_criterea} FAILED \nwith value: {measured_value}")
                return False
            # variable = evaluation[criterea]["system_value"]["variable"]
            # if result: print(Fore.GREEN + f"test  {variable} {op} {eval_criterea} PASSED \nwith value: {measured_value}")
            # else:      print(Fore.RED + f"test {variable} {op} {eval_criterea} FAILED \nwith value: {measured_value}")
            # print(Style.RESET_ALL)

        return True



    ################################################
    ############### SYSTEM TESTS ###################
    ################################################
    async def run_single_step_test(self, test: dict) -> None:
        await self.run_single_loop(test_loops=test["system_loop"])
        await self.check_outputs(evaluation=test["evaluation"])

    async def run_multi_step_test(self, test: dict): 
        """
        TODO: LOOP while the test has not completed, with some termination criterea
        for example, the user wants to read after 
        """
        print(f"test time {test["stop_time"]}")
        sim_time = 0

        simulation_status = True
        while simulation_status:
            sim_time += test["timestep"]
    
            await self.run_single_loop(test_loops=test["system_loop"])

            if await self.check_reading_conditions(test["start_readings_conditions"]):
                await self.check_outputs(test["evaluation"])
                
            if(self.check_time(sim_time, test["stop_time"])):
                simulation_status = False

    async def run_test(self, test: dict) -> None:
        """
        check_test_type
        call corresponding test
        """
        await self.reset_system()
        await self.initialize_system_variables(test=test)
        if test["test_type"] == "single_step": 
            await self.run_single_step_test(test)
        elif test["test_type"] == "multi_step": 
            await self.run_multi_step_test(test=test)
        else: 
            print(f"unknown test type {test["test_type"]}")


    async def reset_system(self) -> None:
        for client_name in self.system_clients:
            object_node = self.system_clients[client_name].get_node(ua.NodeId(1, 1))
            await object_node.call_method(ua.NodeId(1, 4))#, str(1)) # update fmu before updating values

    async def check_outputs(self, evaluation: dict[list[dict]]) -> None:

        for criterea in evaluation:
            print(evaluation[criterea], "\n", f"criterea {criterea} end")
            node = self.system_servers[evaluation[criterea]["system_value"]["fmu"]].server_variable_ids[evaluation[criterea]["system_value"]["variable"]]
            measured_value = self.system_clients[evaluation[criterea]["system_value"]["fmu"]].get_node(node)
            measured_value = await measured_value.read_value()

            print(f"checking {measured_value} {evaluation[criterea]["operator"]} {evaluation[criterea]["target"]}")
            eval_criterea = evaluation[criterea]["target"] 
            op =evaluation[criterea]["operator"] 
            result = ops[op](measured_value, eval_criterea)
            variable = evaluation[criterea]["system_value"]["variable"]

            if result: print(Fore.GREEN + f"test  {variable} {op} {eval_criterea} PASSED \nwith value: {measured_value}")
            else:      print(Fore.RED + f"test {variable} {op} {eval_criterea} FAILED \nwith value: {measured_value}")
            print(Style.RESET_ALL)

    #######################################################################
    ################   SYSTEM VARIABLE INIT   #############################
    #######################################################################
    async def initialize_system_variables(self, test:dict):
        initial_system_state = test["initial_system_state"]
        for server in initial_system_state:
            for variable in initial_system_state[server]:
                object_node = self.system_clients[server].get_node(ua.NodeId(1, 1))
                update_values = {
                    "variable": variable,
                    "value": float(initial_system_state[server][variable])
                }
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

    ############################################################################
    #######################   CLIENTS INIT   ###################################
    ############################################################################
    async def create_system_clients(self):

        for server_name in self.system_servers:
            server = self.system_servers[server_name]
            client = Client(url=server.url)
            await client.connect()
            self.system_clients[server_name] = client

        print(f"system clients clients setup: {self.system_clients}")
    
    ################################################################################
    ###########################   MAIN LOOP   ######################################
    ################################################################################
    async def main_testing_loop(self):
        tasklist = await self.initialize_fmu_opc_servers()
        await self.create_system_clients()
        print(f"TESTS = {self.tests}, \n type {type(self.tests)} \n {self.tests.keys()} \n\n")        
        for test in self.tests:
            await self.run_test(self.tests[test])
        return
        await asyncio.gather(*tasklist)

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