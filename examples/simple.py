"""
A simple example

Browse to: http://127.0.0.1:8000/index.html
"""

import asyncio
import os.path

from hypercorn.asyncio import Config, serve

from bareasgi import Application
from bareasgi_static import add_static_file_provider

here = os.path.abspath(os.path.dirname(__file__))

app = Application()
add_static_file_provider(app, os.path.join(
    here, 'simple_www'), index_filename='index.html')

config = Config()
asyncio.run(serve(app, config))
