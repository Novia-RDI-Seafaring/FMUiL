from FMUiL.handlers import ExternalServerHandler
from FMUiL.communications.server_setup import InternalServerSetup
from pathlib import Path
import asyncio

class server_manager:
    # TODO: pass directly "FMU FILES" not whole experiment config file
    # TODO: add 
    @classmethod
    async def create(cls, experiment_config, port):
        self = cls()
        self.remote_servers = self.construct_remote_servers(experiment_config["external_servers"])
        self.fmu_files = experiment_config["fmu_files"]
        self._tasks: list[asyncio.Task] = []
        self.internal_servers: dict[str, InternalServerSetup] = {}
        self.base_port = port
        await self.initialize_fmu_opc_servers()
        return self
    
    def construct_remote_servers(self, remote_servers: list[str]) -> dict[str:ExternalServerHandler]:
        """
        remote_servers = path to directory with remote server definitions
        this function iterates through all of them and adds them to a dictionaty in a structured manner
        """
        server_dict = {}

        for server_name in remote_servers:
            server_desription = ExternalServerHandler(server_name).dump_dict()
            name = Path(server_name).stem
            server_dict[name] = server_desription
            
        return server_dict

    async def initialize_fmu_opc_servers(self) -> None:
        for fmu_file in self.fmu_files:            
            self.base_port+=1
            server =  await InternalServerSetup.async_server_init(
                fmu=fmu_file, 
                port=self.base_port
            )
            server_task = asyncio.create_task(server.main_loop())
            await server.server_started.wait()
            server.server_started.clear()
            self.internal_servers[server.fmu.fmu_name] = server
            self._tasks.append(server_task)
        
    async def close(self) -> None:
        """Stop all servers and free the ports."""
        for srv in self.internal_servers.values():
            await srv.server.stop()          # closes socket listener
        for t in self._tasks:                # background loops
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self.internal_servers.clear()