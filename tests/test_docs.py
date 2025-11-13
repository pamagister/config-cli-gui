from unittest.mock import patch

from config_cli_gui.config import (
    Color,
    ConfigCategory,
    ConfigManager,
    ConfigParameter,
)
from config_cli_gui.docs import DocumentationGenerator

# ---------------------------------------
# Helper category used in tests
# ---------------------------------------


class DocTestCategory(ConfigCategory):
    param1: ConfigParameter = ConfigParameter(
        name="param1", value=10, help="First parameter", choices=[1, 5, 10]
    )
    param2: ConfigParameter = ConfigParameter(
        name="param2", value=Color(10, 20, 30), help="Color parameter"
    )
    cli_only: ConfigParameter = ConfigParameter(
        name="cli_only", value="x", help="CLI parameter", is_cli=True
    )

    def get_category_name(self) -> str:
        return "doc_test"


# ---------------------------------------
# Test generate_config_markdown_doc
# ---------------------------------------


def test_generate_config_markdown_doc(tmp_path):
    cat = DocTestCategory()
    mgr = ConfigManager((cat,))
    docgen = DocumentationGenerator(mgr)

    out = tmp_path / "config.md"
    docgen.generate_config_markdown_doc(out.as_posix())

    assert out.exists(), "File should be created"

    text = out.read_text()

    # Verify headers and content exist
    assert "# Configuration Parameters" in text
    assert '## Category "doc_test"' in text

    # Verify table structure
    assert "| Name" in text
    assert "| param1" in text
    assert "Color" in text
    assert "First parameter" in text


# ---------------------------------------
# Test generate_default_config_file
# ---------------------------------------


def test_generate_default_config_file(tmp_path):
    cat = DocTestCategory()
    mgr = ConfigManager((cat,))
    docgen = DocumentationGenerator(mgr)

    out = tmp_path / "default.yaml"

    with patch.object(mgr, "save_to_file") as mock_save:
        docgen.generate_default_config_file(out.as_posix())
        mock_save.assert_called_once_with(out.as_posix())


# ---------------------------------------
# Test generate_cli_markdown_doc – with CLI params
# ---------------------------------------


def test_generate_cli_markdown_doc(tmp_path):
    cat = DocTestCategory()
    # Mark one as required CLI param
    cat.cli_only.required = True
    cat.cli_only.help = "CLI only parameter"

    mgr = ConfigManager((cat,))
    docgen = DocumentationGenerator(mgr)

    out = tmp_path / "cli_doc.md"
    docgen.generate_cli_markdown_doc(out.as_posix(), app_name="myapp")

    assert out.exists()
    text = out.read_text()

    # Verify main headers
    assert "# Command Line Interface" in text
    assert "Command line options for myapp" in text

    # Verify table includes CLI param
    assert "| `cli_only`" in text  # required → printed as plain name without '--'
    assert "CLI only parameter" in text

    # Verify example usage includes cli_only
    assert "python -m myapp cli_only" in text


# ---------------------------------------
# Test generate_cli_markdown_doc – no CLI params (should write nothing)
# ---------------------------------------


def test_generate_cli_markdown_doc_no_params(tmp_path):
    # Remove CLI flags
    class NoCLI(ConfigCategory):
        p1: ConfigParameter = ConfigParameter(name="p1", value=1, help="normal")

        def get_category_name(self):
            return "nocli"

    cat = NoCLI()
    mgr = ConfigManager((cat,))
    docgen = DocumentationGenerator(mgr)

    out = tmp_path / "no_cli.md"

    # Should NOT write file because there are no CLI params
    docgen.generate_cli_markdown_doc(out.as_posix())

    assert not out.exists(), "File should not be created if no CLI parameters exist"


# ---------------------------------------
# Test markdown formatting correctness (column widths)
# ---------------------------------------


def test_markdown_column_alignment(tmp_path):
    cat = DocTestCategory()
    mgr = ConfigManager((cat,))
    docgen = DocumentationGenerator(mgr)

    out = tmp_path / "config.md"
    docgen.generate_config_markdown_doc(out.as_posix())

    text = out.read_text()

    # Check table header alignment with '-' filler
    assert "| Name" in text
    assert "|-" in text  # markdown alignment separator

    # Ensure each row starts with '|'
    rows = [line for line in text.splitlines() if line.startswith("|")]
    assert len(rows) > 2


# ---------------------------------------
# Test that directory creation is performed
# ---------------------------------------
def test_directory_created_for_docs(tmp_path):
    cat = DocTestCategory()
    mgr = ConfigManager((cat,))
    docgen = DocumentationGenerator(mgr)

    nested_dir = tmp_path / "deep" / "deeper"
    out = nested_dir / "config.md"

    docgen.generate_config_markdown_doc(out.as_posix())

    assert out.exists()
    assert nested_dir.exists()


# ---------------------------------------
# Test that generate_config_markdown_doc uses repr() for defaults
# ---------------------------------------


def test_markdown_uses_repr(tmp_path):
    cat = DocTestCategory()
    mgr = ConfigManager((cat,))
    docgen = DocumentationGenerator(mgr)

    out = tmp_path / "config.md"
    docgen.generate_config_markdown_doc(out.as_posix())

    text = out.read_text()

    # repr(Color) is like "Color(10, 20, 30)"
    assert "Color(10, 20, 30)" in text


# ---------------------------------------
# Validate choices column printed correctly
# ---------------------------------------


def test_choices_rendered_in_markdown(tmp_path):
    cat = DocTestCategory()
    mgr = ConfigManager((cat,))
    docgen = DocumentationGenerator(mgr)

    out = tmp_path / "config.md"
    docgen.generate_config_markdown_doc(out.as_posix())

    text = out.read_text()

    assert "[1, 5, 10]" in text  # Choices rendered


# ---------------------------------------
# Test multiple optional CLI example customization
# ---------------------------------------


def test_cli_examples_include_optional_params(tmp_path):
    cat = DocTestCategory()
    # Mark another as CLI parameter
    cat.param1.is_cli = True

    mgr = ConfigManager((cat,))
    docgen = DocumentationGenerator(mgr)

    out = tmp_path / "cli_doc.md"
    docgen.generate_cli_markdown_doc(out.as_posix(), app_name="tool")

    text = out.read_text()

    # Should include example using param1
    assert "--param1" in text or "`--param1`" in text
