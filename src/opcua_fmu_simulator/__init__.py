# src/opcua_fmu_simulator/__init__.py
from .operations import ops
# from .system_tester import TestSystem
from .test_runner import TestSystem
import asyncio
import sys
import os

from opcua_fmu_simulator.db.connection import SQLDB
from opcua_fmu_simulator.config import load_config


def main():
    """Main entry point for running experiments."""
    cfg = load_config()
    exp_dir = cfg.experiments.dir  # Path object
    os.makedirs(exp_dir, exist_ok=True)

    args = sys.argv[1:]
    if not args:
        print("Running all experiments")
        experiment_configs = [
            exp_dir / f
            for f in os.listdir(exp_dir)
            if os.path.isfile(exp_dir / f)
        ]
    else:
        print("Running specific experiments")
        experiment_configs = [exp_dir / file_name for file_name in args]

    # initialize database
    db = SQLDB(table="logs")
    db.ensure_schema()

    async def run_experiments():
        experiments = TestSystem(
            experiment_configs=experiment_configs,
            db=db,
        )
        await experiments.main_testing_loop()

    try:
        asyncio.run(run_experiments())
    finally:
        db.commit()  # Commit any remaining transactions
        db.close()   # Release resources
