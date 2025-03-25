from headers.fmu_loader import FmuLoader
from asyncua import Server, ua
import asyncio
import datetime
from asyncua.common.methods import uamethod


class OPCUAFMUServerSetup:
    def __init__(self) -> None:
        self.server_started = asyncio.Event()
        self.server = None
        self.url = None
        self.server_variables = []
        self.fmu = None
        self.fmu_time = 0
        self.idx = None
        self.server_variable_ids = {}

    @classmethod
    async def async_server_init(cls, fmu:str, port:int):
        self = cls()
        self.fmu:FmuLoader = FmuLoader(fmu_file=fmu)
        self.url = self.construct_server_url(port)
        await self.setup_sequence()
        self.idx = int(await self.server.register_namespace(self.url))
        return self
    
    def construct_server_url(self, port):
        return f"opc.tcp://localhost:{port}/{self.fmu.fmu_name}/"

    async def setup_sequence(self) -> None:
        await self.initialize_server()
        await self.setup_server_variables()


    async def initialize_server(self):
        self.server = Server()
        await self.server.init()
        self.server.set_endpoint(self.url)

    async def setup_server_variables(self):

        obj = await self.server.nodes.objects.add_object(bname = self.fmu.fmu_name, 
                                                         nodeid= ua.NodeId(Identifier=1, NamespaceIndex=1)) 
        
        self.server_variable_ids[self.fmu.fmu_name] = ua.NodeId(Identifier=1, NamespaceIndex=1)

        for var in self.fmu.fmu_inputs:
            self.server_variables.append(var)
            variable = await obj.add_variable(nodeid=ua.NodeId(var), bname=var, val=0.0)
            self.server_variable_ids[var] = ua.NodeId(var)
            await variable.set_writable()

        for var in self.fmu.fmu_outputs:
            self.server_variables.append(var)
            variable = await obj.add_variable(nodeid=ua.NodeId(var), bname=var, val=0.0)
            self.server_variable_ids[var] = ua.NodeId(var)
            await variable.set_writable()

        #######################################################
        ####### STANDARD METHODS FOR ALL OFJBECTS #############
        #######################################################
        
        ######### simulation #########
        await obj.add_method(
            ua.NodeId(1, 2),   
            "simulate",          
            self.simulate_fmu,           
        )

        ######### value update for fmu and opc #########
        await obj.add_method(
            ua.NodeId(1, 3),   
            "update",          
            self.update_value_opc_and_fmu,           
        )

        ######### value update for fmu and opc #########
        await obj.add_method(
            ua.NodeId(1, 4),   
            "reset_fmu",          
            self.reset_fmu,           
        )

        await obj.add_method(
            ua.NodeId(1, 5),   
            "reset_fmu",          
            self.test,           
        )

    @uamethod
    async def simulate_fmu(self, parent:None, value:None):
        # TODO: make the "value" variable the one in the timestep 
        time_step = 1.0
        # Updating fmu for the timestep
        self.fmu.fmu.doStep(currentCommunicationPoint=self.fmu_time, communicationStepSize=time_step)
        # ADD READ FROM THE FMU, SO AFTER THE SIMULATION THE OUTPUTS ARE ON THE OPCUA SERVER
        self.fmu_time += time_step
        for output in self.fmu.fmu_outputs:
            fmu_output = self.fmu.fmu.getReal([int(self.fmu.fmu_outputs[output]["id"])])
            node = self.server.get_node(self.server_variable_ids[output])
            await node.set_value(float(fmu_output[0]))

    @uamethod
    async def update_value_opc_and_fmu(self, parent= None, value= None):
        value = eval(value)
        node = self.server.get_node(self.server_variable_ids[value["variable"]])
        await node.set_value(float(value["value"]))
        self.fmu.fmu.setReal([self.fmu.fmu_parameters[value["variable"]]["id"]], [float(value["value"])])
        print(f"\n\n\n\n server {self.fmu.fmu_name} WAS UPDATED")

    @uamethod
    def test(self, parent= None, value= None):
        print("test method")

    @uamethod
    async def reset_fmu(self, parent= None, value = None):
        self.fmu_time = 0
        self.fmu.fmu.reset()
        self.fmu.fmu.instantiate()
        self.fmu.fmu.enterInitializationMode()
        self.fmu.fmu.exitInitializationMode()
        print(f"fmu {self.fmu.fmu_name} was resetted")

    def get_server_description(self):
        return {self.fmu.fmu_name: self.server_variables}

    def update_inputs(self):
        pass

    def get_outputs(self):
        pass

    def run_simulation_loop_once(self):
        pass

    def run_simulation_loop(self, time, step):
        pass

    async def main_loop(self):
        async with self.server:
            self.server_started.set()
            while True:
                print(f"working {datetime.datetime.now()} at {self.url}")
                await asyncio.sleep(1) ######


