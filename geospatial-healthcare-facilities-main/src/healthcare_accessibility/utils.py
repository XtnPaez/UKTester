from pathlib import Path
from datetime import datetime


def setup_sub_dir(data_dir: Path, sub_dir_name: str) -> Path:
    """
    Check if subdirectory of given name exists and create if not, return path.

    Parameters
    ----------
    data_dir : pathlib.Path
        Path to current data directory.
    sub_dir_name : str
        Name of desired subdirectory within data directory.

    Returns
    -------
    sub_dir : pathlib.Path
        Path to the newly created, or pre-existing, subdirectory of given name.
    """
    sub_dir = data_dir.joinpath(sub_dir_name)
    if not sub_dir.is_dir():
        sub_dir.mkdir(parents=True, exist_ok=True)
    return sub_dir


def setup_output_directory(config):
    """
    Create and return output directories for a configured country run.

    Parameters
    ----------
    config : dict
        Configuration dictionary containing at least `outputs_dir` and `country`.

    Returns
    -------
    tuple[pathlib.Path, pathlib.Path]
        A tuple of `(output_dir, maps_dir)` where:
        - `output_dir` is `outputs_dir/<country>`
        - `maps_dir` is the `maps` subdirectory within `output_dir`
    """
    output_dir = config.get("outputs_dir")
    country = config.get("country")
    output_dir = Path(output_dir).joinpath(country)
    output_dir.mkdir(parents=True, exist_ok=True)
    maps_dirs = setup_sub_dir(output_dir, "maps")
    return output_dir, maps_dirs


def continue_confirmation(processed_file_path):
    """
    Check if processed file exists at desired output location, and if so prompt
     user to confirm whether to overwrite or not. If file doesn't exist, it
     will continue by default.

    Parameters
    ----------
    processed_file_path : pathlib.Path or str
        Desired path for the processed data output.

    Returns
    -------
    bool
        Return True if processed file does not already exist, or the user has confirmed
        they wish to overwrite existing file. Return False if user does not wish
        to overwrite existing file.
    """
    generate_output = False
    if Path(processed_file_path).is_file():
        response = input(
            f"A file already exists at {processed_file_path}. "
            "Continuing will overwrite this. Do you want to continue? [y/n] "
        )
        if response.lower() == "y":
            generate_output = True
    else:
        generate_output = True
    return generate_output
