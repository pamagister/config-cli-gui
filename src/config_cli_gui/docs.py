from collections.abc import Sequence
from pathlib import Path
from textwrap import dedent

from config_cli_gui.config import ConfigManager


def _markdown_table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    """Render an aligned Markdown table; ``|`` inside cells is escaped."""
    cells = [[str(c).replace("|", "\\|") for c in row] for row in [header, *rows]]
    widths = [max(len(row[i]) for row in cells) for i in range(len(header))]

    def fmt(row: list[str]) -> str:
        return "| " + " | ".join(c.ljust(w) for c, w in zip(row, widths)) + " |\n"

    separator = "|-" + "-|-".join("-" * w for w in widths) + "-|\n"
    return fmt(cells[0]) + separator + "".join(fmt(row) for row in cells[1:])


def _write(output_file: str, content: str) -> None:
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
        markdown_content = dedent("""
            # Configuration Parameters

            These parameters are available to configure the behavior of your application.
            Parameters marked as CLI parameters can also be set via the command line interface.

            """).lstrip()

        if config_file_path and link_strategy != "none":
            if link_strategy == "file":
                link = f"file://{Path(config_file_path).resolve().as_posix()}"
            else:
                link = config_file_path

            markdown_content += dedent(f"""
                ## Configuration File Reference

                The actual configuration is stored in [`config.yaml`]({link}). You can:

                - Edit the configuration file directly using your text editor
                - Use the `--config` command-line option to specify a custom config file

                """).lstrip()

        header = ["Name", "Type", "Description", "Default", "Choices"]
        for category_name, category in self.config_manager.iter_categories():
            rows = [
                (
                    param.name,
                    param.type_name,
                    param.help,
                    repr(param.value),
                    str(param.choices) if param.choices else "-",
                )
                for param in category.get_parameters()
            ]
            if not rows:
                continue

            category_anchor = category_name.lower().replace(" ", "-")
            markdown_content += f'## Category "{category_name}" {{#{category_anchor}}}\n\n'
            markdown_content += _markdown_table(header, rows) + "\n"

        _write(output_file, markdown_content)

    def generate_default_config_file(self, output_file: str):
        """Generate a default configuration file with all parameters and descriptions."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_manager.save_to_file(output_path.as_posix())

    def generate_cli_markdown_doc(self, output_file: str, app_name: str | None = None):
        """Generate Markdown CLI documentation.

        The generated doc prefers the installed command for end users (for example
        ``gpx-kml-converter --help``), while still including the direct module
        invocation as a development fallback (``python -m gpx_kml_converter``).

        Args:
            output_file: Path where the markdown file will be written
            app_name: Command name; defaults to ``config_manager.get_app_name()``
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
            ("-q, --quiet", "bool", "Show warnings and errors only", "False", "[True, False]"),
        ]
        required_params = []
        optional_params = []

        for param in cli_params:
            if param.required:
                cli_arg = f"`{param.name}`"
                default = "*required*"
                required_params.append(param)
            else:
                cli_arg = f"`{param.cli_arg or f'--{param.name}'}`"
                default = "-" if param.value in (None, "") else repr(param.value)
                optional_params.append(param)
            choices = str(param.choices) if param.choices else "-"
            rows.append((cli_arg, param.type_name, param.help, default, choices))

        table = _markdown_table(["Option", "Type", "Description", "Default", "Choices"], rows)

        required_arg_names = [param.name for param in required_params]
        required_target = (
            " ".join(f"<{name}>" for name in required_arg_names) if required_arg_names else "input"
        )
        usage_command = f"{command_name} [OPTIONS] {required_target}".strip()
        usage_module = f"python -m {module_name} [OPTIONS] {required_target}".strip()

        primary_target = required_arg_names[0] if required_arg_names else "input"
        examples = [
            dedent(f"""
            ### 1. Basic usage

            ```bash
            {command_name} {primary_target}
            ```
            """),
            dedent(f"""
            ### 2. With verbose logging

            ```bash
            {command_name} -v {primary_target}
            {command_name} --verbose {primary_target}
            ```
            """),
            dedent(f"""
            ### 3. With quiet mode

            ```bash
            {command_name} -q {primary_target}
            {command_name} --quiet {primary_target}
            ```
            """),
        ]

        example_params = [
            p for p in optional_params if p.name not in {"verbose", "quiet", "config"}
        ]
        for i, param in enumerate(example_params[:3], len(examples) + 1):
            example_value = param.choices[0] if param.choices else param.value
            if example_value in (None, ""):
                example_value = f"<{param.name}>"
            examples.append(
                dedent(f"""
                ### {i}. With {param.name} parameter

                ```bash
                {command_name} {param.cli_arg or f"--{param.name}"} {example_value} {primary_target}
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

        _write(output_file, markdown + "\n")
