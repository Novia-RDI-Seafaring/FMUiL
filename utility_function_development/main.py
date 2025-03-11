import asyncio
from headers.server_setup_dev import OPCUAFMUServerSetup
from headers.config_loader import DataLoaderClass



async def run_multiple_servers():
    base_port = 7000
    config = DataLoaderClass("system_config.yaml")
    tasklist = []
    for i in config.data["fmu"]:
        print(i)
        base_port+=1
        server1 = OPCUAFMUServerSetup(fmu="../FMUs/LOC_CNTRL_custom_linux.fmu", port=base_port)
        task1 = asyncio.create_task(server1.main_loop())
        tasklist.append(task1)
    
    for i in tasklist:
        await i
    # # Create OPCUA server objects
    # server1 = OPCUAFMUServerSetup(fmu="../FMUs/LOC_CNTRL_custom_linux.fmu", port=7003)
    # server2 = OPCUAFMUServerSetup(fmu="../FMUs/LOC_SYSTEM_linux.fmu", port=7004)
    # # Create tasks but don't await them yet
    # task1 = asyncio.create_task(server1.main_loop())
    # task2 = asyncio.create_task(server2.main_loop())
    # print("Servers are now running in the background...")
    # # await asyncio.sleep(10)  # placeholder for "doing other stuff"
    # await task1
    # await task2

async def main():
    await run_multiple_servers()

# if __name__ == "__main__":
asyncio.run(main())
