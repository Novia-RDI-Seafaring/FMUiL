from .fmu_loader import FmuLoader
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

    @classmethod
    async def async_server_init(cls, fmu:str, port:int):
        self = cls()
        self.fmu:FmuLoader = FmuLoader(fmu_file=fmu)
        self.url = self.construct_server_url(port)
        await self.setup_sequence()
        self.idx = int(await self.server.register_namespace(self.url))
        return self
    
    def construct_server_url(self, port):
        # return f"opc.tcp://0.0.0.0:{port}/{self.fmu.fmu_name}/"
        return f"opc.tcp://localhost:{port}/{self.fmu.fmu_name}/"

    async def setup_sequence(self) -> None:
        await self.initialize_server()
        await self.setup_server_variables()


    async def initialize_server(self):
        self.server = Server()
        await self.server.init()
        self.server.set_endpoint(self.url)

    async def setup_server_variables(self):

        obj = await self.server.nodes.objects.add_object(bname = self.fmu.fmu_name, nodeid= ua.NodeId(Identifier=1, NamespaceIndex=1)) 

        for var in self.fmu.fmu_inputs:
            self.server_variables.append(var)
            var = await obj.add_variable(nodeid=ua.NodeId(var), bname=var, val=0.0)
            await var.set_writable()

        for var in self.fmu.fmu_outputs:
            self.server_variables.append(var)
            var = await obj.add_variable(nodeid=ua.NodeId(var), bname=var, val=0.0)
            await var.set_writable()
        # idx = await self.server.register_namespace(uri)

        await obj.add_method(
            ua.NodeId(2, 3),   
            "simulate",          
            self.test,           
        )

    @uamethod
    def simulate_fmu(self, value):
        time_step = 0.5
        # Updating fmu for the timestep
        self.fmu.fmu.doStep(currentCommunicationPoint=self.fmu_time, communicationStepSize=time_step)
        print("here 1l")
        self.fmu_time += time_step
        print("here 2l")

    @uamethod
    def test(self, parent: None, value:None):
        print("test method")

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


