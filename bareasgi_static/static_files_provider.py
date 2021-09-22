"""Static Files Provider"""

import os
import stat
from typing import Optional

from aiofiles.os import stat as aio_stat
from bareasgi import Application, HttpRequest, HttpResponse
from bareutils import text_writer, response_code

from .file_streaming import file_response


class StaticFilesProvider:
    """Static files provider"""

    def __init__(
            self,
            source_folder: str,
            *,
            path_variable: Optional[str] = None,
            check_source_folder: bool = True,
            index_filename: Optional[str] = None
    ) -> None:
        """A static file provider.

        Args:
            source_folder (str): Where to find the files to serve.
            path_variable (Optional[str], optional): A path variable to capture
                the mount point. Defaults to None.
            check_source_folder (bool, optional): If True check the source
                folder exists. Defaults to True.
            index_filename (Optional[str], optional): An optional index file
                name. Defaults to None.

        Raises:
            RuntimeError: If the source folder does not exist.
        """
        if check_source_folder and not os.path.isdir(source_folder):
            raise RuntimeError(f"Directory '{source_folder}' does not exist")
        self.source_folder = source_folder
        self.path_variable = path_variable
        self.config_checked = False
        self.index_filename = index_filename

    async def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.scope["method"] not in ("GET", "HEAD"):
            return HttpResponse(
                response_code.METHOD_NOT_ALLOWED,
                [(b'content-type', b'text/plain')],
                text_writer("Method Not Allowed")
            )

        try:
            # Get the path from the scope or the route match.
            path: str = '/' + \
                request.matches.get(
                    self.path_variable,
                    '') if self.path_variable else request.scope["path"]
            if (path == '' or path.endswith('/')) and self.index_filename:
                path += self.index_filename

            relative_path = os.path.normpath(os.path.join(*path.split("/")))
            if relative_path.startswith(".."):
                raise FileNotFoundError()

            rooted_path = os.path.join(self.source_folder, relative_path)

            if self.config_checked:
                check_directory = None
            else:
                check_directory = self.source_folder
                self.config_checked = True

            if check_directory is not None:
                stat_result = await aio_stat(check_directory)
                if not (stat.S_ISDIR(stat_result.st_mode) or stat.S_ISLNK(stat_result.st_mode)):
                    raise FileNotFoundError()

            stat_result = await aio_stat(rooted_path)
            mode = stat_result.st_mode
            if not stat.S_ISREG(mode):
                raise FileNotFoundError()

            return await file_response(request.scope, 200, rooted_path, check_modified=True)
        except FileNotFoundError:
            return HttpResponse(
                response_code.NOT_FOUND,
                [(b'content-type', b'text/plain')],
                text_writer("Not Found")
            )


def add_static_file_provider(
        app: Application,
        source_folder: str,
        *,
        mount_point: str = '/',
        check_source_folder: bool = True,
        index_filename: Optional[str] = None
) -> None:
    """Add static file support.

    Args:
        app (Application): The bareASGI application.
        source_folder (str): Where to find the files to serve.
        mount_point (str, optional): Where the files should appear on the url.
            Defaults to '/'.
        check_source_folder (bool, optional): If True check the source folder
            exists. Defaults to True.
        index_filename (Optional[str], optional): An optional index file name.
            Defaults to None.

    Raises:
        RuntimeError: If the mount point doesn't start with '/'.
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
