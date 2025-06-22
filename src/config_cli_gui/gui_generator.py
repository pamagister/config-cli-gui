# config_framework/gui.py
"""Generic GUI settings dialog generator for configuration framework."""

import calendar
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from config_cli_gui.config_framework import Color, ConfigManager, ConfigParameter


class ToolTip:
    """Create a tooltip for a given widget."""

    def __init__(self, widget, text="widget info"):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event=None):
        self.show_tooltip()

    def on_leave(self, event=None):
        self.hide_tooltip()

    def show_tooltip(self):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
        )
        label.pack(ipadx=1)

    def hide_tooltip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class CalendarDialog:
    """Simple calendar dialog for date selection."""

    def __init__(self, parent, initial_date: datetime = None):
        self.parent = parent
        self.result = None
        self.initial_date = initial_date or datetime.now()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Date")
        self.dialog.geometry("300x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.geometry(
            f"+{int(parent.winfo_rootx() + 100)}+{int(parent.winfo_rooty() + 100)}"
        )

        self._create_widgets()

    def _create_widgets(self):
        """Create calendar widgets."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Year selection
        year_frame = ttk.Frame(main_frame)
        year_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(year_frame, text="Year:").pack(side=tk.LEFT)
        self.year_var = tk.IntVar(value=self.initial_date.year)
        year_spinbox = ttk.Spinbox(
            year_frame,
            from_=1900,
            to=2100,
            textvariable=self.year_var,
            command=self._update_calendar,
            width=10,
        )
        year_spinbox.pack(side=tk.LEFT, padx=(5, 0))

        # Month selection
        month_frame = ttk.Frame(main_frame)
        month_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(month_frame, text="Month:").pack(side=tk.LEFT)
        self.month_var = tk.IntVar(value=self.initial_date.month)
        month_combo = ttk.Combobox(
            month_frame,
            textvariable=self.month_var,
            values=list(range(1, 13)),
            state="readonly",
            width=8,
        )
        month_combo.pack(side=tk.LEFT, padx=(5, 0))
        month_combo.bind("<<ComboboxSelected>>", lambda e: self._update_calendar())

        # Day selection
        day_frame = ttk.Frame(main_frame)
        day_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(day_frame, text="Day:").pack(side=tk.LEFT)
        self.day_var = tk.IntVar(value=self.initial_date.day)
        self.day_spinbox = ttk.Spinbox(
            day_frame, from_=1, to=31, textvariable=self.day_var, width=8
        )
        self.day_spinbox.pack(side=tk.LEFT, padx=(5, 0))

        # Time selection
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(time_frame, text="Time:").pack(side=tk.LEFT)

        self.hour_var = tk.IntVar(value=self.initial_date.hour)
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=4).pack(
            side=tk.LEFT, padx=(5, 2)
        )
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)

        self.minute_var = tk.IntVar(value=self.initial_date.minute)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=4).pack(
            side=tk.LEFT, padx=(2, 0)
        )

        self._update_calendar()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT)

    def _update_calendar(self):
        """Update day spinbox based on selected month/year."""
        year = self.year_var.get()
        month = self.month_var.get()
        max_day = calendar.monthrange(year, month)[1]
        self.day_spinbox.configure(to=max_day)

        # Adjust day if it's beyond the valid range
        if self.day_var.get() > max_day:
            self.day_var.set(max_day)

    def _on_ok(self):
        """Handle OK button."""
        try:
            self.result = datetime(
                year=self.year_var.get(),
                month=self.month_var.get(),
                day=self.day_var.get(),
                hour=self.hour_var.get(),
                minute=self.minute_var.get(),
            )
            self.dialog.destroy()
        except ValueError as e:
            messagebox.showerror("Invalid Date", f"Invalid date/time: {e}")

    def _on_cancel(self):
        """Handle Cancel button."""
        self.result = None
        self.dialog.destroy()


class SettingsDialogGenerator:
    """Generates settings dialog from ConfigManager."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def create_settings_dialog(
        self, parent, title="Settings", config_file="config.yaml"
    ) -> "GenericSettingsDialog":
        """Create a settings dialog for the configuration."""
        return GenericSettingsDialog(parent, self.config_manager, title, config_file)


class GenericSettingsDialog:
    """Generic settings dialog for ConfigManager."""

    def __init__(
        self, parent, config_manager: ConfigManager, title="Settings", config_file="config.yaml"
    ):
        self.parent = parent
        self.config_manager = config_manager
        self.config_file = config_file
        self.result = None
        self.widgets = {}

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.geometry(f"+{int(parent.winfo_rootx() + 50)}+{int(parent.winfo_rooty() + 50)}")

        self._create_widgets()

        # Handle window closing
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _create_widgets(self):
        """Create the settings dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs for each configuration category
        for category_name, category in self.config_manager._categories.items():
            self._create_category_tab(category_name, category)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT)

    def _create_category_tab(self, category_name: str, category):
        """Create a tab for a configuration category."""
        # Create tab frame
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=category_name.title())

        # Create scrollable frame
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add parameters
        self._add_category_parameters(scrollable_frame, category_name, category)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _add_category_parameters(self, parent, category_name: str, category):
        """Add parameter widgets for a specific category."""
        row = 0
        parameters = category.get_parameters()

        for param in parameters:
            if param.required:
                # Skip required parameters as they are not configurable in GUI
                continue

            # Create label
            label = ttk.Label(parent, text=f"{param.name}:")
            label.grid(row=row, column=0, sticky="w", padx=5, pady=2)

            # Create appropriate widget based on parameter type
            widget = self._create_parameter_widget(parent, param)
            widget.grid(row=row, column=1, sticky="ew", padx=5, pady=2)

            # Add tooltip
            ToolTip(label, param.help)
            if hasattr(widget, "entry_widget"):
                ToolTip(widget.entry_widget, param.help)
            else:
                ToolTip(widget, param.help)

            # Store widget reference
            self.widgets[f"{category_name}__{param.name}"] = widget

            row += 1

        # Configure column weights
        parent.columnconfigure(1, weight=1)

    def _create_parameter_widget(self, parent, param: ConfigParameter):
        """Create appropriate widget for parameter type."""
        param_type = type(param.default)

        # Boolean type - Checkbox
        if param_type == bool:
            var = tk.BooleanVar(value=param.default)
            widget = ttk.Checkbutton(parent, variable=var)
            widget.var = var
            return widget

        # Path type - File/Directory selector
        elif param_type == Path:
            return self._create_path_widget(parent, param)

        # Color type - Color picker
        elif param_type == Color:
            return self._create_color_widget(parent, param)

        # DateTime type - DateTime picker
        elif param_type == datetime:
            return self._create_datetime_widget(parent, param)

        # List/Tuple with choices - Combobox
        elif param.choices and param_type != bool:
            var = tk.StringVar(value=str(param.default))
            widget = ttk.Combobox(
                parent, textvariable=var, values=list(param.choices), state="readonly"
            )
            widget.var = var
            return widget

        # List/Tuple type - Multi-entry widget
        elif param_type in (list, tuple):
            return self._create_list_widget(parent, param)

        # Dict type - Key-Value editor
        elif param_type == dict:
            return self._create_dict_widget(parent, param)

        # Integer type - Spinbox
        elif param_type == int:
            var = tk.IntVar(value=param.default)
            widget = ttk.Spinbox(parent, from_=-999999, to=999999, textvariable=var)
            widget.var = var
            return widget

        # Float type - Spinbox
        elif param_type == float:
            var = tk.DoubleVar(value=param.default)
            widget = ttk.Spinbox(
                parent, from_=-999999.0, to=999999.0, increment=1.0, textvariable=var
            )
            widget.var = var
            return widget

        # Default: String type - Entry
        else:
            var = tk.StringVar(value=str(param.default))
            widget = ttk.Entry(parent, textvariable=var)
            widget.var = var
            return widget

    def _create_path_widget(self, parent, param: ConfigParameter):
        """Create file/directory selector widget."""
        frame = ttk.Frame(parent)

        var = tk.StringVar(value=str(param.default))
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def browse_file():
            if param.default.is_dir() if isinstance(param.default, Path) else False:
                path = filedialog.askdirectory(initialdir=str(param.default.parent))
            else:
                path = filedialog.askopenfilename(initialdir=str(param.default.parent))
            if path:
                var.set(path)

        browse_btn = ttk.Button(frame, text="Browse", command=browse_file)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        frame.var = var
        frame.entry_widget = entry
        return frame

    def _create_color_widget(self, parent, param: ConfigParameter):
        """Create color picker widget."""
        frame = ttk.Frame(parent)

        color_value = param.default if isinstance(param.default, Color) else Color()
        var = tk.StringVar(value=color_value.to_hex())

        entry = ttk.Entry(frame, textvariable=var, width=10)
        entry.pack(side=tk.LEFT)

        color_display = tk.Label(frame, width=3, bg=color_value.to_hex())
        color_display.pack(side=tk.LEFT, padx=(5, 0))

        def pick_color():
            color = colorchooser.askcolor(color=var.get())
            if color[1]:  # color[1] is hex string
                var.set(color[1])
                color_display.config(bg=color[1])

        pick_btn = ttk.Button(frame, text="Pick", command=pick_color)
        pick_btn.pack(side=tk.LEFT, padx=(5, 0))

        def on_color_change(*args):
            try:
                color_display.config(bg=var.get())
            except tk.TclError:
                pass

        var.trace("w", on_color_change)

        frame.var = var
        frame.entry_widget = entry
        return frame

    def _create_datetime_widget(self, parent, param: ConfigParameter):
        """Create datetime picker widget."""
        frame = ttk.Frame(parent)

        dt_value = param.default if isinstance(param.default, datetime) else datetime.now()
        var = tk.StringVar(value=dt_value.strftime("%Y-%m-%d %H:%M"))

        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def pick_datetime():
            dialog = CalendarDialog(self.dialog, dt_value)
            self.dialog.wait_window(dialog.dialog)
            if dialog.result:
                var.set(dialog.result.strftime("%Y-%m-%d %H:%M"))

        cal_btn = ttk.Button(frame, text="Calendar", command=pick_datetime)
        cal_btn.pack(side=tk.RIGHT, padx=(5, 0))

        frame.var = var
        frame.entry_widget = entry
        return frame

    def _create_list_widget(self, parent, param: ConfigParameter):
        """Create list/tuple editor widget."""
        frame = ttk.Frame(parent)

        # Convert list/tuple to comma-separated string
        if isinstance(param.default, (list | tuple)):
            value_str = ", ".join(str(item) for item in param.default)
        else:
            value_str = str(param.default)

        var = tk.StringVar(value=value_str)
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(frame, text="(comma-separated)").pack(side=tk.RIGHT, padx=(5, 0))

        frame.var = var
        frame.entry_widget = entry
        return frame

    def _create_dict_widget(self, parent, param: ConfigParameter):
        """Create dictionary editor widget."""
        frame = ttk.Frame(parent)

        # Convert dict to JSON-like string
        if isinstance(param.default, dict):
            import json

            value_str = json.dumps(param.default, indent=None, separators=(",", ":"))
        else:
            value_str = str(param.default)

        var = tk.StringVar(value=value_str)
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(frame, text="(JSON format)").pack(side=tk.RIGHT, padx=(5, 0))

        frame.var = var
        frame.entry_widget = entry
        return frame

    def _on_ok(self):
        """Handle OK button click."""
        try:
            # Update configuration with widget values
            overrides = {}
            for key, widget in self.widgets.items():
                value = widget.var.get()

                # Parse value based on parameter type
                category_name, param_name = key.split("__", 1)
                category = self.config_manager.get_category(category_name)
                param = getattr(category, param_name)

                # Convert value to appropriate type
                if type(param.default) == bool:
                    overrides[key] = value
                elif type(param.default) == Path:
                    overrides[key] = Path(value)
                elif type(param.default) == Color:
                    overrides[key] = Color.from_hex(value)
                elif type(param.default) == datetime:
                    overrides[key] = datetime.strptime(value, "%Y-%m-%d %H:%M")
                elif type(param.default) in (list, tuple):
                    # Parse comma-separated values
                    items = [item.strip() for item in value.split(",") if item.strip()]
                    overrides[key] = type(param.default)(items)
                elif type(param.default) == dict:
                    # Parse JSON format
                    import json

                    overrides[key] = json.loads(value)
                elif type(param.default) == int:
                    overrides[key] = int(value)
                elif type(param.default) == float:
                    overrides[key] = float(value)
                else:
                    overrides[key] = value

            # Apply overrides to config manager
            self.config_manager._apply_kwargs(overrides)

            # Save to file
            self.config_manager.save_to_file(self.config_file)

            self.result = "ok"
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def _on_cancel(self):
        """Handle Cancel button click."""
        self.result = "cancel"
        self.dialog.destroy()
