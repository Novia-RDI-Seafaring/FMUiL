import matplotlib.pyplot as plt
import mpl_panel_builder as mpb
from numpy._core.numeric import True_
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, Optional
import pandas as pd
import os

DEFAULT_CONFIG = {
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

class AlarmColors(BaseModel):
    warning: str = Field(default="#FBBD23")
    alarm: str = Field(default="#F97316")
    success: str = Field(default="#36D399")
    error: str = Field(default="#F87272")

class LineStyles(BaseModel):
    line_styles: List[Literal["-", "--", "-.", ":"]] = Field(
        default_factory=lambda: ["-", "--", "-.", ":"]
    )
    primary_color: str = Field(default="#000000")
    width: float = Field(default=1.0)
    alpha: float = Field(default=1.0)

class ShadeStyles(BaseModel):
    color: str = Field(default="#F87272")
    alpha: float = Field(default=0.40)

class Styles(BaseModel):
    line_styles: LineStyles = Field(default_factory=LineStyles)
    shade_styles: ShadeStyles = Field(default_factory=ShadeStyles)
    alarms: AlarmColors = Field(default_factory=AlarmColors)
    panels_config: dict = Field(default_factory=dict)

#### Panel axis model ####
class AxisModel(BaseModel):
    xlabel: str
    ylabel: str
    xlim: tuple
    ylim: tuple
    xtick_distance: float
    ytick_distance: float

#### Data model ####
class DataModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    label: str
    path: str
    validation_data: pd.DataFrame = Field(default_factory=pd.DataFrame)
    evaluation_data: pd.DataFrame = Field(default_factory=pd.DataFrame)
    evaluate: bool = Field(default=True)
    ax: Optional[AxisModel] = Field(default=None)

class Panels(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    axes: List[plt.Axes]
    variables: List[str]

########################################################
class Plotter:
    def __init__(self, styles: Styles = None, path: str = None):
        self.styles = styles
        self.path = path
        self.data = []
        self.panels: Optional[Panels] = None
        self.current_figure: Optional[plt.Figure] = None
        self.error_figure: Optional[plt.Figure] = None

    def add_data(self, data_model: DataModel):
        """Add a DataModel with data and axis configuration."""
        # Process the data from the data_model's path
        dir_path = data_model.path
        evaluate = data_model.evaluate
        
        if not os.path.isdir(dir_path):
            raise ValueError(f"Expected directory with Values.csv: {dir_path}")

        files = {f.lower(): os.path.join(dir_path, f) for f in os.listdir(dir_path)}
        values_path = files.get("values.csv")
        eval_path = files.get("evaluation.csv")

        # Load data
        validation_data = self._load_data(values_path) if values_path else pd.DataFrame()
        evaluation_data = pd.DataFrame()  # Default to empty
        
        # Only process evaluation data if evaluate=True
        if evaluate and eval_path:
            evaluation_data = self._load_data(eval_path)
            if not evaluation_data.empty:
                evaluation_data = self._process_evaluation_data(evaluation_data)

        # Update data_model with loaded data
        data_model.validation_data = validation_data
        data_model.evaluation_data = evaluation_data
        data_model.path = values_path or ""
        
        self.data.append(data_model)
        return self


    def _create_panels(self):
        """Create panels based on data models and variables."""
        # Get all unique variables
        all_variables = self._get_all_variables()
        if not all_variables:
            print("No variables found in the data.")
            return
        
        # Calculate grid dimensions
        cols = min(3, len(all_variables))
        rows = (len(all_variables) + cols - 1) // cols
        
        # Create figure and panels
        mpb.configure(self.styles.panels_config)
        mpb.set_rc_style()
        figure, axs = mpb.create_panel(rows=rows, cols=cols)
        
        # Flatten axes
        if rows == 1:
            axes_flat = axs[0] if cols > 1 else [axs[0][0]]
        else:
            axes_flat = [axs[i][j] for i in range(rows) for j in range(cols)]
        
        # Hide unused subplots
        for idx in range(len(all_variables), len(axes_flat)):
            axes_flat[idx].set_visible(False)
        
        # Store panels and figure reference
        self.panels = Panels(axes=axes_flat, variables=all_variables)
        self.current_figure = figure

    def _plot_panel(self, ax, variable, show_legend):
        """Plot all experiments for a single variable panel."""
        for exp_idx, exp in enumerate(self.data):
            if exp.validation_data.empty:
                continue
                
            exp_name = exp.label
            exp_data = exp.validation_data
            exp_eval = exp.evaluation_data
            
            # Get styling
            primary_color = self.styles.line_styles.primary_color
            line_style = self.styles.line_styles.line_styles[exp_idx % len(self.styles.line_styles.line_styles)] if self.styles.line_styles.line_styles else '-'
            line_width = self.styles.line_styles.width
            line_alpha = self.styles.line_styles.alpha
            
            if variable in exp_data['Variable'].values:
                systems_with_var = exp_data[exp_data['Variable'] == variable]['System'].unique()
                legend_added = False
                
                for system in systems_with_var:
                    plot_data = exp_data[
                        (exp_data["System"] == system) & (exp_data["Variable"] == variable)
                    ].sort_values("Time")
                    
                    
                    if not plot_data.empty:
                        # Plot value
                        legend_added = self._plot_value(ax, plot_data, exp_name, primary_color, line_style, line_width, line_alpha, legend_added)
                        # Plot evaluation only if evaluate=True
                        if exp.evaluate:
                            self._plot_evaluation(ax, plot_data, exp_eval, system, variable, primary_color, line_style, line_width, line_alpha)
        
        # Configure panel
        ax.autoscale(enable=True, tight=True)
        ax.set_xlabel("Time")
        ax.set_ylabel(variable)
        ax.grid(False)
        
        if show_legend:
            ax.legend(loc='upper right', framealpha=0.5)
        else:
            ax.legend().set_visible(False)

    def _load_data(self, path: str):
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
    
    def _process_evaluation_data(self, eval_df):
        """Process evaluation data to extract System and Variable columns."""
        # Normalize types
        if 'experiment_result' in eval_df.columns:
            eval_df['experiment_result'] = eval_df['experiment_result'].astype(str).str.strip().str.lower().map({'true': True, 'false': False})
        if 'system_timestamp' in eval_df.columns:
            eval_df['system_timestamp'] = pd.to_numeric(eval_df['system_timestamp'], errors='coerce')
        if 'measured_value' in eval_df.columns:
            eval_df['measured_value'] = pd.to_numeric(eval_df['measured_value'], errors='coerce')

        # Parse System and Variable from evaluation_function like "System.Variable op threshold"
        sys_vals = []
        if 'evaluation_function' in eval_df.columns:
            for expr in eval_df['evaluation_function'].astype(str).fillna(''):
                lhs = expr.split('>')[0].split('<')[0].split('>=')[0].split('<=')[0].split('==')[0].split('!=')[0].strip()
                # lhs expected "System.Variable"
                if '.' in lhs:
                    system_name, variable_name = lhs.split('.', 1)
                else:
                    system_name, variable_name = None, None
                sys_vals.append((system_name, variable_name))
        if sys_vals:
            eval_df['System'] = [sv[0] for sv in sys_vals]
            eval_df['Variable'] = [sv[1] for sv in sys_vals]

        return eval_df
    
    def _plot_value(self, ax, plot_data, exp_name, primary_color, line_style, line_width, line_alpha, legend_added):
        """Plot the main value line."""
        base_label = exp_name if not legend_added else "_nolegend_"
        ax.plot(
            plot_data['Time'], plot_data['Value'],
            linewidth=line_width,
            label=base_label,
            color=primary_color,
            linestyle=line_style,
            dash_capstyle='butt',
            dash_joinstyle='miter',
            zorder=0.6,
            alpha=line_alpha,
        )
        return True

    def _plot_evaluation(self, ax, plot_data, exp_eval, system, variable, primary_color, line_style, line_width, line_alpha):
        """Plot evaluation overlays (shading and red segments)."""
        if exp_eval.empty or not {'System', 'Variable', 'system_timestamp', 'experiment_result'}.issubset(exp_eval.columns):
            return False

        eval_mask_all = (
            (exp_eval['System'] == system) &
            (exp_eval['Variable'] == variable)
        )
        eval_seq = exp_eval.loc[eval_mask_all, ['system_timestamp', 'experiment_result']]\
            .dropna()\
            .sort_values('system_timestamp')

        start_time = float(plot_data['Time'].min())
        end_time = float(plot_data['Time'].max())

        intervals_all = []  # (start, end, state_bool)
        current_state = False  # default to non-violation
        current_start = start_time

        for ts, res in zip(eval_seq['system_timestamp'], eval_seq['experiment_result']):
            ts_f = float(ts)
            if ts_f <= start_time:
                current_state = bool(res)
                current_start = start_time
                continue
            if ts_f >= end_time:
                intervals_all.append((current_start, end_time, current_state))
                current_start = end_time
                current_state = bool(res)
                break
            intervals_all.append((current_start, ts_f, current_state))
            current_start = ts_f
            current_state = bool(res)

        if current_start < end_time:
            intervals_all.append((current_start, end_time, current_state))

        # Full-panel shading for True intervals
        shade_color = self.styles.shade_styles.color
        shade_alpha = self.styles.shade_styles.alpha
        for s, e, st in intervals_all:
            if e <= s or (st is not True):
                continue
            ax.axvspan(s, e, color=shade_color, alpha=shade_alpha, linewidth=0, zorder=0.2)

        # Overlay red segments (True) using the same linestyle
        for s, e, st in intervals_all:
            if e <= s or (st is not True):
                continue
            seg = plot_data[(plot_data['Time'] >= s) & (plot_data['Time'] <= e)]
            if seg.empty:
                continue
            ax.plot(
                seg['Time'], seg['Value'],
                linewidth=line_width,
                label="_nolegend_",
                color=shade_color,
                linestyle=line_style,
                dash_capstyle='butt',
                dash_joinstyle='miter',
                zorder=0.7,
                alpha=line_alpha,
            )
        return True

    def _get_all_variables(self):
        """Get all unique variables across experiments."""
        all_variables = set()
        for exp in self.data:
            if not exp.validation_data.empty:
                variables = exp.validation_data['Variable'].unique()
                all_variables.update(variables)
        return sorted(list(all_variables))

    def create_plots(self, title: str = "All Experiments - Variable Analysis", 
                    show_legend: bool = True, legend_position: str = "upper right"):
        if not self.data:
            print("No experiments added. Call add_data() first.")
            return self
        
        # Create panels based on experiments and variables
        self._create_panels()
        
        # Plot each variable in its panel
        for var_idx, variable in enumerate(self.panels.variables):
            if var_idx < len(self.panels.axes):
                self._plot_panel(self.panels.axes[var_idx], variable, show_legend)
        
        # Apply axis configurations from DataModels automatically
        self.apply_axis_configs()
        
        print(f"Created plot with {len(self.panels.variables)} variables")
        return self

    def save_plots(self, filename: str = "all_experiments_plot.pdf"):
        """Save the current figure to disk.
        
        Args:
            filename: Output filename
        """
        if not self.current_figure:
            print("No figure to save. Call create_plots() first.")
            return self
        
        mpb.save_panel(self.current_figure, filename)
        print(f"Saved plot to: {filename}")
        
        return self

    def update_ax(self, panel_id: int = None, xlabel: str = None, ylabel: str = None, 
                   xlim: tuple = None, ylim: tuple = None, 
                   xtick_distance: float = None, ytick_distance: float = None):
        """Update axis properties for specific panel or all panels.
        
        Args:
            panel_id: Panel index to update (0-based, if None, updates all panels)
            xlabel: x-axis label
            ylabel: y-axis label  
            xlim: x-axis limits (xmin, xmax)
            ylim: y-axis limits (ymin, ymax)
            xtick_distance: Distance between x-axis ticks
            ytick_distance: Distance between y-axis ticks
        """
        if not self.panels or not self.panels.axes:
            print("No panels available. Call create_plots() first.")
            return self
            
        # Determine which axes to update
        if panel_id is not None:
            if panel_id < 0 or panel_id >= len(self.panels.axes):
                print(f"Panel ID {panel_id} is out of range. Available panels: 0-{len(self.panels.axes)-1}")
                return self
            axes_to_update = [self.panels.axes[panel_id]]
        else:
            axes_to_update = self.panels.axes
            
        # Update axis
        for ax in axes_to_update:
            #update x and y labels
            if xlabel is not None:
                ax.set_xlabel(xlabel)
            if ylabel is not None:
                ax.set_ylabel(ylabel)
            # update x and y limits
            if xlim is not None:
                ax.set_xlim(xlim)
            if ylim is not None:
                ax.set_ylim(ylim)
            # update ticks distance for x-axis
            if xtick_distance is not None:
                x_min, x_max = ax.get_xlim()
                step = float(xtick_distance)
                new_ticks = []
                current_tick = x_min
                while current_tick <= x_max:
                    new_ticks.append(current_tick)
                    current_tick += step
                ax.set_xticks(new_ticks)
            # update ticks distance for y-axis
            if ytick_distance is not None:
                y_min, y_max = ax.get_ylim()
                step = float(ytick_distance)
                new_ticks = []
                current_tick = y_min
                while current_tick <= y_max:
                    new_ticks.append(current_tick)
                    current_tick += step
                ax.set_yticks(new_ticks)
                
        return self

    def apply_axis_configs(self):
        """Apply axis configurations from stored Experiments."""
        if not self.panels or not self.panels.axes:
            print("No panels available. Call create_plots() first.")
            return self
            
        for panel_id, data_model in enumerate(self.data):
            if panel_id < len(self.panels.axes) and data_model.ax:
                ax_config = data_model.ax
                self.update_ax(
                    panel_id=panel_id,
                    xlabel=ax_config.xlabel,
                    ylabel=ax_config.ylabel,
                    xlim=ax_config.xlim,
                    ylim=ax_config.ylim,
                    xtick_distance=ax_config.xtick_distance,
                    ytick_distance=ax_config.ytick_distance
                )
        return self

    def close_plots(self):
        """Close the current figure to free memory."""
        if self.current_figure:
            plt.close(self.current_figure)
            self.current_figure = None
        self.panels = None
        print("Closed figure")
        return self
