"""File streaming"""

from email.utils import formatdate, parsedate
import hashlib
import stat
import os
from time import mktime, struct_time
from typing import (
    AsyncIterable,
    Iterable,
    List,
    Optional,
    Tuple,
    cast
)
from mimetypes import guess_type

import aiofiles
import aiofiles.os

from bareasgi import HttpRequest, HttpResponse
from bareutils import text_writer, header, response_code

CHUNK_SIZE = 4096

NOT_MODIFIED_HEADERS = (
    b"cache-control",
    b"content-location",
    b"date",
    b"etag",
    b"expires",
    b"vary",
)


def _stat_to_etag(value: os.stat_result) -> str:
    key = f'{value.st_mtime}-{value.st_size}'.encode()
    hash_str = hashlib.md5(key)
    return hash_str.hexdigest()


def _is_not_modified(
        request_headers: Iterable[Tuple[bytes, bytes]],
        response_headers: Iterable[Tuple[bytes, bytes]]
) -> bool:
    if request_headers is None or response_headers is None:
        return False
    etag = header.find(b'etag', response_headers)
    last_modified = header.find(b'last-modified', response_headers)
    assert last_modified is not None
    if etag == header.find(b'if-none-match', request_headers):
        return True
    if not header.find(b'if-modified-since', request_headers):
        return False
    last_req_time = header.find(b'if-modified-since', request_headers)
    assert last_req_time is not None
    last_req = cast(struct_time, parsedate(last_req_time.decode()))
    last_modified_struct_time = cast(
        struct_time,
        parsedate(last_modified.decode())
    )
    return mktime(last_req) >= mktime(last_modified_struct_time)


async def file_writer(path: str, chunk_size: int = CHUNK_SIZE) -> AsyncIterable[bytes]:
    """Creates an async iterator to write a file.

    Args:
        path (str): The path of the file to write.
        chunk_size (int, optional): The size of each block. Defaults to
            CHUNK_SIZE.

    Returns:
        Content: An async iterator of bytes.

    Yields:
        Content: The bytes in chunks.
    """
    async with aiofiles.open(path, mode="rb") as file:
        more_body = True
        while more_body:
            chunk = await file.read(chunk_size)
            yield chunk
            more_body = len(chunk) == chunk_size


async def file_response(
        request: HttpRequest,
        status: int,
        path: str,
        headers: Optional[List[Tuple[bytes, bytes]]] = None,
        content_type: Optional[str] = None,
        filename: Optional[str] = None,
        check_modified: Optional[bool] = False
) -> HttpResponse:
    """A utility method to create a file response.

    Args:
        scope (Scope): The ASGI scope.
        status (int): The HTTP status code.
        path (str): The path to the file.
        headers (Optional[Headers], optional): The headers. Defaults to None.
        content_type (Optional[str], optional): The content type.. Defaults to
            None.
        filename (Optional[str], optional): The filename. Defaults to None.
        check_modified (Optional[bool], optional): If True check for
            modifications to the file. Defaults to False.

    Raises:
        RuntimeError: If the path was not a file.

    Returns:
        HttpResponse: The HTTP response
    """
    try:
        stat_result = await aiofiles.os.stat(path)
        mode = stat_result.st_mode
        if not stat.S_ISREG(mode):
            raise RuntimeError(f"File at path {path} is not a file.")

        if not headers:
            headers = []
        else:
            headers = headers.copy()

        if content_type is None:
            content_type = guess_type(filename or path)[0] or "text/plain"
        headers.append((b'content-type', content_type.encode()))

        headers.append((b'content-length', str(stat_result.st_size).encode()))
        headers.append(
            (
                b'last-modified',
                formatdate(stat_result.st_mtime, usegmt=True).encode()
            )
        )
        headers.append((b'etag', _stat_to_etag(stat_result).encode()))

        if filename is not None:
            content_disposition = f'attachment; filename="{filename}"'
            headers.append(
                (b"content-disposition", content_disposition.encode()))

        if check_modified and _is_not_modified(request.scope['headers'], headers):
            return HttpResponse(
                response_code.NOT_MODIFIED,
                [
                    (name, value)
                    for name, value in headers if name in NOT_MODIFIED_HEADERS
                ],
                None
            )

        return HttpResponse(
            status,
            headers,
            None if request.scope['method'] == 'HEAD' else file_writer(path)
        )

    except FileNotFoundError:
        return HttpResponse(
            response_code.INTERNAL_SERVER_ERROR,
            [(b'content-type', b'text/plain')],
            text_writer(f"File at path {path} does not exist.")
        )
    except RuntimeError:
        return HttpResponse(response_code.INTERNAL_SERVER_ERROR)
