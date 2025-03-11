from .fmu_loader import FmuLoader
from asyncua import Server, ua
import asyncio
import datetime

class OPCUAFMUServerSetup:
    def __init__(self, fmu:str, port:int):
        self.fmu:FmuLoader = FmuLoader(fmu_file=fmu)
        self.server = None
        self.url = self.construct_server_url(port)
        self.server_variables = {}

    def construct_server_url(self, port):
        return f"opc.tcp://0.0.0.0:{port}/{self.fmu.fmu_name}/"

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
            var = await obj.add_variable(nodeid=ua.NodeId(var), bname=var, val=0.0)
            await var.set_writable()

    def update_inputs(self):
        pass

    def get_outputs(self):
        pass

    def run_simulation_loop_once(self):
        pass

    def run_simulation_loop(self, time, step):
        pass

    async def main_loop(self):
        await self.setup_sequence()
        async with self.server:
            while True:
                print(f"working {datetime.datetime.now()} at {self.url}")
                await asyncio.sleep(1) ######


