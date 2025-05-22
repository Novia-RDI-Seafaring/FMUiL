from headers.config_loader import DataLoaderClass
from pathlib import Path
from headers.server_setup_dev import OPCUAFMUServerSetup
import asyncio
import os

class server_manager:
    @classmethod
    async def create(cls, test_config, remote_server_directory):
        self = cls()
        self.remote_server_directory = remote_server_directory
        self.remote_servers = self.construct_remote_servers(test_config["external_servers"])
        self.fmu_files = test_config["fmu_files"]
        self.system_servers = {}
        self.base_port = 7000
        await self.initialize_fmu_opc_servers() 
        return self
    
    def construct_remote_servers(self, remote_servers):
        """
        remote_servers = path to directory with remote server definitions
        this function iterates through all of them and adds them to a dictionaty in a structured manner
        """
        server_dict = {}
        server_files = [os.path.join(self.remote_server_directory, i) for i in remote_servers]

        for server_name in server_files:
            server_desription = DataLoaderClass(server_name).data
            name = Path(server_name).stem
            server_dict[name] = server_desription
            
        return server_dict


    async def initialize_fmu_opc_servers(self):
        
        tasklist = []
        
        for fmu_file in self.fmu_files:
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

