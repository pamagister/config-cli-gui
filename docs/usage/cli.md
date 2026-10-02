# Command Line Interface

Command line options for app

```bash
app [OPTIONS] <input>
```

For development from a source checkout, the equivalent module invocation is:

```bash
python -m app [OPTIONS] <input>
```

## Options

| Option                | Type | Description                                       | Default    | Choices       |
|-----------------------|------|---------------------------------------------------|------------|---------------|
| --config              | str  | Path to configuration file                        | -          | -             |
| -v, --verbose         | bool | Enable debug logging                              | False      | [True, False] |
| -q, --quiet           | bool | Show warnings and errors only                     | False      | [True, False] |
| `input`               | str  | Path to input (file or folder)                    | *required* | -             |
| `--output`            | str  | Path to output destination                        | *required* | -             |
| `--min_dist`          | int  | Maximum distance between two waypoints            | 20         | -             |
| `--extract_waypoints` | bool | Extract starting points of each track as waypoint | True       | [True, False] |
| `--elevation`         | bool | Include elevation data in waypoints               | False      | [True, False] |


## Examples


### 1. Basic usage

```bash
app input
```

### 2. With verbose logging

```bash
app -v input
app --verbose input
```

### 3. With quiet mode

```bash
app -q input
app --quiet input
```

### 4. With output parameter

```bash
app --output  input
```

### 5. With min_dist parameter

```bash
app --min_dist 20 input
```

### 6. With extract_waypoints parameter

```bash
app --extract_waypoints True input
```

### Developer usage

```bash
python -m app --help
python -m app input
```