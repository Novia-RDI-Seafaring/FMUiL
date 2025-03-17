import asyncio
import logging
from asyncua import Server, ua
from .data_loader import DataLoaderClass
from typing import Union
import datetime

_logger = logging.getLogger(__name__)

class CentralSetup:
    def __init__(self, url_server:str, config_file:str) -> None:
        self.server = None
        self.config = DataLoaderClass(file_path=config_file).data
        self.url_server = url_server
        self.registered_nodes = {}
        self.RESERVED_VARIABLE_NAMES = ["Ns", "i", "methods"]
    
    async def create_server(self) -> Server:
        self.server = Server()
        await self.server.init()
        self.server.set_endpoint(self.url_server)

    def node_constructor(self, name) -> ua.NodeId:
        print("trying to construct ", name)
        return ua.NodeId(self.find_key(nested_dict= self.config, target_key= name)["i"] ,  self.find_key(nested_dict= self.config, target_key= name)["Ns"])
    
    async def add_opcua_object_variable(self, obj, var_name:str, var_val, var_type) -> None:
        var = await obj.add_variable(self.node_constructor(var_name), var_name, val= var_val, varianttype= var_type)  
        await var.set_writable()
        self.registered_nodes[var_name] = var

        
    async def add_root_opcua_object_variable(self, var_name:str, var_val, var_type) -> None:
        var = await self.server.nodes.root.add_variable(self.node_constructor(var_name), var_name, val= var_val, varianttype= var_type)
        await var.set_writable()
        self.registered_nodes[var_name] = var

    def check_variable_type(self, var_config_type):
            if var_config_type == "double":
                var_type = ua.VariantType.Double
            elif var_config_type == "float":
                var_type = ua.VariantType.Float
            elif var_config_type == "boolean":
                var_type = ua.VariantType.Boolean
            elif var_config_type == "int16":
                var_type = ua.VariantType.Int16
            elif var_config_type == "int32":
                var_type = ua.VariantType.Int32
            elif var_config_type == "int64":
                var_type = ua.VariantType.Int64
            else:
                raise Exception(f"object has unkown type {var_config_type}")
            
            return var_type


    def find_key(self, nested_dict:dict[dict], target_key:str) -> Union[str, None]:
        """
        Recursively searches for a key in a nested dictionary and returns its value if found.
        
        :param nested_dict: The main dictionary that may contain nested dictionaries.
        :param target_key: The key to search for.
        :return: The value associated with the key if found, otherwise None.
        """
        if isinstance(nested_dict, dict):
            if target_key in nested_dict:
                return nested_dict[target_key]
            for key, value in nested_dict.items():
                result = self.find_key(value, target_key)
                if result is not None:
                    return result
        return None

    async def initialize_server_object(self, obj_name):
        """ initializes server object and its variables """
        
        print(f"trying to register object {obj_name}")

        obj = await self.server.nodes.objects.add_object(self.node_constructor(obj_name), obj_name) 
        self.registered_nodes[obj_name] = obj

        for var in self.config[obj_name]:
            if var not in self.RESERVED_VARIABLE_NAMES:
                _logger.info(f"trying to register variable {var} under object {obj} ")
                var_type = self.check_variable_type(var_config_type= self.config[obj_name][var]["type"])
                await self.add_opcua_object_variable(obj=obj, 
                                                    var_name=var, 
                                                    var_val = self.config[obj_name][var]["initial_value"], 
                                                    var_type= var_type)        

        print(f"\n\nregistered object {obj_name} \n")

    async def register_root_variables(self): 
        
        for var in self.config["root"]:
            print(f"registering var {var}")
            if var not in self.RESERVED_VARIABLE_NAMES:

                _logger.info(f"\n!!! trying to register variable {var} under object root ")
                var_type = self.check_variable_type(var_config_type= self.config["root"][var]["type"])       
                await self.add_root_opcua_object_variable(var_name= var, var_val=self.config["root"][var]["initial_value"],var_type=  var_type)

        print(f"\n\nregistered object root \n")


    async def register_nodes_from_config(self) -> None:
        """
        Iterates over objects found in .yaml file and calls the initialization function for each
        """
        for obj in self.config.keys():
            if obj == "root": await self.register_root_variables() 
            elif obj in self.RESERVED_VARIABLE_NAMES: continue
            else:             await self.initialize_server_object(obj)



