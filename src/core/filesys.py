"""File and Directory Management Utilities."""
import re
from pathlib import Path
from dataclasses import dataclass
import aiofiles
from fastapi import UploadFile


@dataclass
class CheckedDir:
    available: list[str]
    missing: list[str]


def secure_filename(filename: str, max_length: int = 255) -> str:
    """Replace invalid character(s) for a filename.

    secure_filename("новый файл.txt") -> "новый_файл.txt"
    secure_filename("../../../etc/passwd") -> 'etc_passwd'
    secure_filename('i contain cool \xfcml\xe4uts.txt') 
        -> 'i_contain_cool_ümläuts.txt'

    Args:
        filename (str): the filename to secure.
        max_length (int, optional): 
            character filename limit. Defaults to 255.

    Returns:
        str: sanitized filename.
    """

    sanitized_filename = re.sub(r'[\/:*?"<>| ]', "_", filename).strip(" ._")

    if len(sanitized_filename) > max_length:
        path = Path(sanitized_filename)
        short_name = path.stem[:max_length - len(path.suffix)]
        return short_name + path.suffix

    return sanitized_filename


def get_dir_size(dir_path: Path, units: int = 0) -> float:
    """Return directory size (in bytes by default).

    Args:
        dir_path (str | Path): path to the directory.
        units (int, optional): 
            0 - Byte, 1 - KiB, 2 - MiB, 
            3 - GiB, 4 - TiB. Defaults to 0.

    Returns:
        int | float: total size of the directory.
    """
    total_size = 0

    if not dir_path.exists():
        return total_size

    # scan given directory and all subdirectories, recursively
    for item in dir_path.glob("**/*"):
        if item.is_file():
            total_size += item.stat().st_size

    if 0 < units < 5:
        total_size = total_size / 1024 ** units
    return total_size


def get_dir_files(dir_path: Path, recursive: bool = False,
                  extensions: list = None, suffix: bool = True) -> list[str]:
    """Return a list of filenames for given directory.

    Args:
        dir_path (Path): destination directory.
        recursive (bool, optional): 
            scan subdirectories. Defaults to False.
        extensions (list, optional): 
            filter files extensions. Defaults to None.
        suffix (bool, optional): 
            return filename with extension. Defaults to True.

    Returns:
        list: list of filenames.
    """
    files: list[Path] = []

    if not dir_path.exists():
        return files
    for item in dir_path.glob('**/*' if recursive else '*'):
        if item.is_file() and (extensions is None or
                               item.suffix in extensions):
            files.append(item)
    if suffix:
        return [file.name for file in files]

    return [file.stem for file in files]


def del_files_from_dir(files: list[str], dir_path: Path) -> None:
    for file in files:
        for item in dir_path.iterdir():
            if item.is_file() and item.exists() and item.name == file:
                item.unlink()


def check_dir_files(files: list[str], dir_path: Path) -> CheckedDir:
    result = CheckedDir(available=[], missing=[])
    for file in files:
        if (dir_path/file).exists():
            result.available.append(file)
        else:
            result.missing.append(file)
    return result


async def aio_save_files_to_dir(files: list[UploadFile], dir_path: Path,
                                chunk_size: int = 25 * 1024 ** 2) -> None:
    """Async file saving.

    Args:
        files (list[UploadFile]): list of files.

        dir_path (Path): destination directory.

        chunk_size (int, optional): 
            chunk size. Defaults to 25 megabytes.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    for file in files:
        path = Path(dir_path, secure_filename(file.filename))
        async with aiofiles.open(path, "wb") as f:
            while chunk := await file.read(chunk_size):
                await f.write(chunk)
