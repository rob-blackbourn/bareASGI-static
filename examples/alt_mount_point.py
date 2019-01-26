"""
Typically static files are served from the root pat '/'.
However, sometimes it is necessary to serve them from a different
location. For example if the app provides a REST service the static
content might be mounted at '/ui' with the REST calls at '/api/'.
"""
import json
import os.path
import uvicorn
from bareasgi import (
    Application,
    Scope,
    Info,
    RouteMatches,
    Content,
    HttpResponse,
    text_reader,
    text_writer
)
from bareasgi_static import add_static_file_provider

here = os.path.abspath(os.path.dirname(__file__))


async def get_info(scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:
    text = json.dumps(info)
    return 200, [(b'content-type', b'application/json')], text_writer(text)


async def set_info(scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:
    text = await text_reader(content)
    data = json.loads(text)
    info.update(data)
    return 204, None, None


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
