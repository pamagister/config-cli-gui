# Installation


## 🐍 PyPI

### Install the package from PyPI

Download from [PyPI](https://pypi.org/):

```bash
pip install config-cli-gui
```

### Run CLI from command line
```bash
config-cli-gui [OPTIONS] path/to/file
```

### Run GUI from command line
```bash
config-cli-gui-gui
```

## 🔽 Executable

Download the latest executable:

- [⬇️ Download for Windows](https://github.com/pamagister/config-cli-gui/releases/latest/download/installer-win.zip)
- [⬇️ Download for macOS](https://github.com/pamagister/config-cli-gui/releases/latest/download/package-macos.zip)


## 👩🏼‍💻 Run from source

### Clone the repository

```bash
git clone
```

### Navigate to the project directory

```bash
cd config-cli-gui
```

### Install dependencies

```bash
uv venv
uv pip install -e .[dev,docs]
```


### Run with CLI from source

```bash
python -m config_cli_gui.cli [OPTIONS] path/to/file
```


### Run with GUI from source

```bash
python -m config_cli_gui.gui
```

