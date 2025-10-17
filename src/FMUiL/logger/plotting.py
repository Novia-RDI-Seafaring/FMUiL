import matplotlib.pyplot as plt
import mpl_panel_builder as mpb
import pandas as pd

DEFAULT_CONFIG = {
    "panel": {
        "dimensions": {
            "width_cm": 15.0,
            "height_cm": 6.0,
        },
        "margins": {
            "top_cm": 0.5,
            "bottom_cm": 1.0,
            "left_cm": 1.5,
            "right_cm": 0.5,
        },
        "axes_separation": {
            "x_cm": 1.5,
            "y_cm": 1.5,
        },
    },
    "style": {
        "rc_params": {
            "font.size": 8,
            "text.usetex": False,
            "font.family": "serif",
            "mathtext.fontset": "stix",
            "mathtext.default": "regular",
            "legend.fontsize": 6,

        }
    },
    "output": {
        "format": "pdf",
        "dpi": 600,
    }
}

PLOT_COLORS = ["1971c2", "f08c00", "2f9e44", "e03131" ]

class Plotter:
    def __init__(self, config: dict = DEFAULT_CONFIG):
        self.config = config
        self.experiments = []
        self.figures = []  # Store created figures

    def add_data(self, path: str, label: str = None):
        """Add a data file to the plotter with optional custom label. Returns self for method chaining."""
        data = self.load_data(path)
        
        # Use custom label if provided, otherwise create from path and data
        if label:
            experiment_name = label
        else:
            # Create unique experiment name based on file path and data
            exp_names = data["Experiment_name"].unique()
            if len(exp_names) == 1:
                base_name = exp_names[0]
            else:
                base_name = f"experiment_{len(self.experiments) + 1}"
            
            # Extract timestamp from path for uniqueness
            import os
            path_parts = path.split(os.sep)
            timestamp = None
            for part in path_parts:
                if part.startswith("2025_") and "_" in part:
                    timestamp = part
                    break
            
            if timestamp:
                experiment_name = f"{base_name}_{timestamp}"
            else:
                experiment_name = f"{base_name}_{len(self.experiments) + 1}"
        
        self.experiments.append({
            'name': experiment_name,
            'data': data,
            'path': path
        })
        return self

    def list_experiments(self):
        """List all available experiment names."""
        if not self.experiments:
            print("No experiments added.")
            return []
        
        experiment_names = [exp['name'] for exp in self.experiments]
        print(f"Available experiments: {experiment_names}")
        return experiment_names

    def load_data(self, path: str):
        """Load CSV data with multiple encoding attempts."""
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df = None
        for encoding in encodings:
            try:
                df = pd.read_csv(path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError(f"Could not read file with any of the attempted encodings: {encodings}")
            
        df.columns = [c.strip() for c in df.columns]
        # Strip whitespace from string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()
        return df

    def create_plots(self, title: str = "All Experiments - Variable Analysis", 
                    show_legend: bool = True, legend_position: str = "best"):
        """Create plots and store them in self.figures.
        
        Args:
            title: Title for the overall plot
            show_legend: Whether to show legends on all panels
            legend_position: Position of the legend ('best', 'upper right', 'lower left', etc.)
        """
        if not self.experiments:
            print("No experiments added. Call add_data() first.")
            return self
        
        # Clear existing figures
        self.figures = []
        
        # Get all unique variables across all experiments
        all_variables = set()
        for exp in self.experiments:
            variables = exp['data']['Variable'].unique()
            all_variables.update(variables)
        
        all_variables = sorted(list(all_variables))
        n_variables = len(all_variables)
        
        if n_variables == 0:
            print("No variables found in the data.")
            return self
        
        # Calculate grid dimensions
        cols = min(3, n_variables)
        rows = (n_variables + cols - 1) // cols
        
        # Configure and create figure
        mpb.configure(self.config)
        mpb.set_rc_style()
        fig, axs = mpb.create_panel(rows=rows, cols=cols)
        
        # Flatten axs for easier indexing
        if rows == 1:
            axs_flat = axs[0] if cols > 1 else [axs[0][0]]
        else:
            axs_flat = [axs[i][j] for i in range(rows) for j in range(cols)]
        
        # Plot each variable in its own panel
        for var_idx, variable in enumerate(all_variables):
            if var_idx >= len(axs_flat):
                break
                
            ax = axs_flat[var_idx]
            
            # Get the system name for this variable (from first experiment that has it)
            system_name = None
            for exp in self.experiments:
                exp_data = exp['data']
                if variable in exp_data['Variable'].values:
                    systems_with_var = exp_data[exp_data['Variable'] == variable]['System'].unique()
                    if len(systems_with_var) > 0:
                        system_name = systems_with_var[0]  # Use first system found
                        break
            
            # Plot this variable from all experiments
            for exp_idx, exp in enumerate(self.experiments):
                exp_name = exp['name']
                exp_data = exp['data']
                
                # Get color for this experiment (cycle through PLOT_COLORS)
                color = f"#{PLOT_COLORS[exp_idx % len(PLOT_COLORS)]}"
                
                # Check if this experiment has this variable
                if variable in exp_data['Variable'].values:
                    # Get all systems that have this variable
                    systems_with_var = exp_data[exp_data['Variable'] == variable]['System'].unique()
                    
                    for system in systems_with_var:
                        # Get data for this system-variable combination
                        plot_data = exp_data[
                            (exp_data["System"] == system) & (exp_data["Variable"] == variable)
                        ].sort_values("Time")
                        
                        if not plot_data.empty:
                            ax.plot(plot_data["Time"], plot_data["Value"], 
                                   linewidth=1.5, label=exp_name, color=color)
            
            # Set labels (font sizes from config)
            ax.set_xlabel("Time")
            ax.set_ylabel(variable)
            ax.grid(True, alpha=0.3)
            
            # Set panel title to System name
            if system_name:
                ax.set_title(system_name)
            
            # Add legend inside panel (best position)
            if show_legend:
                ax.legend(loc='best')
            else:
                ax.legend().set_visible(False)
        
        # Hide unused subplots
        for idx in range(n_variables, len(axs_flat)):
            axs_flat[idx].set_visible(False)

        # Store the figure
        self.figures.append(fig)
        print(f"Created plot with {n_variables} variables")
        
        return self

    def get_consistent_legend_elements(self):
        """Get consistent legend elements across all experiments and systems."""
        legend_elements = set()
        for exp in self.experiments:
            exp_name = exp['name']
            exp_data = exp['data']
            systems = exp_data['System'].unique()
            for system in systems:
                legend_elements.add(f"{exp_name}: {system}")
        return sorted(list(legend_elements))

    def save_plots(self, filename: str = "all_experiments_plot.pdf"):
        """Save all stored figures to disk.
        
        Args:
            filename: Output filename (if multiple figures, will add index)
        """
        if not self.figures:
            print("No figures to save. Call create_plots() first.")
            return self
        
        for i, fig in enumerate(self.figures):
            if len(self.figures) == 1:
                output_filename = filename
            else:
                name, ext = filename.rsplit('.', 1)
                output_filename = f"{name}_{i+1}.{ext}"
            
            mpb.save_panel(fig, output_filename)
            print(f"Saved plot to: {output_filename}")
        
        return self

    def close_plots(self):
        """Close all stored figures to free memory."""
        for fig in self.figures:
            plt.close(fig)
        self.figures = []
        print("Closed all figures")
        return self


def main():
    # example of plotting data from log files   
    
    plt = Plotter()
    # add data from log files
    plt.add_data(path="logs/2025_10_17_19_33_35/Water Level Control/Values.csv", label="PI-controller - $K_p =  1.6$")
    plt.add_data(path="logs/2025_10_17_19_34_45/Water Level Control/Values.csv", label="PI-controller - $K_p =  2.6$")
    plt.add_data(path="logs/2025_10_17_19_35_52/Water Level Control/Values.csv", label=f"PI-controller - $K_p = 0.6$")

    #create the panels from data
    plt.create_plots(title="Water Level Control Analysis")

    #save panels to file
    plt.save_plots("water_level_analysis.pdf")

    #close panels
    plt.close_plots()

if __name__ == "__main__":
    main()