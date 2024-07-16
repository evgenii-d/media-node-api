from pathlib import Path
from fastapi import APIRouter, Body, HTTPException, Response

from src.constants import AppDir
from src.core.filesys import (get_dir_files, del_files_from_dir,
                              check_dir_files)
from src.api.playlists.config import config_manager
from src.api.playlists.service import playlist_content, create_playlist
from src.api.playlists.schemas import (PlaylistSchema, ConfigSchema,
                                       DeletedPlaylistsSchema)

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get("/", responses={
    200: {"description": "Playlists retrieved successfully"},
    204: {"description": "No playlists available"}
})
def available_playlists() -> list[str]:
    files = get_dir_files(AppDir.PLAYLISTS.value, suffix=False)
    files.sort()
    return files if len(files) > 0 else Response(status_code=204)


@router.post("/", responses={
    200: {"description": "Playlist created successfully"},
    404: {"description": "Playlist files not found"}
})
def new_playlist(playlist: PlaylistSchema) -> PlaylistSchema:
    files = check_dir_files(playlist.files, AppDir.MEDIA.value)
    if len(files.available) == 0:
        raise HTTPException(404, "Playlist files not found")

    paths = [AppDir.MEDIA.value/file for file in files.available]
    create_playlist(playlist.name, AppDir.PLAYLISTS.value, paths)
    return PlaylistSchema(name=playlist.name, files=files.available)


@router.delete("/")
def delete_playlists(files: list[str]) -> DeletedPlaylistsSchema:
    files = [f"{file}.m3u" for file in files]
    dir_files = check_dir_files(files, AppDir.PLAYLISTS.value)
    del_files_from_dir(dir_files.available, AppDir.PLAYLISTS.value)
    return DeletedPlaylistsSchema(
        deleted=[Path(file).stem for file in dir_files.available],
        missing=[Path(file).stem for file in dir_files.missing]
    )


@router.get("/default", responses={
    200: {"description": "Default playlist retrieved successfully"},
    204: {"description": "Default playlist not set"},
})
async def default_playlist() -> str:
    config = ConfigSchema.model_validate(config_manager.load_section())
    if config.defaultPlaylist:
        return Path(config.defaultPlaylist).stem
    return Response(status_code=204)


@router.post("/default", responses={
    200: {"description": "Default playlist changed"},
    404: {"description": "Playlist not found"}
})
def set_default_playlist(playlist: str = Body()) -> Response:
    playlists = get_dir_files(AppDir.PLAYLISTS.value, suffix=False)
    if playlist != "" and playlist not in playlists:
        raise HTTPException(404, "Playlist not found")

    if playlist == "":
        # Default playlist unset
        data = ConfigSchema(defaultPlaylist="")
        config_manager.save_section(data.model_dump())
        return Response(status_code=200)

    # Default playlist set to {playlist}
    playlist_path = (AppDir.PLAYLISTS.value/f"{playlist}.m3u").as_posix()
    data = ConfigSchema(defaultPlaylist=playlist_path)
    config_manager.save_section(data.model_dump())
    return Response(status_code=200)


@router.get("/content/{playlist_name}", responses={
    200: {"description": "Playlist content retrieved"},
    404: {"description": "Playlist not found"}
})
def get_playlist_content(playlist_name: str) -> list[str]:
    playlist_path = AppDir.PLAYLISTS.value/f"{playlist_name}.m3u"
    if playlist_path.exists():
        return playlist_content(playlist_path)
    raise HTTPException(404, "Playlist not found")
