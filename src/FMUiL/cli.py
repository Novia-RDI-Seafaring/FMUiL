import typer
import asyncio
import os
from FMUiL.simulator.experiment_controller import ExperimentSystem

app = typer.Typer(help="Run FMUiL experiments and simulations")


async def run_experiments(experiment_configs: list[str], port: int = 7500):
    experiments = ExperimentSystem(experiment_configs=experiment_configs, base_port=port)
    await experiments.main_experiment_loop()

# TODO: muokkaa --experiment-dir option komento selkeemmäksi
# --experiment-dir toimii, mutta hakee rootista fmu pathia, joten sitä pitää jotenkin muokata
@app.command()
def run_all(
    experiments_dir: str = typer.Option("experiments/", help="Directory containing experiment YAML files"),
    port: int = typer.Option(7500, help="Base port for OPC UA servers"),
    ):
    """Run all experiments in the experiments folder."""
    experiment_configs = [
        os.path.join(experiments_dir, f)
        for f in os.listdir(experiments_dir)
        if os.path.isfile(os.path.join(experiments_dir, f))
    ]
    asyncio.run(run_experiments(experiment_configs, port))

# TODO: Täytyy vielä muokata niin että voi antaa pelkästään pathin: "experiments/exp.yaml" ei molempia
@app.command()
def run(
    experiment_name: str,
    experiments_dir: str = typer.Option("experiments/", help="Directory containing experiment YAML files"),
    port: int = typer.Option(7500, help="Base port for OPC UA servers"),
):
    """Run a specific experiment by name (e.g. 'FMUiL run tank.yaml')."""
    experiment_config = os.path.join(experiments_dir, experiment_name)
    asyncio.run(run_experiments([experiment_config], port))


