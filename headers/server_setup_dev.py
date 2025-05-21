from headers.fmu_loader import FmuLoader
from asyncua import Server, ua
import asyncio
import datetime
from asyncua.common.methods import uamethod
import logging
# logging.basicConfig(level=logging.INFO) # required to get messages printed out
logger = logging.getLogger(__name__)
from decimal import Decimal, getcontext, ROUND_HALF_UP

getcontext().prec = 8
PRECISION_STR = "0.000001"
COMPARISON_PRECISION = Decimal("0.000001")



class OPCUAFMUServerSetup:
    def __init__(self) -> None:
        self.server_started = asyncio.Event()
        self.server = None
        self.url = None
        self.server_variables = []
        self.fmu = None
        self.fmu_time    = Decimal("0.0")
        self.server_time = Decimal("0.0")
        self.idx = None
        self.server_variable_ids = {}
        self.opc_server_only_variables = ["timestep"] # variables reserved only for the server not fmu
        self.last_simulation_timestamp = 0.0
        
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

        await self.setup_standard_methods(obj= obj)
    
    #######################################################
    ####### STANDARD METHODS FOR ALL OFJBECTS #############
    #######################################################
    async def setup_standard_methods(self, obj):
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


    async def single_simulation_loop(self):
        time_step = Decimal(await self.get_value(variable="timestep")).quantize(Decimal(PRECISION_STR))

        # logger.info(f"DID update due to {self.server_time} - {self.fmu_time}:  > {time_step}")
        self.fmu.fmu.doStep(
            currentCommunicationPoint=self.fmu_time,
            communicationStepSize=time_step
            )
        self.fmu_time += time_step
    
        for output in self.fmu.fmu_outputs:
            output_id = int(self.fmu.fmu_outputs[output]["id"])
            fmu_output = self.fmu.fmu.getReal([output_id])
            node = self.server.get_node(self.server_variable_ids[output])
            await node.set_value(float(fmu_output[0]))
            # print(f"\n\n var {output} with val {fmu_output} passed to  {output}, {self.server_variable_ids[output]} \n\n")
            

    @uamethod
    async def simulate_fmu(self, parent=None, value: str = None):
        try:
            # Convert inputs to Decimal with defined precision
            system_timestep = Decimal(value).quantize(Decimal(PRECISION_STR), rounding=ROUND_HALF_UP)
            time_step = Decimal(await self.get_value(variable="timestep")).quantize(Decimal(PRECISION_STR), rounding=ROUND_HALF_UP)
            self.server_time += system_timestep

            # print(f"system_timestep = {system_timestep}, time_step = {time_step}, server_time = {self.server_time}, fmu_time = {self.fmu_time}")

            time_diff = (self.server_time - self.fmu_time).quantize(Decimal(PRECISION_STR), rounding=ROUND_HALF_UP)
            double_step = (2 * time_step).quantize(Decimal(PRECISION_STR), rounding=ROUND_HALF_UP)

            if time_diff > double_step:
                logger.warning(
                    f"\n\n\\SOMETHING IS WRONG with timing: the gap is double the step time "
                    f"{time_diff} > {double_step}\n\n"
                )

            if time_diff >= time_step:
                await self.single_simulation_loop()
            else:
                logger.info(
                    f"DID !NOT! update due to {self.server_time} - {self.fmu_time}: "
                    f"{self.server_time - self.fmu_time} < {time_step}"
                )
        except Exception as e:
            logger.error(f"Exception in simulate_fmu: {e}")


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


