"""
A file streaming example

Broqwse to: http://127.0.0.1:8000/example1
"""

import asyncio
import os.path

from hypercorn.asyncio import Config, serve

from bareasgi import Application, HttpRequest, HttpResponse
from bareasgi_static import file_response

here = os.path.abspath(os.path.dirname(__file__))


async def http_request_callback(request: HttpRequest) -> HttpResponse:
    return await file_response(request, 200, os.path.join(here, 'file_stream.html'))


app = Application()
app.http_router.add({'GET'}, '/example1', http_request_callback)

config = Config()
asyncio.run(serve(app, config))  # type: ignore
