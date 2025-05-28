import asyncio
from OPCUA_FMU_simulator import TestSystem

test_directory = "TESTS/"

async def main():
    tests = TestSystem(config_folder=test_directory)
    await tests.main_testing_loop()

if __name__ == "__main__":
    asyncio.run(main())
