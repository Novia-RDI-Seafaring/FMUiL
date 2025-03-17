import asyncio
from headers.server_setup_dev import OPCUAFMUServerSetup
from headers.config_loader import DataLoaderClass
from asyncua import Client, ua
import asyncua
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

    async def tranfer_value(self, transfer_list):
        node_from = self.system_clients[transfer_list[0][0]].get_node(ua.NodeId(transfer_list[0][1]))
        value = await node_from.read_value()  
        node_to = self.system_clients[transfer_list[1][0]].get_node(ua.NodeId(transfer_list[1][1]))
        await node_to.write_value(value)

    ################### SYSTEM UPDATES ########################
    async def run_single_loop(self, test_loops):
        # print("looop = ",test_loops)
        for obj in test_loops:
            # doing 1 update to the object fmu
            # print(f" updatring {obj}\n\n") 
            client = self.system_clients[obj]
            object_node = client.get_node(ua.NodeId(1, 1))
            await object_node.call_method(ua.NodeId(1, 2), 1) # update fmu before updating values
            
            # updating I/Os after system update
            for io_update in test_loops[obj]:
                # print(f"io_update[0]from {obj} reading {io_update[0][0]}")
                # node_from = self.system_clients[obj].get_node(ua.NodeId(io_update[0][0]))
                # print("var ids", self.system_servers[obj].server_variable_ids)
                node_from = self.system_clients[obj].get_node(self.system_servers[obj].server_variable_ids[io_update[0][0]])
                # print(f"node {node_from}")
                val = await node_from.read_value()

                object_node = self.system_clients[obj].get_node(ua.NodeId(1, 1))
                update_values = {
                    "variable": io_update[0][0],
                    "value": float(val)
                }
                await object_node.call_method(ua.NodeId(1, 3), str(update_values))
                # await object_node.call_method(ua.NodeId(1, 3), str(update_values)) # update fmu before updating values


                value = await node_from.read_value()  
                # print(f"node from = {node_from} value {value} \n\n\n")
                node_id = self.system_servers[io_update[1][0]].server_variable_ids[io_update[1][1]]

                node_to = self.system_clients[io_update[1][0]].get_node(node_id)
                await node_to.write_value(value)


    async def run_single_step_test(self, test: dict): 
        await self.run_single_loop(test_loops=test["system_loop"])
        # check outputs
        # pass


    async def run_multi_step_test(self, test: dict): 
        await self.run_single_loop(test_loops=test["system_loop"])
        # check outputs
        # pass

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
                # exit()
                # await self.update_value(client= self.system_clients[server], 
                                        # var_name= variable, 
                                        # value= float(initial_system_state[server][variable]))


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
    ########################   CLIENT INIT   ###################################
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
        
async def main(funciton):
    conf = "TESTS/system_config.yaml"
    tests = TestSystem(config_file=conf)
    if   funciton == "test":     await tests.main_testing_loop()
    elif funciton == "describe": await tests.describe_system()

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == '-func':
        asyncio.run(main(funciton=args[1]))
    else:
        print("args reuqired '-func' and it can be rither 'test' or 'describe' ")
            
"""

var ids {'LOC_SYSTEM': NodeId(Identifier=1, NamespaceIndex=1, NodeIdType=<NodeIdType.FourByte: 1>), 
'INPUT_temperature_cold_circuit_inlet': NodeId(Identifier='INPUT_temperature_cold_circuit_inlet', NamespaceIndex=0, 
NodeIdType=<NodeIdType.String: 3>), 'INPUT_massflow_cold_circuit': NodeId(Identifier='INPUT_massflow_cold_circuit', NamespaceIndex=0, NodeIdType=<NodeIdType.String: 3>), 'INPUT_engine_load_0_1': NodeId(Identifier='INPUT_engine_load_0_1', NamespaceIndex=0, NodeIdType=<NodeIdType.String: 3>), 'INPUT_control_valve_position': NodeId(Identifier='INPUT_control_valve_position', NamespaceIndex=0, NodeIdType=<NodeIdType.String: 3>), 'OUTPUT_temperature_cold_circuit_outlet': NodeId(Identifier='OUTPUT_temperature_cold_circuit_outlet', NamespaceIndex=0, NodeIdType=<NodeIdType.String: 3>), 'OUTPUT_massflow_cold_circuit': NodeId(Identifier='OUTPUT_massflow_cold_circuit', NamespaceIndex=0, NodeIdType=<NodeIdType.String: 3>), 
'OUTPUT_temperature_lube_oil': NodeId(Identifier='OUTPUT_temperature_lube_oil', NamespaceIndex=0, NodeIdType=<NodeIdType.String: 3>)}

"""