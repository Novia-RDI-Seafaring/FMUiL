from opcua_fmu_simulator.config_loader import DataLoaderClass

data_handler = DataLoaderClass("experiments/exp3_external_server.yaml")

print("--------------DATA--------------")
print(data_handler.dump_json())
data_handler.save_yaml("exp3")
