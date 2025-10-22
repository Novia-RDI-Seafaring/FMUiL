import typer
import asyncio
import os
from pathlib import Path
from .handlers.simulation_handler import SimulationHandler
from .logger.plotting import Plotter

app = typer.Typer(help="Run FMUiL experiments and simulations.")

# -----------------------------
# Callback: global options
# -----------------------------
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    experiments_dir: str = typer.Option(
        "experiments/",
        "--experiments-dir",
        "-d",
        help="Path to the folder containing experiment YAML files."
    ),
    # currently not useful
    show_folder: bool = typer.Option(
        False,
        "--show-folder",
        help="Print the current experiments folder."
    ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show FMUiL version."
    ),
):
    """FMUiL CLI — manage and run in-the-loop simulations with FMUs."""



    # Store global options in context
    ctx.obj = {
        "experiments_dir": Path(experiments_dir),
    }

    # Print version if requested
    if version:
        typer.echo("FMUiL version 0.1.0")

    # Print folder if requested
    if show_folder:
        typer.echo(f"Current experiments folder: {experiments_dir}")

    # Show help if no command and no special flags
    if ctx.invoked_subcommand is None and not (version or show_folder):
        typer.echo(ctx.get_help())


# -----------------------------
# Utility function: run experiments
# -----------------------------
async def run_experiments(experiment_configs: list[str], port: int = 7500):
    experiments = SimulationHandler(experiment_configs=experiment_configs, base_port=port)
    await experiments.main_experiment_loop()


# -----------------------------
# Command: folder
# -----------------------------
@app.command(help="Print the current experiments folder")
def folder(ctx: typer.Context):
    experiments_dir: Path = ctx.obj["experiments_dir"]
    typer.echo(f"Current experiments folder: {experiments_dir}")


# -----------------------------
# Command: run-all
# -----------------------------
@app.command(help="Run all experiments in the folder")
def run_all(ctx: typer.Context, port: int = typer.Option(7500, "--port", "-p", help="Base port for OPC UA servers.")):
    experiments_dir: Path = ctx.obj["experiments_dir"]

    experiment_configs = [
        os.path.join(experiments_dir, f)
        for f in os.listdir(experiments_dir)
        if os.path.isfile(os.path.join(experiments_dir, f))
    ]

    asyncio.run(run_experiments(experiment_configs, port))


# -----------------------------
# Command: run
# -----------------------------
@app.command(help="Run a specific experiment by name (e.g. 'FMUiL run tank.yaml')")
def run(ctx: typer.Context, experiment_name: str, port: int = typer.Option(7500, "--port", "-p", help="Base port for OPC UA servers.")):
    experiments_dir: Path = ctx.obj["experiments_dir"]
    experiment_config = os.path.join(experiments_dir, experiment_name)

    asyncio.run(run_experiments([experiment_config], port))


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    app()
