import asyncio
import sys
# from headers import TestSystem
from OPCUA_FMU_Simulator import TestSystem

async def main(function):
    conf = "TESTS/"
    remote_servers = "test_servers/" # SERVERRS ARE INDIVIDUAL FILES!!!
    tests = TestSystem(config_folder= conf, remote_server_directory=remote_servers )#, remote_servers= remote_servers)
    if   function == "test":     await tests.main_testing_loop()

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == '-func':
        asyncio.run(main(function=args[1]))
    else:
        raise Exception("args required '-func' and it can be rither 'test' or 'describe' ")
