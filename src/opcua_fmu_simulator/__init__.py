from .operations import ops
# from .system_tester import TestSystem
from .test_runner import TestSystem
import asyncio
import sys
import os

from opcua_fmu_simulator.utils import EXPERIMENTS_DIR
from opcua_fmu_simulator.db.connection import SQLDB
#EXPERIMENTS_DIR = "experiments/"

def main():
    """Main entry point for running experiments."""
    args = sys.argv[1:]
    if not args:
        print("Running all experiments")
        experiment_configs = [
            os.path.join(EXPERIMENTS_DIR, f)
            for f in os.listdir(EXPERIMENTS_DIR)
            if os.path.isfile(os.path.join(EXPERIMENTS_DIR, f))
        ]
    else:
        print("Running specific experiments")
        experiment_configs = [f"{EXPERIMENTS_DIR}/{file_name}" for file_name in args]

    # initialize database
    db = SQLDB(table="logs")
    db.ensure_schema()

    async def run_experiments():
        experiments = TestSystem(
            experiment_configs=experiment_configs,
            db=db
        )
        await experiments.main_testing_loop()
    
    try:
        asyncio.run(run_experiments())
    finally:
        db.commit() # Commit any remaining transactions to the database
        db.close() # Close the database connection to release resources


