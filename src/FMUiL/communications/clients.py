from asyncua import Client, ua
import logging
import asyncio
import sys

class client_manager:
    @classmethod
    async def create(cls, internal_servers, external_servers, node_ids):
        self = cls()
        
        self.internal_servers = internal_servers
        self.external_servers = external_servers
        self.node_ids = node_ids
        
        self.internal_clients     = {} 
        self.external_clients   = {}
        
        await self.create_internal_clients()
        await self.create_external_clients()
        
        return self
    

    async def create_internal_clients(self) -> None:
        for server_name in self.internal_servers:
            server = self.internal_servers[server_name]
            client = Client(url=server.url)

            # This should never fail, since we are creating the servers ourselves
            try:
                await client.connect()
                self.internal_clients[server_name] = client
                logging.info(f"Connected to server {server_name} at {server.url}")
            except Exception as e:
                logging.error(f"Failed to connect to server {server_name} at {server.url}: {e}")
        
    async def create_external_clients(self) -> None:
        # TODO: REMOVE SYSTEM NODE ID INITIALIZATION FROM HERE, SEPARATE THE FUNCTIONALITY
        for server in self.external_servers:
            server_url = self.external_servers[server]["url"]
            print(f"TRYING TO CONNECT TO {server_url} ")
            client = Client(url=server_url)

            # This can fail, since we are connecting to an user defined server
            try:
                await client.connect()
                self.external_clients[server] = client
                self.node_ids[server] = {}
                for obj in self.external_servers[server]["objects"]:
                    for var in self.external_servers[server]["objects"][obj]:
                        var_data = self.external_servers[server]["objects"][obj][var]
                        keys = var_data.keys()
                        if "name" in keys and var_data["name"] is not None:
                            self.node_ids[server][var] = ua.NodeId(self.external_servers[server]["objects"][obj][var]["name"])
                        elif("id" in keys and "ns" in keys):
                            id = self.external_servers[server]["objects"][obj][var]["id"]
                            ns = self.external_servers[server]["objects"][obj][var]["ns"]                            
                            self.node_ids[server][var] = ua.NodeId(Identifier= id, NamespaceIndex= ns)
                        else:
                            raise Exception(f"server {server} with object {obj} found no acceptable id namespace or name for variable {var}")
                        
            # In the future this could be changed to move to the next experiment if an expection happens
            except Exception as e:
                logging.error(f"Failed to connect to server {server} at {server_url}: {e}")
                sys.exit(1)

    def get_client(self, client_name)->Client:
        if client_name in self.internal_clients.keys():     return self.internal_clients[client_name]
        elif client_name in self.external_clients.keys(): return self.external_clients[client_name]
        else: raise Exception(f"UNKNOWN CLIENT {client_name}")
    
    async def get_system_values(self) -> dict:
            print(self.internal_clients.keys())
            return self.internal_clients.keys()
            
    async def reset_system(self) -> None:
        for client_name in self.internal_clients:
            object_node = self.internal_clients[client_name].get_node(ua.NodeId(1, 1))
            await object_node.call_method(ua.NodeId(1, 4))

    async def initialize_system_variables(self, experiment:dict) -> None:
        """
        initialize system variables base on input state
        uses user defined initial state
        """
        initial_system_state = experiment["initial_system_state"]
        for server in initial_system_state:
            for variable in initial_system_state[server]:
                object_node = self.internal_clients[server].get_node(ua.NodeId(1, 1))
                update_values = {
                    "variable": variable,
                    "value": float(initial_system_state[server][variable])
                }
                await object_node.call_method(ua.NodeId(1, 3), str(update_values)) 

    async def close(self) -> None:
        """ 
        disconnects all clients to enable the setup of new ones
        releases ports
        """
        if(len(self.external_clients)):
            await asyncio.gather(
                *(c.disconnect() for c in self.external_clients.values()),
            )
            self.external_clients.clear()
        
        if(len(self.internal_clients)):    
            await asyncio.gather(
                *(c.disconnect() for c in self.internal_clients.values()),
            )
            self.internal_clients.clear()
            