import os.path
import uvicorn
from bareasgi import Application
from bareasgi_static import StaticFiles

here = os.path.abspath(os.path.dirname(__file__))
static_files = StaticFiles(os.path.join(here, 'www'), index_filename='index.html')

app = Application()
app.http_router.add({'GET'}, '/{rest:path}', static_files)

uvicorn.run(app, port=9010)
