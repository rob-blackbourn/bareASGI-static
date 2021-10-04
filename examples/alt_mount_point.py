"""
Typically static files are served from the root pat '/'.
However, sometimes it is necessary to serve them from a different
location. For example if the app provides a REST service the static
content might be mounted at '/ui' with the REST calls at '/api/'.
"""
import json
import os.path

import uvicorn

from bareasgi import Application, HttpRequest, HttpResponse
from bareutils import (
    text_reader,
    text_writer
)
from bareasgi_static import add_static_file_provider

here = os.path.abspath(os.path.dirname(__file__))


async def get_info(request: HttpRequest) -> HttpResponse:
    text = json.dumps(request.info)
    return HttpResponse(200, [(b'content-type', b'application/json')], text_writer(text))


async def set_info(request: HttpRequest) -> HttpResponse:
    text = await text_reader(request.body)
    data = json.loads(text)
    request.info.update(data)
    return HttpResponse(204)


app = Application(info={'name': 'Michael Caine'})
add_static_file_provider(
    app,
    os.path.join(here, 'alt_mount_point_www'),
    index_filename='index.html',
    mount_point='/ui/'
)
app.http_router.add({'GET'}, '/api/info', get_info)
app.http_router.add({'POST'}, '/api/info', set_info)

uvicorn.run(app, port=9010)
