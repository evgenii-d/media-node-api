from pathlib import Path


def create_playlist(name: str, dir_path: Path, files: list[str]) -> None:
    """Create M3U playlist.

    Args:
        name (str): playlist name.
        files (list[str]): list of paths to files.
        dir_path (Path): destination directory.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    with open(dir_path/f"{name}.m3u", "w", encoding="utf-8") as playlist:
        playlist.write("#EXTM3U\n")
        for file_path in files:
            playlist.write(f"{file_path}\n")


def playlist_content(playlist_path: Path) -> list[str]:
    """Get playlist content."""
    content = []
    if not playlist_path.exists():
        return content

    with open(playlist_path, "r", encoding="utf-8") as playlist:
        for line in playlist:
            content.append(Path(line.strip()).name)
    return content[1:]
