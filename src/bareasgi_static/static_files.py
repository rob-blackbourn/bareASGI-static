import os
import stat
from typing import Optional
from aiofiles.os import stat as aio_stat
from bareasgi import (
    Scope,
    Info,
    RouteMatches,
    Content,
    HttpResponse,
    text_writer
)
from bareasgi_static.file_streaming import file_response


class StaticFiles:

    def __init__(self, directory: str, check_dir: bool = True, index_filename: Optional[str] = None) -> None:
        if check_dir and not os.path.isdir(directory):
            raise RuntimeError(f"Directory '{directory}' does not exist")
        self.directory = directory
        self.config_checked = False
        self.index_filename = index_filename


    async def __call__(self, scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:
        if scope["method"] not in ("GET", "HEAD"):
            return 405, [(b'content-type', b'text/plain')], text_writer("Method Not Allowed")

        path: str = scope["path"]
        if path.endswith('/') and self.index_filename:
            path += self.index_filename

        relative_path = os.path.normpath(os.path.join(*path.split("/")))
        if relative_path.startswith(".."):
            return 404, [(b'content-type', b'text/plain')], text_writer("Not Found")

        rooted_path = os.path.join(self.directory, relative_path)

        if self.config_checked:
            check_directory = None
        else:
            check_directory = self.directory
            self.config_checked = True

        if check_directory is not None:
            try:
                stat_result = await aio_stat(check_directory)
            except FileNotFoundError:
                raise RuntimeError(f"directory '{check_directory}' does not exist.")
            if not (stat.S_ISDIR(stat_result.st_mode) or stat.S_ISLNK(stat_result.st_mode)):
                raise RuntimeError(f"path '{check_directory}' is not a directory.")

        try:
            stat_result = await aio_stat(rooted_path)
        except FileNotFoundError:
            return 404, [(b'content-type', b'text/plain')], text_writer("Not Found")
        else:
            mode = stat_result.st_mode
            if not stat.S_ISREG(mode):
                return 404, [(b'content-type', b'text/plain')], text_writer("Not Found")
            else:
                return await file_response(scope, 200, rooted_path, check_modified=True)
