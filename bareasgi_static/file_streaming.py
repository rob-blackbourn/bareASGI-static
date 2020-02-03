import aiofiles
import aiofiles.os
from email.utils import formatdate, parsedate
import hashlib
import stat
import os
from typing import (
    List,
    Optional
)
from mimetypes import guess_type

from baretypes import (
    Scope,
    Header,
    Headers,
    Content,
    HttpResponse
)
from bareutils import text_writer
import bareutils.header as header

CHUNK_SIZE = 4096

NOT_MODIFIED_HEADERS = (
    b"cache-control",
    b"content-location",
    b"date",
    b"etag",
    b"expires",
    b"vary",
)


def _stat_to_etag(value: os.stat) -> str:
    key = f'{value.st_mtime}-{value.st_size}'.encode()
    hash_str = hashlib.md5(key)
    return hash_str.hexdigest()


def _is_not_modified(request_headers: List[Header], response_headers: Headers) -> bool:
    if request_headers is None or response_headers is None:
        return False
    etag = header.find(b'etag', response_headers)
    last_modified = header.find(b'last-modified', response_headers)
    if etag == header.find(b'if-none-match', request_headers):
        return True
    if not header.find(b'if-modified-since', request_headers):
        return False
    last_req_time = header.find(b'if-modified-since', request_headers)
    return parsedate(last_req_time) >= parsedate(last_modified)


async def file_writer(path: str, chunk_size: int = CHUNK_SIZE) -> Content:
    """
    Creates an async generator to write a file.

    :param path: The path of the file to write.
    :param chunk_size: The size of each block.
    :return: An async generator of bytes.
    """
    async with aiofiles.open(path, mode="rb") as file:
        more_body = True
        while more_body:
            chunk = await file.read(chunk_size)
            yield chunk
            more_body = len(chunk) == chunk_size


async def file_response(
        scope: Scope,
        status: int,
        path: str,
        headers: Optional[Headers] = None,
        content_type: Optional[str] = None,
        filename: Optional[str] = None,
        check_modified: Optional[bool] = False
) -> HttpResponse:
    """
    A utility method to create a file response.

    :param scope: The ASGI scope.
    :param status: The HTTP status code.
    :param path: The path to the file.
    :param headers: The headers.
    :param content_type: The content type.
    :param filename: The filename.
    :param check_modified: If True check for modifications to the file.
    :return: An http response.
    """
    try:
        stat_result = await aiofiles.os.stat(path)
        mode = stat_result.st_mode
        if not stat.S_ISREG(mode):
            raise RuntimeError(f"File at path {path} is not a file.")

        if not headers:
            headers = []

        if content_type is None:
            content_type = guess_type(filename or path)[0] or "text/plain"
        headers.append((b'content-type', content_type.encode()))

        headers.append((b'content-length', str(stat_result.st_size).encode()))
        headers.append((b'last-modified', formatdate(stat_result.st_mtime, usegmt=True).encode()))
        headers.append((b'etag', _stat_to_etag(stat_result).encode()))

        if filename is not None:
            content_disposition = f'attachment; filename="{filename}"'
            headers.append((b"content-disposition", content_disposition.encode()))

        if check_modified and _is_not_modified(scope['headers'], headers):
            return 304, [(name, value) for name, value in headers if name in NOT_MODIFIED_HEADERS], None

        return status, headers, None if scope['method'] == 'HEAD' else file_writer(path)

    except FileNotFoundError:
        return 500, [(b'content-type', b'text/plain')], text_writer(f"File at path {path} does not exist.")
    except RuntimeError:
        return 500
