import asyncio
import sys
from headers import TestSystem

async def main(funciton):
    conf = "TESTS/system_config.yaml"
    remote_servers = "TESTS/remote_servers/"
    tests = TestSystem(config_file= conf, remote_servers= remote_servers)
    if   funciton == "test":     await tests.main_testing_loop()
    elif funciton == "describe": await tests.describe_system()

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == '-func':
        asyncio.run(main(funciton=args[1]))
    else:
        print("args reuqired '-func' and it can be rither 'test' or 'describe' ")
        