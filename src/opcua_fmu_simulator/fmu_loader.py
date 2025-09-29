import fmpy
import logging

_logger = logging.getLogger(__name__)

class FmuLoader:
    def __init__(self, fmu_file) -> None:
        
        self.model_description = fmpy.read_model_description(fmu_file)  
        self.fmu_name = self.model_description.modelName
        self.unzipdir = fmpy.extract(fmu_file)
        self.fmu = fmpy.fmi2.FMU2Slave(guid=self.model_description.guid,
                        unzipDirectory=self.unzipdir,
                        modelIdentifier=self.model_description.coSimulation.modelIdentifier,
                        instanceName='instance1')

        self.fmu.instantiate()
        self.fmu.enterInitializationMode()      
        self.fmu.exitInitializationMode()
        self.fmu_inputs = {}
        self.fmu_outputs = {}
        self.fmu_parameters = {} 
        self.locate_variable_names()

    def _add_input(self, variable:fmpy.model_description.ScalarVariable) -> None:
        self.fmu_inputs[variable.name] = {
            "id" : variable.valueReference,
            "type" : variable.type
        }
        return

    def _add_output(self, variable:fmpy.model_description.ScalarVariable) -> None:
        self.fmu_outputs[variable.name] = {
            "id" : variable.valueReference,
            "type" : variable.type
        }
    
    def _add_parameter(self, variable:fmpy.model_description.ScalarVariable) -> None:
        self.fmu_parameters[variable.name] = {
                "id" : variable.valueReference,
                "type" : variable.type
            }
            
    def locate_variable_names(self) -> None:
        """
        adds fmu I/Os to object
        """
        # Setting up
        _logger.info("Run simulation \n")            

        # Gathering the I/Os references TODO: Outside of simulation loop - beforehand?
        for variable in self.model_description.modelVariables:
            if variable.causality == "input":    
                self._add_input(variable=variable)
            elif variable.causality == "output": 
                self._add_output(variable=variable)
            elif variable.causality == "parameter":
                self._add_parameter(variable=variable)
                
        _logger.info(f"inp = {self.fmu_inputs}, \nout = {self.fmu_outputs}, \npar = {self.fmu_parameters}")

    def get_fmu_inputs(self) -> list[str]:
        return list(self.fmu_inputs.keys())
    
    def get_fmu_outputs(self)  -> list[str]:
        return list(self.fmu_outputs.keys())
    
    def get_fmu_parameters(self)  -> list[str]:
        return list(self.fmu_parameters.keys())

