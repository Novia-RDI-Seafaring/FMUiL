from opcua_fmu_simulator.config_loader import DataLoaderClass

data_handler = DataLoaderClass("experiments/exp1_water_tank.yaml")

print("--------------DATA--------------")
print(data_handler.dump_json())
data_handler.save_json("exp1")
data_handler.save_yaml("exp1")
print("--------------DATA--------------")
