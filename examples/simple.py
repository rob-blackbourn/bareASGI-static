import os.path
import uvicorn
from bareasgi import Application
from bareasgi_static import add_static_file_provider

here = os.path.abspath(os.path.dirname(__file__))

app = Application()
add_static_file_provider(app, os.path.join(here, 'simple_www'), index_filename='index.html')

uvicorn.run(app, port=9010)
