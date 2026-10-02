from pathlib import Path
from textwrap import dedent

from config_cli_gui.config import ConfigManager


class DocumentationGenerator:
    """Generates documentation and configuration files from ConfigManager."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def generate_config_markdown_doc(
        self,
        output_file: str,
        config_file_path: str | None = "../../config.yaml",
        link_strategy: str = "relative",
    ):
        """Generate Markdown documentation for all configuration parameters.

        Args:
            output_file: Path where the markdown file will be written
            config_file_path: Path to the config.yaml file (for creating links)
                             Can be relative (e.g., "../../config.yaml") or absolute
            link_strategy: How to generate links to config.yaml:
                          - "relative": relative path (default, for documentation)
                          - "file": file:// URI (for file explorer/installed app)
                          - "none": no links (default if config_file_path is None)
        """

        def pad(s, width):
            return s + " " * (width - len(s))

        # Create introduction with link to config file if provided
        markdown_content = dedent("""
            # Configuration Parameters

            These parameters are available to configure the behavior of your application.
            The parameters in the cli category can be accessed via the command line interface.

            """).lstrip()

        # Add config file link if provided
        if config_file_path:
            if link_strategy == "file":
                # Convert to absolute path for file:// URI
                from pathlib import Path as PathlibPath

                abs_path = PathlibPath(config_file_path).resolve()
                link = f"file://{abs_path.as_posix()}"
            else:
                # Use relative path (default)
                link = config_file_path

            markdown_content += dedent(f"""
                ## Configuration File Reference

                The actual configuration is stored in [`config.yaml`]({link}). You can:

                - Edit the configuration file directly using your text editor
                - Use the `--config` command-line option to specify a custom config file
                - Place a `config.yaml` in your application's config
                  directory (typically `~/.config/config-cli-gui/`)

                """).lstrip()

        for category_name, category in self.config_manager._categories.items():
            # Create anchor-friendly category name
            category_anchor = category_name.lower().replace(" ", "-")
            markdown_content += f'## Category "{category_name}" {{#{category_anchor}}}\n\n'

            # Collect all parameters for this category
            rows = []
            header = ["Name", "Type", "Description", "Default", "Choices"]

            for param in category.get_parameters():
                name = param.name
                typ = type(param.value).__name__
                desc = param.help
                value = repr(param.value)
                choices = str(param.choices) if param.choices else "-"

                rows.append((name, typ, desc, value, choices))

            if not rows:
                continue

            # Calculate column widths
            all_rows = [header] + rows
            widths = [max(len(str(col)) for col in column) for column in zip(*all_rows)]

            # Create Markdown table
            table = (
                "| "
                + " | ".join(pad(h, w) for h, w in zip(header, widths))
                + " |\n"
                + "|-"
                + "-|-".join("-" * w for w in widths)
                + "-|\n"
            )
            for row in rows:
                table += "| " + " | ".join(pad(str(col), w) for col, w in zip(row, widths)) + " |\n"

            markdown_content += table + "\n"

        # Write to file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    def generate_default_config_file(self, output_file: str):
        """Generate a default configuration file with all parameters and descriptions."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_manager.save_to_file(output_path.as_posix())

    def generate_cli_markdown_doc(self, output_file: str, app_name: str = "app"):
        """Generate Markdown CLI documentation.

        The generated doc prefers the installed command for end users (for example
        ``gpx-kml-converter --help``), while still including the direct module
        invocation as a development fallback (``python -m gpx_kml_converter``).
        """
        cli_params = self.config_manager.get_cli_parameters()

        if not cli_params:
            return

        base_app_name = (app_name or self.config_manager.get_app_name()).strip() or "app"
        command_name = base_app_name.replace("_", "-")
        module_name = base_app_name.replace("-", "_")

        rows = [
            ("--config", "str", "Path to configuration file", "-", "-"),
            ("-v, --verbose", "bool", "Enable debug logging", "False", "[True, False]"),
            (
                "-q, --quiet",
                "bool",
                "Show warnings and errors only",
                "False",
                "[True, False]",
            ),
        ]
        required_params = []
        optional_params = []

        for param in cli_params:
            cli_arg = (
                f"`{param.name}`" if param.required else (f"`{param.cli_arg or f'--{param.name}'}`")
            )
            typ = type(param.value).__name__
            desc = param.help
            value = (
                "*required*" if param.required or param.value in (None, "") else repr(param.value)
            )
            choices = str(param.choices) if param.choices else "-"

            rows.append((cli_arg, typ, desc, value, choices))
            if param.required:
                required_params.append(param)
            else:
                optional_params.append(param)

        # Generate table
        def pad(s, width):
            return s + " " * (width - len(s))

        header = ["Option", "Type", "Description", "Default", "Choices"]
        widths = [max(len(str(col)) for col in column) for column in zip(*rows, strict=False)]

        table = dedent(
            "| "
            + " | ".join(pad(h, w) for h, w in zip(header, widths, strict=False))
            + " |\n"
            + "|-"
            + "-|-".join("-" * w for w in widths)
            + "-|\n"
        )
        for row in rows:
            table += (
                "| "
                + " | ".join(pad(str(col), w) for col, w in zip(row, widths, strict=False))
                + " |\n"
            )

        required_arg_names = [param.name for param in required_params]
        required_target = (
            " ".join(f"<{name}>" for name in required_arg_names) if required_arg_names else "input"
        )
        usage_command = f"{command_name} [OPTIONS] {required_target}".strip()
        usage_module = f"python -m {module_name} [OPTIONS] {required_target}".strip()

        examples = []
        primary_target = required_arg_names[0] if required_arg_names else "input"

        examples.append(
            dedent(f"""
            ### 1. Basic usage

            ```bash
            {command_name} {primary_target}
            ```
            """)
        )

        examples.append(
            dedent(f"""
            ### 2. With verbose logging

            ```bash
            {command_name} -v {primary_target}
            {command_name} --verbose {primary_target}
            ```
            """)
        )

        examples.append(
            dedent(f"""
            ### 3. With quiet mode

            ```bash
            {command_name} -q {primary_target}
            {command_name} --quiet {primary_target}
            ```
            """)
        )

        for i, param in enumerate(optional_params[:3], 4):
            if param.name in {"verbose", "quiet", "config"}:
                continue
            example_value = param.choices[0] if param.choices else param.value
            examples.append(
                dedent(f"""
                ### {i}. With {param.name} parameter

                ```bash
                {command_name} --{param.name} {example_value} {primary_target}
                ```
                """)
            )

        examples.append(
            dedent(f"""
            ### Developer usage

            ```bash
            python -m {module_name} --help
            python -m {module_name} {primary_target}
            ```
            """)
        )

        markdown = dedent(f"""
# Command Line Interface

Command line options for {base_app_name}

```bash
{usage_command}
```

For development from a source checkout, the equivalent module invocation is:

```bash
{usage_module}
```

## Options

{table}

## Examples

            {"".join(examples)}
            """).strip()

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
