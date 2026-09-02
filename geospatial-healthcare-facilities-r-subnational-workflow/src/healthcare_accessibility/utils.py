from pathlib import Path


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
