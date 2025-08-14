import asyncio
from .server_setup_dev import OPCUAFMUServerSetup
from .config_loader import DataLoaderClass
from asyncua import Client, ua
import os
from pathlib import Path
from colorama import Fore, Style
from .operations import ops
from decimal import getcontext
import logging
from .connections import parse_connections # Connection
import time
from time import gmtime, strftime
logging.basicConfig(level=logging.ERROR) # required to get messages printed out
logger = logging.getLogger(__name__)
import re
from .infra.servers import server_manager
from .infra.clients import client_manager

getcontext().prec = 8
DEFAULT_BASE_PORT = 7000 # port from which the server initialization begins
DEFAULT_LOGGER_HEADER = "test_name, evaluation_name, evaluation_function, measured_value, test_result, system_timestamp\n"

class TestSystem:
    def __init__(self, config_folder:str) -> None:
        self.config_directory        = config_folder
        self.log_file    = self.generate_logfile()
        self.config      = None 
        self.fmu_files   = None
        self.test        = None
        self.save_logs   = None
        self.timing      = None
        self.connections = None # description of system loop definition from test
        self.server_obj  = None
        self.reading_condition_dict  = {}
        self.evaluation_equation_dic = {}
        self.system_description      = {}
        self.system_node_ids         = {} # this is meant to take in all of the systems node id's
        self.regex_parser_pattern    = r'\d+\.\d+|\d+|[a-zA-Z_][\w]*|[<>!=]=?|==|!=|[^\s\w\.]'

    def generate_logfile(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        file_path = os.path.join("logs", strftime("%Y_%m_%d_%H_%M_%S", gmtime()))
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                file.write(DEFAULT_LOGGER_HEADER)
        return file_path    
    
    def log_result(self, criterea, measured_value, evaluation_result, simulation_time):
        system_output = f"{self.config['test']['test_name']},\
            {criterea},\
            {self.evaluation_equation_dic[criterea]['target_obj']}.{self.evaluation_equation_dic[criterea]['target_var']} {self.evaluation_equation_dic[criterea]['operator']} {self.evaluation_equation_dic[criterea]['value']},\
            {measured_value},\
            {evaluation_result},\
            {simulation_time}\n"
        self.log_system_output(output= system_output)
    
        
    ########### SETTERS & GETTERS ########### 
    async def get_value(self, client_name: str, variable: ua.NodeId) -> None:
        client = self.client_obj.fetch_appropriacte_client(client_name=client_name)
        node = client.get_node(variable)
        return await node.read_value() 

    async def write_value(self, client_name:str, variable:str, value:str)->None:
        """
            write value to specific node in the system
            clienet_name = client to desired server
        """
        # if it's part of the systems servers
        if (client_name in self.server_obj.system_servers):
                object_node = self.client_obj.system_clients[client_name].get_node(ua.NodeId(1, 1))
                update_values = {
                    "variable": variable,
                    "value": value
                }
                await object_node.call_method(ua.NodeId(1, 3), str(update_values)) # update fmu before updating values
        
        # if it's an external server
        else:
            node_id = self.client_obj.system_node_ids[client_name][variable]
            client = self.client_obj.fetch_appropriacte_client(client_name=client_name)
            node = client.get_node(node_id)
            datavalue1 = await node.read_data_value()
            variant1 = datavalue1.Value
            await node.write_value(ua.DataValue(ua.Variant(value, variant1.VariantType)))            
            
    async def run_system_updates(self, timestep):
        for key in self.client_obj.system_clients.keys():
            client = self.client_obj.system_clients[key]
            object_node = client.get_node(ua.NodeId(1, 1))
            await object_node.call_method(ua.NodeId(1, 2), str(float(timestep)))
        return
    
    ################### SYSTEM UPDATES ########################
    async def run_single_loop(self):
        """
        update loop, passing outputs from one fmu to another
        1) Updates fmu1 to get the most recent values
        2) For every I/O perform the value transfer

        *NOTE: the function performs transfer and updates both FMU and Server variable
        ________                      ________
        |      |*OUTPUT1 ====> INPUT1*|      |
        | fmu1 |*OUTPUT2 ====> INPUT2*| fmu2 |
        |______|*OUTPUT3 ====> INPUT3*|______|
        """
        for update in self.connections:
            # get nodeid of the source variable
            value_nodid = self.system_node_ids[update.from_fmu][update.from_var]
            # get the value using the nodeid
            value = await self.get_value(client_name= update.from_fmu, variable= value_nodid)

            # write it to the targer value
            await self.write_value(
                client_name = update.to_fmu,
                variable    = update.to_var,
                value       = value
            )
            
            logger.info(f"\n\n passed fmu {update.from_fmu} var {update.from_var} with {value}, to fmu {update.to_fmu} var {update.to_var} \n\n")


    async def check_reading_conditions(self, conditions):
        """
        checks that the conditions required to start readings are met
        """
        for condition in self.reading_condition_dict:
            node = self.system_node_ids[self.reading_condition_dict[condition]["target_obj"]][self.reading_condition_dict[condition]["target_var"]]
            measured_value = self.client_obj.system_clients[self.reading_condition_dict[condition]["target_obj"]].get_node(node)
            measured_value = await measured_value.read_value()
            eval_criterea = self.reading_condition_dict[condition]["value"] 
            op            = self.reading_condition_dict[condition]["operator"]
            result        = ops[op](measured_value, eval_criterea) 
            variable      = self.reading_condition_dict[condition]["target_var"]

            if result:  logger.info(Fore.GREEN + f"condition  {variable} {op} {eval_criterea}  PASSED \nwith value: {measured_value}")
            else:       logger.info(Fore.RED + f"condition {variable} {op} {eval_criterea} FAILED \nwith value: {measured_value}")

            return result
        
    ################################################
    ############### SYSTEM TESTS ###################
    ################################################
    async def run_multi_step_test(self, test: dict):
        """
        Executes the test while regulating time according to test["timing"]:
        - "simulation_time": advances time instantly
        - "real_time": waits so each step aligns with real wall-clock time
        """
        sim_time = 0.0
        simulation_status = True
        # TODO: PUT IN SETUP
        timestep = float(test["timestep"])  # assumed constant across system

        print(f"""Starting simulation:
        Test: {self.test['test_name']}
        FMU's: {self.fmu_files}
        Simulating""", end="", flush=True)

        while simulation_status:
            start_wall_time = time.time()

            # Update all FMUs with one timestep into the future
            await self.run_system_updates(timestep=timestep)

            # Pass data between FMUs
            await self.run_single_loop()

            # Evaluation logic
            if await self.check_reading_conditions(test["start_readings_conditions"]):
                await self.check_outputs(test["evaluation"], simulation_time=sim_time)

            # Time advancement
            sim_time += timestep

            if self.timing == "real_time":
                await self.regulate_timestep(start_time= start_wall_time, timestep= timestep)
            
            print(".", end="", flush=True)

            if sim_time > test["stop_time"]:
                simulation_status = False
                print("Simulation ended\n\n ")

    async def regulate_timestep(self, start_time: float, timestep: float):
        elapsed = time.time() - start_time
        sleep_duration = timestep - elapsed
        if sleep_duration > 0:
            await asyncio.sleep(sleep_duration)
        elif sleep_duration < 0:
            logger.error("DURANTION OF LOOP EXCEEDS TIMESTEP UNSTABLE SYSTEM!!!!!!")
            # ADD MESSAGE TO LOG FILES
            
            
    async def run_test(self) -> None:
        """
        check_test_type
        call corresponding test
        """
        # reset and initialize system variables for every test
        await self.client_obj.reset_system() 
        await self.client_obj.initialize_system_variables(test=self.test)
        # parses system_loop section of the test and stores it to use it as the system loop
        print("Parsing connections...") 
        self.connections = parse_connections(self.test["system_loop"])
        await self.run_multi_step_test(test=self.test)

    def log_system_output(self, output):
        with open(self.log_file, 'a') as file:            
            file.write(output)

    #######################################################################
    ################   CHECK SYSTEM OUTPUTS   #############################
    #######################################################################
    async def check_outputs(self, evaluation: dict[list[dict]], simulation_time) -> None:
        """
        evaluation of system outputs, this function reads the "evaluation" section of the yaml file
        """
        for criterea in self.evaluation_equation_dic:
            node = self.system_node_ids[self.evaluation_equation_dic[criterea]["target_obj"]][self.evaluation_equation_dic[criterea]["target_var"]]
            measured_value = self.client_obj.system_clients[self.evaluation_equation_dic[criterea]["target_obj"]].get_node(node)
            measured_value = await measured_value.read_value()
            target_value = self.evaluation_equation_dic[criterea]["value"]
            op = self.evaluation_equation_dic[criterea]["operator"] 
            
            # compare the two values
            evaluation_result = ops[op](measured_value, target_value)
            variable = self.evaluation_equation_dic[criterea]["target_var"]

            if evaluation_result: logger.info(Fore.GREEN + f"test {variable} {op} {self.evaluation_equation_dic[criterea]['value']} = {evaluation_result} \n PASSED with value: {measured_value}")
            else:                 logger.info(Fore.RED   + f"test {variable} {op} {self.evaluation_equation_dic[criterea]['value']} = {evaluation_result} \n FAILED with value: {measured_value}")
            
            if self.save_logs:
                self.log_result(criterea          = criterea, 
                                measured_value    = measured_value, 
                                evaluation_result = evaluation_result, 
                                simulation_time   = simulation_time)
            
            logger.info(Style.RESET_ALL)


    ###########################################################################
    #####################   INIT SYSTEM IDS   #################################
    ###########################################################################
    def gather_system_ids(self):
        for server_name in self.server_obj.system_servers:
            self.system_node_ids[server_name] = self.server_obj.system_servers[server_name].server_variable_ids

    
    # TODO: combine the functions bellow somehow
    def parse_reading_conditions(self, conditions_dict):
        #print("\n\n\n\n\n conditions dict: ", conditions_dict)
        print("Parsing reading conditions...")
        self.reading_condition_dict = {}
        for condition in conditions_dict:
            self.reading_condition_dict[condition] = {}
            self.reading_condition_dict[condition]["target_obj"], \
            self.reading_condition_dict[condition]["target_var"], \
            self.reading_condition_dict[condition]["operator"], \
            self.reading_condition_dict[condition]["value"] = re.findall(self.regex_parser_pattern, conditions_dict[condition])    
            # converstion from str to float
            self.reading_condition_dict[condition]["value"] = float(self.reading_condition_dict[condition]["value"])        
        #print(self.reading_condition_dict)

    def parse_evaluation_conditions(self, evalutaion_dict):
        print("Parsing evaluation conditions...")
        self.evaluation_equation_dic = {}
        for condition in evalutaion_dict:
            #print("evaluation   condition ", evalutaion_dict[condition], " regex: ", re.findall(self.regex_parser_pattern, evalutaion_dict[condition])   )
            self.evaluation_equation_dic[condition] = {}
            self.evaluation_equation_dic[condition]["target_obj"], \
            self.evaluation_equation_dic[condition]["target_var"], \
            self.evaluation_equation_dic[condition]["operator"], \
            self.evaluation_equation_dic[condition]["value"] = re.findall(self.regex_parser_pattern, evalutaion_dict[condition])    
            # converstion from str to float
            self.evaluation_equation_dic[condition]["value"] = float(self.evaluation_equation_dic[condition]["value"])
        
        #print("eval cond",self.evaluation_equation_dic)

    async def initialize_test_params(self, test):
            print("Initializing test parameters...")
            self.config    = DataLoaderClass(test).data
            self.fmu_files = self.config["fmu_files"]
            self.test      = self.config["test"]        
            self.timing    = self.test["timing"]
            self.save_logs = self.test["save_logs"]
            self.parse_reading_conditions(self.config["test"]["start_readings_conditions"])
            self.parse_evaluation_conditions(self.config["test"]["evaluation"])
            
    ################################################################################
    ###########################   MAIN LOOP   ######################################
    ################################################################################
    async def main_testing_loop(self):
        # initialize fmu servers, clients and vairable id storage
        # TODO: read only .yaml files
        test_files = [os.path.join(self.config_directory, i) for i in os.listdir(self.config_directory)]

        for test_file in test_files:
            await self.initialize_test_params(test= test_file)
            self.server_obj = await server_manager.create(test_config= self.config)
            self.gather_system_ids()
            self.client_obj = await client_manager.create(system_servers = self.server_obj.system_servers, 
                                                          remote_servers = self.server_obj.remote_servers, 
                                                          system_node_ids= self.system_node_ids)
            
            await self.run_test()
            await self.server_obj.close()
            await self.client_obj.close()
