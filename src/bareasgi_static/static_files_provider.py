import os
import stat
from typing import Optional
from aiofiles.os import stat as aio_stat
from bareasgi import (
    Application,
    Scope,
    Info,
    RouteMatches,
    Content,
    HttpResponse,
    text_writer
)
from bareasgi_static.file_streaming import file_response


class StaticFilesProvider:

    def __init__(
            self,
            source_folder: str,
            *,
            path_variable: Optional[str] = None,
            check_source_folder: bool = True,
            index_filename: Optional[str] = None
    ) -> None:
        """
        A static file provider.

        :param app: The bareASGI application.
        :param source_folder: Where to find the files to serve.
        :param mount_point: Where the files should appear on the url.
        :param check_source_folder: If True check the source folder exists.
        :param index_filename: An optional index file name.
        """
        if check_source_folder and not os.path.isdir(source_folder):
            raise RuntimeError(f"Directory '{source_folder}' does not exist")
        self.source_folder = source_folder
        self.path_variable = path_variable
        self.config_checked = False
        self.index_filename = index_filename

    async def __call__(self, scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:
        if scope["method"] not in ("GET", "HEAD"):
            return 405, [(b'content-type', b'text/plain')], text_writer("Method Not Allowed")

        # Get the path from the scope or the route match.
        path: str = '/' + matches.get(self.path_variable, '') if self.path_variable else scope["path"]
        if (path == '' or path.endswith('/')) and self.index_filename:
            path += self.index_filename

        relative_path = os.path.normpath(os.path.join(*path.split("/")))
        if relative_path.startswith(".."):
            return 404, [(b'content-type', b'text/plain')], text_writer("Not Found")

        rooted_path = os.path.join(self.source_folder, relative_path)

        if self.config_checked:
            check_directory = None
        else:
            check_directory = self.source_folder
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


def add_static_file_provider(
        app: Application,
        source_folder: str,
        *,
        mount_point: str = '/',
        check_source_folder: bool = True,
        index_filename: Optional[str] = None
) -> None:
    """
    Add static file support.

    :param app: The bareASGI application.
    :param source_folder: Where to find the files to serve.
    :param mount_point: Where the files should appear on the url.
    :param check_source_folder: If True check the source folder exists.
    :param index_filename: An optional index file name.
    """
    # The mount point must be absolute.
    if not mount_point.startswith('/') and mount_point.endswith('/'):
        raise RuntimeError('mount_point must start and end with "/"')

    path_variable = 'rest'

    static_file_provider = StaticFilesProvider(
        source_folder,
        path_variable=None if mount_point == '/' else path_variable,
        check_source_folder=check_source_folder,
        index_filename=index_filename
    )
    path = f'{mount_point}{{{path_variable}:path}}'
    app.http_router.add({'GET'}, path, static_file_provider)
