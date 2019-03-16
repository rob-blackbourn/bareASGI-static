# bareasgi-static

Static file support for [bareASGI](http://github.com/rob-blackbourn/bareasgi) (read the [documentation](https://bareasgi-static.readthedocs.io/en/latest/))

## Overview

This package provides support for serving static files to bareasgi.

## Usage

The following example serves a single file.

```python
import uvicorn
import os.path
from bareasgi import Application
from bareasgi_static import file_response

here = os.path.abspath(os.path.dirname(__file__))

async def http_request_callback(scope, info, matches, content):
    return await file_response(scope, 200, os.path.join(here, 'file_stream.html'))

app = Application()
app.http_router.add({'GET'}, '/example1', http_request_callback)

uvicorn.run(app, port=9010)

```

The next example serves files below a given directory.

```python
import os.path
import uvicorn
from bareasgi import Application
from bareasgi_static import add_static_file_provider

here = os.path.abspath(os.path.dirname(__file__))

app = Application()
add_static_file_provider(app, os.path.join(here, simple_www), index_filename='index.html')

uvicorn.run(app, port=9010)
```