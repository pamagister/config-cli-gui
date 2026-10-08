from pathlib import Path

from config_cli_gui.docs import DocumentationGenerator

from config_cli_gui.config import ConfigManager, ConfigCategory, ConfigParameter

"""function to generate config file and documentation."""

class MiscConfig(ConfigCategory):
    def get_category_name(self) -> str:
        return "Your_parameter_category"

    your_cli_parameter: ConfigParameter = ConfigParameter(
        name="your_cli_parameter",
        value=42,
        help="Example integer",
        is_cli=True,
    )


class ConfigParameterManager(ConfigManager):  # Inherit from ConfigManager
    """Main configuration manager that handles all parameter categories."""

    misc: MiscConfig

    def __init__(self, config_file: str | None = None, **kwargs):
        """Initialize the configuration manager with all parameter categories."""
        categories = (MiscConfig(),)
        super().__init__(categories, config_file, **kwargs)

def main():
    default_config: str = "config.yaml"
    default_cli_doc: str = "docs/usage/cli.md"
    default_config_doc: str = "docs/usage/config.md"

    config_manager = ConfigParameterManager()

    doc_gen = DocumentationGenerator(config_manager)
    doc_gen.generate_default_config_file(output_file=default_config)
    print(f"Generated: {default_config}")

    doc_gen.generate_config_markdown_doc(output_file=default_config_doc)
    print(f"Generated: {default_config_doc}")

    doc_gen.generate_cli_markdown_doc(output_file=default_cli_doc, app_name="your-app-name")
    print(f"Generated: {default_cli_doc}")

    additional_cli_content = """
    
    # More parameter
    
    For your specific projects that inherit from the library, 
    you can add more parameters to the CLI and config file 
    by creating your own ConfigManager subclass 
    and adding more ConfigParameter instances. 
    The documentation generator will automatically include them 
    in the generated documentation.
    """

    with Path(default_cli_doc).open("a", encoding="utf-8") as cli_doc:
        cli_doc.write(additional_cli_content)

if __name__ == "__main__":
    main()