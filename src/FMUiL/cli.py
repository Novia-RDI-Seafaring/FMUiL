import typer
import asyncio
import os
from FMUiL.simulator.experiment_controller import ExperimentSystem

app = typer.Typer(help="Run FMUiL experiments and simulations")

EXPERIMENTS_DIR = "experiments/"

async def run_experiments(experiment_configs: list[str]):
    experiments = ExperimentSystem(experiment_configs=experiment_configs)
    await experiments.main_experiment_loop()


@app.command()
def run_all():
    """Run all experiments in the experiments folder."""
    experiment_configs = [
        os.path.join(EXPERIMENTS_DIR, f)
        for f in os.listdir(EXPERIMENTS_DIR)
        if os.path.isfile(os.path.join(EXPERIMENTS_DIR, f))
    ]
    asyncio.run(run_experiments(experiment_configs))


@app.command()
def run(experiment_name: str):
    """Run a specific experiment by name (e.g. 'FMUiL run tank.yaml')."""
    experiment_config = os.path.join(EXPERIMENTS_DIR, experiment_name)
    asyncio.run(run_experiments([experiment_config]))
