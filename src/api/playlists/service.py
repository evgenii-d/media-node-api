from pathlib import Path
from fastapi import HTTPException

from src.constants import AppDir


def create_playlist(name: str, dir_path: Path, files: list[str]) -> None:
    """Create M3U playlist.

    Args:
        name (str): Playlist name.
        dir_path (Path): Destination directory.
        files (list[str]): List of paths to files.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    with open(dir_path/f"{name}.m3u", "w", encoding="utf-8") as playlist:
        playlist.write("#EXTM3U\n")
        for file_path in files:
            playlist.write(f"{file_path}\n")


def get_playlist_content(playlist_path: Path) -> list[str]:
    """Retrieve the content of a playlist file.

    Args:
        playlist_path (Path): Path to the playlist file.

    Returns:
        list[str]: List of filenames extracted from the playlist.
    """
    content = []
    if not playlist_path.exists():
        return content

    with open(playlist_path, "r", encoding="utf-8") as playlist:
        for line in playlist:
            content.append(Path(line.strip()).name)
    return content[1:]


def get_playlist_path(playlist_name: str) -> Path:
    """Retrieve path to playlist by name.

    Args:
        playlist_name (str): Name of playlist (without extension).

    Raises:
        HTTPException: Raises 404 if playlist does not exist.

    Returns:
        Path: Path to playlist file.
    """
    test_path = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if test_path.exists():
        return test_path
    raise HTTPException(404, "Playlist not found")
