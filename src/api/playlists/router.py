from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.constants import AppDir
from src.core.filesys import get_dir_files, check_dir_files
from src.api.playlists.service import playlist_content, create_playlist
from src.api.playlists.schemas import PlaylistSchema

router = APIRouter(prefix="/playlists", tags=["playlists"])


def get_playlist_path(playlist_name: str) -> Path:
    playlist_path = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if playlist_path.exists():
        return playlist_path
    raise HTTPException(404, "Playlist not found")


@router.get("/", responses={
    200: {"description": "Playlists retrieved successfully"}
}, status_code=200)
def available_playlists() -> list[str]:
    files = get_dir_files(AppDir.PLAYLISTS.value, suffix=False)
    files.sort()
    return files


@router.post("/", responses={
    200: {"description": "Playlist updated successfully",
          "model": PlaylistSchema},
    201: {"description": "Playlist created successfully",
          "model": PlaylistSchema},
    404: {"description": "Playlist files not found"}
}, status_code=201)
def create_or_replace_playlist(playlist: PlaylistSchema) -> JSONResponse:
    files = check_dir_files(playlist.files, AppDir.MEDIA.value)
    if len(files.available) == 0:
        raise HTTPException(404, "Playlist files not found")

    is_exists = (AppDir.PLAYLISTS.value/playlist.name).exists()
    paths = [AppDir.MEDIA.value/file for file in files.available]
    create_playlist(playlist.name, AppDir.PLAYLISTS.value, paths)

    new_playlist = PlaylistSchema(name=playlist.name, files=files.available)
    return JSONResponse(new_playlist.model_dump(), 200 if is_exists else 201)


@router.delete("/{playlist_name}", responses={
    204: {"description": "Playlist deleted successfully"},
    404: {"description": "Playlist not found"}
}, status_code=204)
def delete_playlists(playlist_name: str) -> None:
    get_playlist_path(playlist_name).unlink()


@router.get("/content/{playlist_name}", responses={
    200: {"description": "Playlist content retrieved"},
    404: {"description": "Playlist not found"}
}, status_code=200)
def get_playlist_content(playlist_name: str) -> list[str]:
    return playlist_content(get_playlist_path(playlist_name))
