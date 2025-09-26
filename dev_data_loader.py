from opcua_fmu_simulator.config_loader import ExperimentLoader, ExternalServerLoader

data_handler = ExperimentLoader("experiments/exp3_external_server.yaml")

print("--------------DATA--------------")
print(data_handler.dump_json())
#data_handler.save_yaml("exp3")


# external servers
server_handler = ExternalServerLoader("servers/example_server.yaml")
print(server_handler.dump_json())
#server_handler.save_yaml("example_server")