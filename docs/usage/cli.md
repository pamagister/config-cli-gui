# Command Line Interface

Command line options for your-app-name

```bash
your-app-name [OPTIONS] input
```

For development from a source checkout, the equivalent module invocation is:

```bash
python -m your_app_name [OPTIONS] input
```

## Options

| Option                 | Type | Description                   | Default | Choices       |
|------------------------|------|-------------------------------|---------|---------------|
| --config               | str  | Path to configuration file    | -       | -             |
| -v, --verbose          | bool | Enable debug logging          | False   | [True, False] |
| -q, --quiet            | bool | Show warnings and errors only | False   | [True, False] |
| `--your_cli_parameter` | int  | Example integer               | 42      | -             |


## Examples


### 1. Basic usage

```bash
your-app-name input
```

### 2. With verbose logging

```bash
your-app-name -v input
your-app-name --verbose input
```

### 3. With quiet mode

```bash
your-app-name -q input
your-app-name --quiet input
```

### 4. With your_cli_parameter parameter

```bash
your-app-name --your_cli_parameter 42 input
```

### Developer usage

```bash
python -m your_app_name --help
python -m your_app_name input
```

    
    # More parameter
    
    For your specific projects that inherit from the library, 
    you can add more parameters to the CLI and config file 
    by creating your own ConfigManager subclass 
    and adding more ConfigParameter instances. 
    The documentation generator will automatically include them 
    in the generated documentation.
    