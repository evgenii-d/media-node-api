from pathlib import Path
from fastapi import APIRouter, Body, HTTPException

from src.constants import AppDir
from src.core.filesys import get_dir_files, check_dir_files
from src.api.playlists.config import config_manager
from src.api.playlists.service import playlist_content, create_playlist
from src.api.playlists.schemas import PlaylistSchema, ConfigSchema

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get("/", responses={
    200: {"description": "Playlists retrieved successfully"}
}, status_code=200)
def available_playlists() -> list[str]:
    files = get_dir_files(AppDir.PLAYLISTS.value, suffix=False)
    files.sort()
    return files


@router.put("/", responses={
    200: {"description": "Playlist updated successfully"},
    201: {"description": "Playlist created successfully"},
    404: {"description": "Playlist files not found"}
}, status_code=201)
def update_playlist(playlist: PlaylistSchema) -> PlaylistSchema:
    files = check_dir_files(playlist.files, AppDir.MEDIA.value)
    if len(files.available) == 0:
        raise HTTPException(404, "Playlist files not found")

    is_exists = (AppDir.PLAYLISTS.value/playlist.name).exists()
    paths = [AppDir.MEDIA.value/file for file in files.available]
    create_playlist(playlist.name, AppDir.PLAYLISTS.value, paths)
    new_playlist = PlaylistSchema(name=playlist.name, files=files.available)
    if is_exists:
        return new_playlist, 200
    return new_playlist, 201


@router.delete("/{playlist_name}", responses={
    204: {"description": "Playlist deleted successfully"},
    404: {"description": "Playlist not found"}
}, status_code=204)
def delete_playlists(playlist_name: str) -> None:
    file = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if not file.exists():
        raise HTTPException(404, "Playlist not found")
    file.unlink()


@router.get("/default", responses={
    200: {"description": "Default playlist retrieved successfully"}
}, status_code=200)
async def default_playlist() -> str:
    config = ConfigSchema.model_validate(config_manager.load_section())
    return Path(config.defaultPlaylist).stem


@router.put("/default", responses={
    204: {"description": "Default playlist changed"},
    404: {"description": "Playlist not found"}
}, status_code=204)
def set_default_playlist(playlist: str = Body()) -> None:
    playlists = get_dir_files(AppDir.PLAYLISTS.value, suffix=False)
    if playlist != "" and playlist not in playlists:
        raise HTTPException(404, "Playlist not found")

    if playlist == "":
        # Default playlist unset
        data = ConfigSchema(defaultPlaylist="")
        config_manager.save_section(data.model_dump())
        return

    # Default playlist set to {playlist}
    playlist_path = (AppDir.PLAYLISTS.value/f"{playlist}.m3u").as_posix()
    data = ConfigSchema(defaultPlaylist=playlist_path)
    config_manager.save_section(data.model_dump())


@router.get("/content/{playlist_name}", responses={
    200: {"description": "Playlist content retrieved"},
    404: {"description": "Playlist not found"}
}, status_code=200)
def get_playlist_content(playlist_name: str) -> list[str]:
    playlist_path = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if playlist_path.exists():
        return playlist_content(playlist_path)
    raise HTTPException(404, "Playlist not found")
