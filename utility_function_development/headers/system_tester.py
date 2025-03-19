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

    # async def tranfer_value(self, transfer_list) -> None:
    #     node_from = self.system_clients[transfer_list[0][0]].get_node(ua.NodeId(transfer_list[0][1]))
    #     value = await node_from.read_value()  
    #     node_to = self.system_clients[transfer_list[1][0]].get_node(ua.NodeId(transfer_list[1][1]))
    #     await node_to.write_value(value)

    async def get_value(self, client_name: str, variable: str) -> None:
        node = self.system_clients[client_name].get_node(variable)
        return await node.read_value() 

    async def write_value(self, client_name:str, variable:str, value:str)->None:
        pass 

    ################### SYSTEM UPDATES ########################
    async def run_single_loop(self, test_loops:dict):
        """
        update loop, passing outputs from one fmu to another
        1) Updates fmu1 to get the most recent values
        2) For every I/O perform the value transfer
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
            
            # updating I/Os after system update
            for io_update in test_loops[obj]:
                
                # reading value we're interested in
                val = await self.get_value(client_name= obj, variable= self.system_servers[obj].server_variable_ids[io_update[0][0]])

                # construction of update
                object_node = self.system_clients[obj].get_node(ua.NodeId(1, 1))
                update_values = {
                    "variable": io_update[0][0],
                    "value": float(val)
                }


                await object_node.call_method(ua.NodeId(1, 3), str(update_values))
                value = await self.get_value(client_name= obj, variable= self.system_servers[obj].server_variable_ids[io_update[0][0]])

                # writing to variable
                node_id = self.system_servers[io_update[1][0]].server_variable_ids[io_update[1][1]]
                node_to = self.system_clients[io_update[1][0]].get_node(node_id)
                await node_to.write_value(value)    

    async def run_single_step_test(self, test: dict) -> any: 
        await self.run_single_loop(test_loops=test["system_loop"])
        await self.check_outputs(evaluation=test["evaluation"])
        # exit()

    async def check_outputs(self, evaluation: dict[list[dict]]):

        for criterea in evaluation:
            print(evaluation[criterea], "\n", f"crite rea {criterea} end")
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

    async def run_multi_step_test(self, test: dict): 
        await self.run_single_loop(test_loops=test["system_loop"])


    async def run_test(self, test: dict) -> None:
        """
        check_test_type
        call corresponding test
        """
        await self.initialize_system_variables(test=test)
        if test["test_type"] == "single_step": 
            await self.run_single_step_test(test)
        else: 
            print(f"unknown test type {test["test_type"]}")


    async def update_value(self, client, var_name, value):
        variable = client.get_node(ua.NodeId(var_name))
        await variable.write_value(value)


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
    ########################   SERVER INIT   ###################################
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
    
    ################################################################################
    ###########################   MAIN LOOP   ######################################
    ################################################################################
    async def main_testing_loop(self):
        tasklist = await self.initialize_fmu_opc_servers()
        await self.create_system_clients()
        print(f"TESTS = {self.tests}, \n type {type(self.tests)} \n {self.tests.keys()} \n\n")        
        for test in self.tests:
            await self.run_test(self.tests[test])
        
        await asyncio.gather(*tasklist)

        