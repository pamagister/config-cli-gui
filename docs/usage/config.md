# Configuration Parameters

These parameters are available to configure the behavior of your application.
Parameters marked as CLI parameters can also be set via the command line interface.

## Configuration File Reference

The actual configuration is stored in [`config.yaml`](../../config.yaml). You can:

- Edit the configuration file directly using your text editor
- Use the `--config` command-line option to specify a custom config file

## Category "app" {#app}

| Name                   | Type | Description                                 | Default    | Choices                                                                                                                                               |
|------------------------|------|---------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| date_format            | str  | Date format to use                          | '%Y-%m-%d' | -                                                                                                                                                     |
| log_level              | str  | Logging level for the application           | 'INFO'     | ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']                                                                                                     |
| log_file_max_size      | int  | Maximum log file size in MB before rotation | 2          | -                                                                                                                                                     |
| enable_file_logging    | bool | Enable logging to file                      | True       | [True, False]                                                                                                                                         |
| enable_console_logging | bool | Enable logging to console                   | True       | [True, False]                                                                                                                                         |
| theme                  | str  | GUI theme setting supported by ttkbootstrap | 'darkly'   | ['cosmo', 'flatly', 'litera', 'minty', 'lumen', 'sandstone', 'yeti', 'pulse', 'united', 'darkly', 'superhero', 'solar', 'cyborg', 'vapor', 'simplex'] |

## Category "Your_parameter_category" {#your_parameter_category}

| Name               | Type | Description     | Default | Choices |
|--------------------|------|-----------------|---------|---------|
| your_cli_parameter | int  | Example integer | 42      | -       |

