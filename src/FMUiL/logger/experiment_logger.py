import os

# This will be changed
DEFAULT_LOGS = {"Evaluation":"experiment_name, evaluation_name, evaluation_function, measured_value, experiment_result, system_timestamp\n",
                "Values":"Experiment_name, System, Variable, Value, Time\n"}

class ExperimentLogger:
    def __init__(self, system: "SimulationHandler") -> None:
        self.system = system     
        self.log_file = self.generate_logfiles(system.log_folder) 
    
    @property
    def experiment_name(self):
        return self.system.experiment["experiment_name"]

    @property
    def evaluation_equations(self):
        return self.system.evaluation_equation_dic

    @property
    def node_ids(self):
        return self.system.system_node_ids
    
    @property
    def logging(self):
        return self.system.experiment["logging"]
    
    @property
    def config(self):
        return self.system.config
    
    @property
    def logged_values(self):
        logged_values = [(num, part) for num, part in (item.split(".") for item in self.logging)]
        return logged_values

    def generate_logfiles(self, folder_path, logs_with_headers=DEFAULT_LOGS):
        # Subfolder for the experiment
        experiment_folder = os.path.join(folder_path, self.experiment_name)
        os.makedirs(experiment_folder, exist_ok=True)

        file_paths = []
        for log_name, header in logs_with_headers.items():
            file_path = os.path.join(experiment_folder, f"{log_name}.csv")
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write(header)
            file_paths.append(file_path)
        return file_paths
    
    def log_result(self, criterea, measured_value, evaluation_result, simulation_time):
        system_output = f"{self.config['experiment']['experiment_name']},\
            {criterea},\
            {self.evaluation_equations[criterea]['target_obj']}.{self.evaluation_equations[criterea]['target_var']} {self.evaluation_equations[criterea]['operator']} {self.evaluation_equations[criterea]['value']},\
            {measured_value},\
            {evaluation_result},\
            {simulation_time}\n"
        self.write_to_log(output= system_output, filepath= self.log_file[0])

    async def log_value(self, fmu, variable, value, sim_time):
        system_output = f"{self.config['experiment']['experiment_name']},\
            {fmu},\
            {variable},\
            {value},\
            {sim_time}\n"
        self.write_to_log(output= system_output, filepath= self.log_file[1])
    
    def write_to_log(self, output, filepath, mode = "a"):
        with open(filepath, mode) as file:            
            file.write(output)