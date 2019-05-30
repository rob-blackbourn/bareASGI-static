import uvicorn
import os.path
from bareasgi import Application
from baretypes import (
    Scope,
    Info,
    RouteMatches,
    Content,
    HttpResponse
)
from bareasgi_static import file_response

here = os.path.abspath(os.path.dirname(__file__))


async def http_request_callback(scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:
    return await file_response(scope, 200, os.path.join(here, 'file_stream.html'))


app = Application()
app.http_router.add({'GET'}, '/example1', http_request_callback)

uvicorn.run(app, port=9010)
