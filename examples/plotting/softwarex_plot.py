from FMUiL.logger.plotting import Plotter, DataModel, AxisModel, Styles
import os

# Root path configuration
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Panel config
PANEL_CONFIG = {
    "panel": {
        "dimensions": {
            "width_cm": 13.76,
            "height_cm": 5.0,
        },
        "margins": {
            "top_cm": 0.5,
            "bottom_cm": 1.0,
            "left_cm": 1.2,
            "right_cm": 0.3,
        },
        "axes_separation": {
            "x_cm": 1.7,
            "y_cm": 0.0,
        },
    },
    "style": {
        "rc_params": {
            "font.size": 8,
            "text.usetex": False,
            "font.family": "serif",
            "mathtext.fontset": "stix",
            "mathtext.default": "regular",
            "legend.fontsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
        }
    },
    "output": {
        "format": "pdf",
        "dpi": 600,
    }
}

# Define axis configurations
mil_ax = AxisModel(
    xlabel="Time (s)", 
    ylabel="Control Signal (V)", 
    xlim=(0, 60), 
    ylim=(-2.1, 16.1), 
    xtick_distance=10, 
    ytick_distance=4
)
hil_ax = AxisModel(
    xlabel="Time (s)", 
    ylabel="Water Level (m)", 
    xlim=(0, 60), 
    ylim=(0, 16.1), 
    xtick_distance=10, 
    ytick_distance=4
)

# Data to be plotted
mil_data = DataModel(label="MiL", path=os.path.join(ROOT_PATH, "examples", "plotting", "SoftwareX", "MiL"), evaluate=True, ax=mil_ax)
hil_data = DataModel(label="HiL", path=os.path.join(ROOT_PATH, "examples", "plotting", "SoftwareX", "Hil"), evaluate=True, ax=hil_ax)

data = [mil_data, hil_data]

# Configure styles
STYLES = Styles(panels_config=PANEL_CONFIG)

def main():
    """Example of plotting data from log files."""
    
    # Create plotter with styles
    plt = Plotter(styles=STYLES)
    
    # Add data models with data and axis configuration
    for d in data:
        print(f"Adding data: {d.label} from {d.path}")
        plt.add_data(d)

    print(f"Total data models: {len(plt.data)}")
    
    # Create the panels from data (axis configs applied automatically)
    plt.create_plots()

    # Save panels to file
    plt.save_plots("examples/plotting/softwarex_results.pdf")

    # Close panels
    plt.close_plots()

if __name__ == "__main__":
    main()
