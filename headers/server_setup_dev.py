from headers.fmu_loader import FmuLoader
from asyncua import Server, ua
import asyncio
import datetime
from asyncua.common.methods import uamethod
from decimal import Decimal, getcontext

getcontext().prec = 8


class OPCUAFMUServerSetup:
    def __init__(self) -> None:
        self.server_started = asyncio.Event()
        self.server = None
        self.url = None
        self.server_variables = []
        self.fmu = None
        self.fmu_time = 0
        self.server_time = 0
        self.idx = None
        self.server_variable_ids = {}
        self.opc_server_only_variables = ["timestep"] # variables reserved only for the server not fmu
        self.last_simulation_timestamp = 0
        
        # resrved vairabled have a namespace=2 
        self.reserved_variable_ids = {
            "timestep": ua.NodeId(2,1),
            "server_time": ua.NodeId(2,2)
        }

    ########### SETTERS & GETTERS ########### 
    async def get_value(self, variable: str) -> None:
        node =  self.server.get_node(self.server_variable_ids[variable])
        return await node.read_value() 
    
    async def write_value(self, variable:str, value:str)->None:
        # write value to specific node in the system
        # clinet_name = client to desired server
        node_id = self.server_variable_ids[variable]
        node_to = self.server.get_node(node_id)        
        await node_to.write_value(value)    
    
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
        
        for var in self.reserved_variable_ids:
            self.server_variables.append(var)
            variable = await obj.add_variable(nodeid=self.reserved_variable_ids[var], bname=var, val=0.0)
            self.server_variable_ids[var] = self.reserved_variable_ids[var]
            await variable.set_writable()

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


    async def simulation_loop(self, server_time: float, time_step: float):
        print("1")
        
        self.fmu.fmu.doStep(currentCommunicationPoint=server_time, communicationStepSize=time_step)        
        # # ADD READ FROM THE FMU, SO AFTER THE SIMULATION THE OUTPUTS ARE ON THE OPCUA SERVER

        print("2")
        self.fmu_time += time_step
        
        print("3")

        for output in self.fmu.fmu_outputs:
            fmu_output = self.fmu.fmu.getReal([int(self.fmu.fmu_outputs[output]["id"])])
            node = self.server.get_node(self.server_variable_ids[output])
            await node.set_value(float(fmu_output[0]))
        print("end")


    @uamethod
    async def simulate_fmu(self, parent=None, value=None):
        system_timestep = value
        if value == None:
            system_timestep =Decimal(str(value))    
        system_timestep  = round(float(value), 8)  # Round to 8 decimal places
        time_step        = round(float(await self.get_value(variable="timestep")), 8)
        self.server_time = round(self.server_time + system_timestep, 8)
        self.fmu_time    = round(self.fmu_time, 8)
        
        if(self.server_time - self.fmu_time > 2 * time_step):
            print("\n\n\nSHITS WRONG\n\n\n")
        
        if(self.server_time - self.fmu_time >= time_step):
            print(f"DID !update! due to {self.server_time} - {self.fmu_time} >{time_step}")
            self.fmu.fmu.doStep(currentCommunicationPoint=self.fmu_time, communicationStepSize=time_step)
            self.fmu_time += time_step
            for output in self.fmu.fmu_outputs:
                fmu_output = self.fmu.fmu.getReal([int(self.fmu.fmu_outputs[output]["id"])])
                node = self.server.get_node(self.server_variable_ids[output])
                await node.set_value(float(fmu_output[0]))
        else:
            print(f"\n\nDID !NOT! update due to {self.server_time} - {self.fmu_time} < {time_step}\n\n")

    async def update_opc_and_fmu(self, parent, value):
        node = self.server.get_node(self.server_variable_ids[value["variable"]])
        await node.set_value(float(value["value"]))
        self.fmu.fmu.setReal([self.fmu.fmu_parameters[value["variable"]]["id"]], [float(value["value"])])
        print(f"\n\n\n\n server {self.fmu.fmu_name} WAS UPDATED")

    
    async def update_opc(self, parent, value):
        node = self.server.get_node(self.server_variable_ids[value["variable"]])
        await node.set_value(float(value["value"]))
        print(f"\n\n\n\n server {self.fmu.fmu_name} WAS UPDATED")

    @uamethod
    async def update_value_opc_and_fmu(self, parent= None, value= None):        
        value = eval(value)
        if value["variable"] in self.opc_server_only_variables:
            await self.update_opc(parent= parent, value= value)
        else:
            await self.update_opc_and_fmu(parent= parent, value= value)
            
    @uamethod
    def test(self, parent= None, value= None):
        print("test method")

    # async def reset_opc_vars(self):
    #     for variable in self.reserved_variable_ids:
    #         await self.write_value(variable= variable, value=0.0)


    @uamethod
    async def reset_fmu(self, parent= None, value = None):
        await self.write_value(variable= "server_time", value=0.0)
        self.server_time = 0
        
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


