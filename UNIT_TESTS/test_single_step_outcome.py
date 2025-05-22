import asyncio
from asyncua import Client, ua
import asyncua
import sys
from colorama import Fore, Back, Style

sys.path.append("..")

from headers import TestSystem
from headers.server_setup_dev import OPCUAFMUServerSetup
from headers.config_loader import DataLoaderClass

async def main(function):
    conf = "./test_files/single_step_test.yaml"
    tests = TestSystem(config_file=conf)
    if   function == "test":     
        value =  await tests.main_testing_loop()
        print(f"THIS IS AFTER THE VALUE {value}")
        exit()
    elif function == "describe": 
        await tests.describe_system()

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == '-func':
        asyncio.run(main(function=args[1]))
    else:
        print("args reuqired '-func' and it can be rither 'test' or 'describe' ")
   