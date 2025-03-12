import asyncio
from headers.server_setup_dev import OPCUAFMUServerSetup
from headers.config_loader import DataLoaderClass
from asyncua import Client, ua
import sys

class TestSystem:
    def __init__(self, config_file:str):
        self.config = DataLoaderClass("TESTS/system_config.yaml")
        self.fmu_files = self.config.data["fmu_files"]
        self.tests     = self.config.data["tests"]        
        self.base_port = 7000
        self.system_description = {}
        self.system_servers = {}
        self.system_clients = {}


    # async def read_value(self, client:Client, var_name:str):
    #     node = client.get_node(self.node_constructor(var_name))
    #     return await node.read_value()  
    async def tranfer_value(self, transfer_list):
        node_from = self.system_clients[transfer_list[0][0]].get_node(ua.NodeId(transfer_list[0][1]))
        value = await node_from.read_value()  
        node_to = self.system_clients[transfer_list[1][0]].get_node(ua.NodeId(transfer_list[1][1]))
        await node_to.write_value(value)

    ################### SYSTEM UPDATES ########################
    # async def update_value(self, client, var_name, value):
    #     variable = client.get_node(self.node_constructor(var_name))
    #     await variable.write_value(value)

    async def run_single_loop(self, loop):
        for step in loop:
            print(f"loop step {step}")
            await self.tranfer_value(transfer_list=step)



    async def run_single_step_test(self, test: dict): 
        await self.run_single_loop(loop=test["system_loop"])
        # check if reading conditions are met
        # check output

    async def run_test(self, test: dict) -> None:
        """
        check_test_type
        call corresponding test
        """
        await self.initialize_system_variables(test=test)
        # if test["test_type"] == "single_step": 
        #     await self.run_single_step_test(test)
        # else: 
        #     print(f"unknown test type {test["test_type"]}")
        

    async def initialize_fmu_opc_servers(self):
        
        tasklist = []
        
        for i in self.fmu_files:
            print("intializing : ", i)
            self.base_port+=1
            
            server =  await OPCUAFMUServerSetup.async_server_init(
                fmu=i, 
                port=self.base_port
            )
            server_task = asyncio.create_task(server.main_loop())
            await server.server_started.wait()
            server.server_started.clear()

            self.system_servers[server.fmu.fmu_name] = server
            tasklist.append(server_task)
            # tasklist.append(asyncio.create_task(server.main_loop()))

        return tasklist

    async def update_value(self, client, var_name, value):
        variable = client.get_node(ua.NodeId(var_name))
        await variable.write_value(value)


    async def initialize_system_variables(self, test:dict):
        initial_system_state = test["initial_system_state"]
        for server in initial_system_state:
            for variable in initial_system_state[server]:
                await self.update_value(client= self.system_clients[server], 
                                        var_name= variable, 
                                        value= float(initial_system_state[server][variable]))


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
        for i in tasklist:
            await i
    
    #################################################################################
    ###########################   MAIN LOOP   ######################################
    #################################################################################
    async def main_testing_loop(self):
        tasklist = await self.initialize_fmu_opc_servers()
        await self.create_system_clients()
        print(f"TESTS = {self.tests}, \n type {type(self.tests)} \n {self.tests.keys()} \n\n")        
        for test in self.tests:
            await self.run_test(self.tests[test])
        await asyncio.gather(*tasklist)
        # for i in tasklist:
        #     await i


        
async def main(funciton):
    conf = "TESTS/system_config.yaml"
    tests = TestSystem(config_file=conf)
    if funciton == "test":
        await tests.main_testing_loop()
    elif funciton == "describe":
        await tests.describe_system()

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == '-func':
        asyncio.run(main(funciton=args[1]))
            
