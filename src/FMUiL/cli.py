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
# Command: plot
# -----------------------------
@app.command(help="Create plots from CSV data files")
def plot(
    data_files: list[str] = typer.Argument(..., help="Paths to CSV data files to plot"),
    labels: list[str] = typer.Option([], "--label", "-l", help="Custom labels for each data file (optional)"),
    output: str = typer.Option("plot.pdf", "--output", "-o", help="Output filename for the plot"),
    title: str = typer.Option("Data Analysis", "--title", "-t", help="Title for the plot"),
    show_legend: bool = typer.Option(True, "--legend/--no-legend", help="Show/hide legend"),
):
    """Create plots from CSV data files with custom labels and styling."""
    
    if len(labels) > 0 and len(labels) != len(data_files):
        typer.echo("Error: Number of labels must match number of data files", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Creating plot from {len(data_files)} data files...")
    
    plotter = Plotter()
    
    # Add data files with optional labels
    for i, data_file in enumerate(data_files):
        if i < len(labels):
            label = labels[i]
        else:
            label = None
        
        try:
            plotter.add_data(path=data_file, label=label)
            typer.echo(f"Added data file: {data_file}")
        except Exception as e:
            typer.echo(f"Error loading {data_file}: {e}", err=True)
            raise typer.Exit(1)
    
    # Create and save plots
    try:
        plotter.create_plots(title=title, show_legend=show_legend)
        plotter.save_plots(output)
        plotter.close_plots()
        typer.echo(f"Plot saved to: {output}")
    except Exception as e:
        typer.echo(f"Error creating plot: {e}", err=True)
        raise typer.Exit(1)


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    app()
