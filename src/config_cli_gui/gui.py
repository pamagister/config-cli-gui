"""Generic GUI settings dialog generator for configuration framework."""

import calendar
import json
import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk
from typing import Any

import ttkbootstrap
from PIL import Image, ImageDraw, ImageTk

from config_cli_gui.config import (
    ConfigCategory,
    ConfigManager,
    ConfigParameter,
    ConfigSerializer,
)
from config_cli_gui.configtypes.color import Color
from config_cli_gui.configtypes.font import Font
from config_cli_gui.configtypes.vector import Vector

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ToolTip:
    """Create a tooltip for a given widget."""

    def __init__(self, widget, text="widget info", delay_ms: int = 400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

        self.widget.bind("<Enter>", self.on_enter, add="+")
        self.widget.bind("<Leave>", self.on_leave, add="+")
        self.widget.bind("<ButtonPress>", self.on_leave, add="+")

    def on_enter(self, event=None):
        self._cancel()
        self.id = self.widget.after(self.delay_ms, self.show_tooltip)

    def on_leave(self, event=None):
        self._cancel()
        self.hide_tooltip()

    def _cancel(self):
        if self.id is not None:
            self.widget.after_cancel(self.id)
            self.id = None

    def show_tooltip(self):
        self.id = None
        if self.tipwindow or not self.text:
            return
        # Position next to the mouse pointer; works for every widget type.
        x = self.widget.winfo_pointerx() + 15
        y = self.widget.winfo_pointery() + 15
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            foreground="#000000",
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=400,
            padx=4,
            pady=2,
        )
        label.pack()

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

        # Date selection in a single row
        date_label_frame = ttk.Frame(main_frame)
        date_label_frame.pack(fill=tk.X, pady=(0, 2))

        ttk.Label(date_label_frame, text="Year:").pack(side=tk.LEFT, expand=True)
        ttk.Label(date_label_frame, text="Month:").pack(side=tk.LEFT, expand=True)
        ttk.Label(date_label_frame, text="Day:").pack(side=tk.LEFT, expand=True)

        date_input_frame = ttk.Frame(main_frame)
        date_input_frame.pack(fill=tk.X, pady=(0, 10))

        self.year_var = tk.IntVar(value=self.initial_date.year)
        year_spinbox = ttk.Spinbox(
            date_input_frame,
            from_=1900,
            to=2100,
            textvariable=self.year_var,
            command=self._update_calendar,
            width=8,
        )
        year_spinbox.pack(side=tk.LEFT, expand=True, padx=(0, 5))

        self.month_var = tk.IntVar(value=self.initial_date.month)
        month_combo = ttk.Combobox(
            date_input_frame,
            textvariable=self.month_var,
            values=list(range(1, 13)),
            state="readonly",
            width=8,
        )
        month_combo.pack(side=tk.LEFT, expand=True, padx=(0, 5))
        month_combo.bind("<<ComboboxSelected>>", lambda e: self._update_calendar())

        self.day_var = tk.IntVar(value=self.initial_date.day)
        self.day_spinbox = ttk.Spinbox(
            date_input_frame, from_=1, to=31, textvariable=self.day_var, width=8
        )
        self.day_spinbox.pack(side=tk.LEFT, expand=True)

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

        ttk.Button(button_frame, text="OK", command=self._on_ok, width=10).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel, width=10).pack(
            side=tk.RIGHT
        )

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


class _ScrollableFrame(ttk.Frame):
    """Vertically scrollable frame whose ``content`` stretches to the available width."""

    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, padding=(5, 5))
        self._window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.content.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>", lambda e: self.canvas.itemconfigure(self._window, width=e.width)
        )
        # A plain tk.Canvas does not follow the ttk theme; keep its background in sync.
        self.canvas.bind("<<ThemeChanged>>", lambda e: self._sync_background(), add="+")
        self._sync_background()

    def _sync_background(self) -> None:
        background = ttk.Style().lookup("TFrame", "background")
        if background:
            self.canvas.configure(background=background)

    def scroll(self, units: int) -> None:
        if self.canvas.yview() != (0.0, 1.0):  # only when the content overflows
            self.canvas.yview_scroll(units, "units")


class GenericSettingsDialog:
    """Generic settings dialog for ConfigManager."""

    def __init__(
        self,
        parent: ttkbootstrap.Window | tk.Tk,
        config_manager: ConfigManager,
        title="Settings",
        config_file="config.yaml",
    ):
        self.parent = parent
        self.config_manager: ConfigManager = config_manager
        self.config_file = config_file
        self.result = None
        self.widgets = {}
        self._serializer = ConfigSerializer()
        self._tabs: list[tuple[str, _ScrollableFrame]] = []

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.minsize(500, 350)
        self.dialog.transient(parent)

        self._create_widgets()
        self._place_dialog(760, 600)
        self.dialog.grab_set()

        # Window closing and keyboard shortcuts
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())
        self.dialog.bind("<Return>", lambda e: self._on_ok())
        # Wheel events of all child widgets propagate to the toplevel binding.
        self.dialog.bind("<MouseWheel>", self._on_mousewheel)
        self.dialog.bind("<Button-4>", self._on_mousewheel)
        self.dialog.bind("<Button-5>", self._on_mousewheel)

    def _place_dialog(self, width: int, height: int) -> None:
        """Center the dialog over its parent window."""
        self.parent.update_idletasks()
        x = self.parent.winfo_rootx() + max((self.parent.winfo_width() - width) // 2, 0)
        y = self.parent.winfo_rooty() + max((self.parent.winfo_height() - height) // 2, 0)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self):
        """Create the settings dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Button frame (packed first so it stays visible when the dialog shrinks)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs for each configuration category
        for category_name, category in self.config_manager.iter_categories():
            self._create_category_tab(category_name, category)

        reset_btn = ttk.Button(button_frame, text="Reset Tab", command=self._on_reset_tab)
        reset_btn.pack(side=tk.LEFT)
        ToolTip(reset_btn, "Restore the default values of all settings on the current tab")

        # Apply: apply current settings (in-memory) but keep dialog open
        ttk.Button(button_frame, text="Apply", command=self._on_apply, width=10).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="OK", command=self._on_ok, width=10).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel, width=10).pack(
            side=tk.RIGHT
        )

    def _create_category_tab(self, category_name: str, category):
        """Create a tab for a configuration category."""
        tab = _ScrollableFrame(self.notebook)
        self.notebook.add(tab, text="  " + category_name.title() + "  ")
        self._tabs.append((category_name, tab))
        self._add_category_parameters(tab.content, category, category_name)

    def _add_category_parameters(
        self, parent, category: ConfigCategory, category_name: str | None = None
    ):
        """Add parameter widgets for a specific category."""
        category_name = category_name or category.get_category_name()

        for row, param in enumerate(category.get_parameters()):
            # Create label (fixed width for alignment)
            label = ttk.Label(parent, text=f"{param.name}:", width=28, anchor="w")
            label.grid(row=row, column=0, sticky="w", padx=5, pady=4)

            # Create appropriate widget based on parameter type
            widget = self._create_parameter_widget(parent, param)
            widget.grid(row=row, column=1, sticky="ew", padx=5, pady=4)

            # Add tooltip
            ToolTip(label, param.help)
            ToolTip(getattr(widget, "entry_widget", widget), param.help)

            # Store widget reference
            self.widgets[f"{category_name}__{param.name}"] = widget

        # Configure column weights
        parent.columnconfigure(1, weight=1)

    @staticmethod
    def _bind_value(widget, getter: Callable[[], Any], setter: Callable[[Any], None]):
        """Attach ``get_value()`` (typed, raises ValueError) and ``set_value(v)`` to a widget."""
        widget.get_value = getter
        widget.set_value = setter
        return widget

    def _create_parameter_widget(self, parent, param: ConfigParameter):
        """Create appropriate widget for parameter type."""
        # Boolean type - Checkbox
        if isinstance(param.value, bool):
            var = tk.BooleanVar(value=param.value)
            widget = ttk.Checkbutton(parent, variable=var)
            widget.var = var
            return self._bind_value(widget, lambda: bool(var.get()), lambda v: var.set(bool(v)))

        # Path type - File/Directory selector
        elif isinstance(param.value, Path):
            return self._create_path_widget(parent, param)

        # Color type - Color picker
        elif isinstance(param.value, Color):
            return self._create_color_widget(parent, param)

        # Font type - Font picker
        elif isinstance(param.value, Font):
            return self._create_font_widget(parent, param)

        # Vector type - Vector editor
        elif isinstance(param.value, Vector):
            return self._create_vector_widget(parent, param)

        # DateTime type - DateTime picker
        elif isinstance(param.value, datetime):
            return self._create_datetime_widget(parent, param)

        # Choices - Combobox
        elif param.choices:
            return self._create_choice_widget(parent, param)

        # List/Tuple type - Multi-entry widget
        elif isinstance(param.value, list) or isinstance(param.value, tuple):
            return self._create_list_widget(parent, param)

        # Dict type - Key-Value editor
        elif isinstance(param.value, dict):
            return self._create_dict_widget(parent, param)

        # Integer type - Spinbox
        elif isinstance(param.value, int):
            var = tk.IntVar(value=param.value)
            widget = ttk.Spinbox(parent, from_=-999999, to=999999, textvariable=var)
            widget.var = var
            return self._bind_value(
                widget, lambda: self._serializer.convert(widget.get().strip(), int), var.set
            )

        # Float type - Spinbox
        elif isinstance(param.value, float):
            var = tk.DoubleVar(value=param.value)
            widget = ttk.Spinbox(
                parent, from_=-999999.0, to=999999.0, increment=1.0, textvariable=var
            )
            widget.var = var
            return self._bind_value(
                widget, lambda: self._serializer.convert(widget.get().strip(), float), var.set
            )

        # Default: String type - Entry
        else:
            var = tk.StringVar(value="" if param.value is None else str(param.value))
            widget = ttk.Entry(parent, textvariable=var)
            widget.var = var
            keep_none = param.value is None
            return self._bind_value(
                widget,
                lambda: (var.get() or None) if keep_none else var.get(),
                lambda v: var.set("" if v is None else str(v)),
            )

    def _create_choice_widget(self, parent, param: ConfigParameter):
        """Create a read-only combobox; the selection maps back to the original choice object."""
        lookup = {str(choice): choice for choice in param.choices or []}
        var = tk.StringVar(value=str(param.value))
        widget = ttk.Combobox(parent, textvariable=var, values=list(lookup), state="readonly")
        widget.var = var

        def get_value():
            text = var.get()
            if text in lookup:
                return lookup[text]
            return self._serializer.convert(text, param.type_)

        return self._bind_value(widget, get_value, lambda v: var.set(str(v)))

    def _create_path_widget(self, parent, param: ConfigParameter):
        """Create file/directory selector widget."""
        frame = ttk.Frame(parent)

        var = tk.StringVar(value=str(param.value))
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def initial_dir() -> str:
            current = Path(var.get().strip() or ".").expanduser()
            for candidate in (current, current.parent):
                if candidate.is_dir():
                    return str(candidate.resolve())
            return str(Path.cwd())

        def browse_file():
            path = filedialog.askopenfilename(initialdir=initial_dir(), parent=self.dialog)
            if path:
                var.set(path)

        def browse_dir():
            path = filedialog.askdirectory(initialdir=initial_dir(), parent=self.dialog)
            if path:
                var.set(path)

        browse_btn = ttk.Button(frame, text="File", command=browse_file, width=10)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        browse_btn = ttk.Button(frame, text="Directory", command=browse_dir, width=10)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        frame.var = var
        frame.entry_widget = entry
        return self._bind_value(frame, lambda: Path(var.get().strip()), lambda v: var.set(str(v)))

    @staticmethod
    def _create_color_swatch(frame, var: tk.StringVar) -> tk.Label:
        """Create a color preview label that follows ``var`` while the hex code is valid."""
        swatch = tk.Label(frame, width=8, relief=tk.SOLID, borderwidth=1)

        def on_color_change(*args):
            if Color.is_valid_hex(var.get()):
                swatch.config(bg=Color.from_hex(var.get()).to_hex())

        var.trace_add("write", on_color_change)
        on_color_change()
        return swatch

    @staticmethod
    def _parse_color(text: str) -> Color:
        if not Color.is_valid_hex(text):
            raise ValueError(f"Invalid color {text!r}, expected #rrggbb")
        return Color.from_hex(text)

    def _pick_color(self, var: tk.StringVar) -> None:
        initial = var.get() if Color.is_valid_hex(var.get()) else None
        color = colorchooser.askcolor(color=initial, parent=self.dialog)
        if color[1]:  # color[1] is hex string
            var.set(color[1])

    def _create_color_widget(self, parent, param: ConfigParameter):
        """Create color picker widget."""
        frame = ttk.Frame(parent)

        color_value = param.value if isinstance(param.value, Color) else Color()
        var = tk.StringVar(value=color_value.to_hex())

        entry = ttk.Entry(frame, textvariable=var, width=10)
        entry.pack(side=tk.LEFT)

        self._create_color_swatch(frame, var).pack(side=tk.LEFT, padx=(8, 2), fill=tk.Y)

        pick_btn = ttk.Button(frame, text="Pick", command=lambda: self._pick_color(var), width=10)
        pick_btn.pack(side=tk.LEFT, padx=(5, 0))

        frame.var = var
        frame.entry_widget = entry
        return self._bind_value(
            frame, lambda: self._parse_color(var.get().strip()), lambda v: var.set(v.to_hex())
        )

    def _create_font_widget(self, parent, param: ConfigParameter):
        """Create font picker widget."""
        frame = ttk.Frame(parent)
        font_value = param.value if isinstance(param.value, Font) else Font("Arial", 12, Color())

        # Font type
        font_type_var = tk.StringVar(value=Path(font_value.name).name)
        font_type_combo = ttk.Combobox(
            frame,
            textvariable=font_type_var,
            values=Font.font_names,
            state="readonly",
            width=20,
        )
        font_type_combo.pack(side=tk.LEFT, padx=(0, 5))

        # Font size
        font_size_var = tk.DoubleVar(value=font_value.size)
        font_size_spinbox = ttk.Spinbox(frame, from_=1, to=100, textvariable=font_size_var, width=5)
        font_size_spinbox.pack(side=tk.LEFT, padx=(0, 5))

        # Font color
        color_var = tk.StringVar(value=font_value.color.to_hex())
        self._create_color_swatch(frame, color_var).pack(side=tk.LEFT, padx=(8, 2), fill=tk.Y)

        pick_btn = ttk.Button(
            frame, text="Pick Color", command=lambda: self._pick_color(color_var), width=10
        )
        pick_btn.pack(side=tk.LEFT, padx=(5, 0))

        def get_value() -> Font:
            size = self._serializer.convert(font_size_spinbox.get().strip(), float)
            if size <= 0:
                raise ValueError(f"Font size must be positive, got {size}")
            return Font(font_type_var.get(), size, self._parse_color(color_var.get().strip()))

        def set_value(font: Font) -> None:
            font_type_var.set(Path(font.name).name)
            font_size_var.set(font.size)
            color_var.set(font.color.to_hex())

        def show_preview():
            try:
                font_obj = get_value()
            except ValueError as e:
                messagebox.showerror("Invalid font", str(e), parent=self.dialog)
                return

            font_size = int(font_obj.size)
            img_width = 170 + 3 * font_size
            img_height = 20 + font_size

            preview_win = tk.Toplevel(self.dialog)
            preview_win.title("Font Preview")
            preview_win.geometry(f"{img_width}x{img_height}")
            preview_win.transient(self.dialog)
            preview_win.grab_set()
            preview_win.bind("<Escape>", lambda e: preview_win.destroy())

            img = Image.new("RGB", (img_width, img_height), "white")
            draw = ImageDraw.Draw(img)
            draw.text(
                (img_width / 2, img_height / 2),
                "Sample",
                fill=font_obj.color.to_hex(),
                font=font_obj.get_image_font(),
                anchor="mm",
            )

            photo = ImageTk.PhotoImage(img)

            img_label = tk.Label(preview_win, image=photo)
            img_label.image = photo
            img_label.pack()

        preview_btn = ttk.Button(frame, text="Preview", command=show_preview, width=10)
        preview_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Store variables in the frame for later access
        frame.font_type_var = font_type_var
        frame.font_size_var = font_size_var
        frame.color_var = color_var
        frame.entry_widget = font_type_combo
        return self._bind_value(frame, get_value, set_value)

    def _create_vector_widget(self, parent, param: ConfigParameter):
        """Create vector editor widget."""
        frame = ttk.Frame(parent)

        vector_value = param.value if isinstance(param.value, Vector) else Vector(0, 0)
        components = vector_value.to_list()
        # Integer vectors stay integer vectors as long as the user enters whole numbers.
        integer_vector = all(isinstance(c, int) for c in components)

        frame.vars = []
        spinboxes = []
        for value in components:
            var = tk.DoubleVar(value=value)
            spinbox = ttk.Spinbox(
                frame,
                from_=-999999.0,
                to=999999.0,
                increment=1.0,
                textvariable=var,
                width=8,
            )
            spinbox.pack(side=tk.LEFT, padx=(0, 5))
            frame.vars.append(var)
            spinboxes.append(spinbox)

        if spinboxes:
            frame.entry_widget = spinboxes[0]

        def get_value() -> Vector:
            values = [self._serializer.convert(s.get().strip(), float) for s in spinboxes]
            if integer_vector and all(v.is_integer() for v in values):
                return Vector(*(int(v) for v in values))
            return Vector(*values)

        def set_value(vector: Vector) -> None:
            for var, component in zip(frame.vars, vector.to_list()):
                var.set(component)

        return self._bind_value(frame, get_value, set_value)

    def _create_datetime_widget(self, parent, param: ConfigParameter):
        """Create datetime picker widget."""
        frame = ttk.Frame(parent)

        dt_value = param.value if isinstance(param.value, datetime) else datetime.now()
        var = tk.StringVar(value=dt_value.strftime(DATETIME_FORMAT))

        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def get_value() -> datetime:
            return datetime.fromisoformat(var.get().strip())

        def pick_datetime():
            try:
                initial = get_value()
            except ValueError:
                initial = dt_value
            dialog = CalendarDialog(self.dialog, initial)
            self.dialog.wait_window(dialog.dialog)
            if dialog.result:
                var.set(dialog.result.strftime(DATETIME_FORMAT))

        cal_btn = ttk.Button(frame, text="Calendar", command=pick_datetime, width=10)
        cal_btn.pack(side=tk.RIGHT, padx=(5, 0))

        frame.var = var
        frame.entry_widget = entry
        return self._bind_value(frame, get_value, lambda v: var.set(v.strftime(DATETIME_FORMAT)))

    def _create_list_widget(self, parent, param: ConfigParameter):
        """Create list/tuple editor widget."""
        frame = ttk.Frame(parent)

        sequence_type = type(param.value)
        item_types = {type(item) for item in param.value}
        # Homogeneous lists of plain values keep their item type; everything else becomes str.
        item_type = item_types.pop() if len(item_types) == 1 else str
        if item_type not in (bool, int, float, str):
            item_type = str

        var = tk.StringVar(value=", ".join(str(item) for item in param.value))
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(frame, text="(comma-separated)").pack(side=tk.RIGHT, padx=(5, 0))

        def get_value():
            items = [item.strip() for item in var.get().split(",") if item.strip()]
            return sequence_type(self._serializer.convert(item, item_type) for item in items)

        frame.var = var
        frame.entry_widget = entry
        return self._bind_value(
            frame, get_value, lambda v: var.set(", ".join(str(item) for item in v))
        )

    def _create_dict_widget(self, parent, param: ConfigParameter):
        """Create dictionary editor widget."""
        frame = ttk.Frame(parent)

        var = tk.StringVar(value=json.dumps(param.value, separators=(",", ":")))
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(frame, text="(JSON format)").pack(side=tk.RIGHT, padx=(5, 0))

        def get_value() -> dict:
            value = json.loads(var.get())
            if not isinstance(value, dict):
                raise ValueError("A JSON object ({...}) is expected")
            return value

        frame.var = var
        frame.entry_widget = entry
        return self._bind_value(
            frame, get_value, lambda v: var.set(json.dumps(v, separators=(",", ":")))
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _current_tab(self) -> tuple[str, _ScrollableFrame] | None:
        if not self._tabs:
            return None
        return self._tabs[self.notebook.index(self.notebook.select())]

    def _on_mousewheel(self, event):
        """Scroll the visible tab, unless the wheel is used on a value widget."""
        if event.widget.winfo_class() in ("TCombobox", "TSpinbox"):
            return
        tab = self._current_tab()
        if tab is None:
            return
        if getattr(event, "num", None) == 4:
            units = -1
        elif getattr(event, "num", None) == 5:
            units = 1
        else:
            units = -1 if event.delta > 0 else 1
        tab[1].scroll(units)

    def _on_reset_tab(self):
        """Reset the widgets of the current tab to the declared default values."""
        tab = self._current_tab()
        if tab is None:
            return
        category_name = tab[0]
        if not messagebox.askyesno(
            "Reset to defaults",
            f"Reset all settings on the '{category_name}' tab to their default values?\n"
            "Changes are saved when you press OK or Apply.",
            parent=self.dialog,
        ):
            return
        for key, widget in self.widgets.items():
            widget_category, param_name = key.split("__", 1)
            if widget_category != category_name:
                continue
            param = self.config_manager.get_parameter(widget_category, param_name)
            if param is not None:
                widget.set_value(param.default_value)

    def _collect_values(self) -> tuple[dict[str, Any], list[tuple[str, str]]]:
        """Read all widgets; return ``(overrides, [(key, error message), ...])``."""
        values: dict[str, Any] = {}
        errors: list[tuple[str, str]] = []
        for key, widget in self.widgets.items():
            try:
                values[key] = widget.get_value()
            except (ValueError, TypeError, tk.TclError) as e:
                errors.append((key, str(e)))
        return values, errors

    def _show_errors(self, errors: list[tuple[str, str]]) -> None:
        """Report invalid fields and jump to the first one."""
        lines = [f"• {key.replace('__', '.')}: {message}" for key, message in errors]
        messagebox.showerror(
            "Invalid settings",
            "Please correct the following settings:\n\n" + "\n".join(lines),
            parent=self.dialog,
        )
        first_key = errors[0][0]
        category_name = first_key.split("__", 1)[0]
        for index, (name, _) in enumerate(self._tabs):
            if name == category_name:
                self.notebook.select(index)
                break
        widget = self.widgets[first_key]
        getattr(widget, "entry_widget", widget).focus_set()

    def _persist_settings(self) -> bool:
        """Apply the widget values and save them; return False if a value is invalid."""
        overrides, errors = self._collect_values()
        if errors:
            self._show_errors(errors)
            return False

        # Apply overrides to config manager (in-memory)
        self.config_manager.apply_overrides(overrides)

        # Persist to file
        self.config_manager.save_to_file(self.config_file)

        self.result = "ok"
        return True

    def _current_theme(self) -> str | None:
        app = getattr(self.config_manager, "app", None)
        theme = getattr(app, "theme", None)
        return getattr(theme, "value", None)

    def _apply_gui_updates(self, old_theme=None):
        """Apply GUI-level updates that should happen after settings are persisted.

        Currently this changes the ttkbootstrap theme if it was modified. The
        logic is centralized here so it can be called from both Apply and OK
        handlers.
        """
        new_theme = self._current_theme()
        if new_theme and new_theme != old_theme:
            try:
                ttkbootstrap.Style().theme_use(new_theme)
            except Exception:
                # Best-effort; don't crash the settings dialog if theme switch fails
                pass

    def _save(self) -> bool:
        old_theme = self._current_theme()
        try:
            if not self._persist_settings():
                return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}", parent=self.dialog)
            return False
        self._apply_gui_updates(old_theme)
        return True

    def _on_ok(self):
        """Handle OK button click."""
        if self._save():
            self.dialog.destroy()

    def _on_cancel(self):
        """Handle Cancel button click."""
        self.result = "cancel"
        self.dialog.destroy()

    def _on_apply(self):
        """Apply current settings without closing the dialog.

        This applies the widget values to the in-memory configuration and
        applies the theme change live if the GUI theme parameter is present.
        """
        self._save()
