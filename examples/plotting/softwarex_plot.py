from FMUiL.logger.plotting import Plotter, DataModel, AxisModel, Styles, DEFAULT_CONFIG

# Define data models with axis configurations
DATA = [
    DataModel(
        label="MiL",
        path="examples/plotting/SoftwareX/MiL", 
        evaluate=True,
        ax=AxisModel(
            xlabel="Time (s)", 
            ylabel="Control Signal (V)", 
            xlim=(0, 60), 
            ylim=(-2, 16), 
            xtick_distance=10, 
            ytick_distance=4
        )
    ),
    DataModel(
        label="HiL",
        path="examples/plotting/SoftwareX/Hil", 
        evaluate=True,
        ax=AxisModel(
            xlabel="Time (s)", 
            ylabel="Water Level (m)", 
            xlim=(0, 60), 
            ylim=(0, 16), 
            xtick_distance=10, 
            ytick_distance=4
        )
    )
]

# Configure styles
STYLES = Styles(panels_config=DEFAULT_CONFIG)

def main():
    """Example of plotting data from log files."""
    
    # Create plotter with styles
    plt = Plotter(styles=STYLES)
    
    # Add data models with data and axis configuration
    for data_model in DATA:
        plt.add_data(data_model)

    # Create the panels from data (axis configs applied automatically)
    plt.create_plots(title="Water Level Control Analysis")

    # Save panels to file
    plt.save_plots("examples/plotting/softwarex.pdf")

    # Close panels
    plt.close_plots()

if __name__ == "__main__":
    main()
