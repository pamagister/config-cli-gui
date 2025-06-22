from pathlib import Path
from textwrap import dedent

from config_cli_gui.config_framework import ConfigManager


class DocumentationGenerator:
    """Generates documentation and configuration files from ConfigManager."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def generate_config_markdown_doc(self, output_file: str):
        """Generate Markdown documentation for all configuration parameters."""

        def pad(s, width):
            return s + " " * (width - len(s))

        markdown_content = dedent("""
            # Configuration Parameters

            These parameters are available to configure the behavior of your application.
            The parameters in the cli category can be accessed via the command line interface.

            """).lstrip()

        for category_name, category in self.config_manager._categories.items():
            markdown_content += f'## Category "{category_name}"\n\n'

            # Collect all parameters for this category
            rows = []
            header = ["Name", "Type", "Description", "Default", "Choices"]

            for param in category.get_parameters():
                name = param.name
                typ = type(param.default).__name__
                desc = param.help
                default = repr(param.default)
                choices = str(param.choices) if param.choices else "-"

                rows.append((name, typ, desc, default, choices))

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

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Configuration File\n")
            f.write("# This file was auto-generated. Modify as needed.\n\n")

            for category_name, category in self.config_manager._categories.items():
                f.write(f"# {category_name.upper()} Configuration\n")
                f.write(f"{category_name}:\n")

                for param in category.get_parameters():
                    f.write(f"  # {param.help}\n")
                    if param.choices:
                        f.write(f"  # Choices: {param.choices}\n")
                    f.write(f"  # Type: {type(param.default).__name__}\n")
                    f.write(f"  {param.name}: {repr(param.default)}\n\n")

                f.write("\n")

    def generate_cli_markdown_doc(self, output_file: str, app_name: str = "app"):
        """Generate Markdown CLI documentation."""
        cli_params = self.config_manager.get_cli_parameters()

        if not cli_params:
            return

        rows = []
        required_params = []
        optional_params = []

        for param in cli_params:
            cli_arg = f"`--{param.name}`" if not param.required else f"`{param.name}`"
            typ = type(param.default).__name__
            desc = param.help
            default = (
                "*required*"
                if param.required or param.default in (None, "")
                else repr(param.default)
            )
            choices = str(param.choices) if param.choices else "-"

            rows.append((cli_arg, typ, desc, default, choices))
            if default == "*required*":
                required_params.append(param)
            else:
                optional_params.append(param)

        # Generate table
        def pad(s, width):
            return s + " " * (width - len(s))

        widths = [max(len(str(col)) for col in column) for column in zip(*rows)]
        header = ["Option", "Type", "Description", "Default", "Choices"]

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

        # Generate examples
        examples = []
        required_arg = required_params[0].name if required_params else "example.input"

        examples.append(
            dedent(
                f"""
            ### 1. Basic usage

            ```bash
            python -m {app_name} {required_arg}
            ```
            """
            )
        )

        # Add more examples with optional parameters
        for i, param in enumerate(optional_params[:3], 2):
            if param.name in ["verbose", "quiet"]:
                continue
            example_value = param.choices[0] if param.choices else param.default
            examples.append(
                dedent(f"""
                ### {i}. With {param.name} parameter

                ```bash
                python -m {app_name} --{param.name} {example_value} {required_arg}
                ```
                """)
            )

        markdown = dedent(
            f"""
            # Command Line Interface

Command line options for {app_name}

```bash
python -m {app_name} [OPTIONS] {required_arg if required_params else ""}
```

## Options

{table}

## Examples

            {"".join(examples)}
            """
        ).strip()

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
