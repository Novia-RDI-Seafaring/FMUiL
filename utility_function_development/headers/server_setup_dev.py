from .fmu_loader import FmuLoader
from asyncua import Server, ua
import asyncio
import datetime

class OPCUAFMUServerSetup:
    def __init__(self) -> None:
        self.server_started = asyncio.Event()
        self.server = None
        self.url = None
        self.server_variables = []
        self.fmu = None

    @classmethod
    async def async_server_init(cls, fmu:str, port:int):
        self = cls()
        self.fmu:FmuLoader = FmuLoader(fmu_file=fmu)
        self.url = self.construct_server_url(port)
        await self.setup_sequence()
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
        # await self.setup_sequence()
        async with self.server:
            self.server_started.set()
            while True:
                print(f"working {datetime.datetime.now()} at {self.url}")
                await asyncio.sleep(1) ######


