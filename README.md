# bareasgi-static

Static file support for bareasgi

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
    return await file_response(scope, 200, os.path.join(here, 'example1.html'))


app = Application()
app.http_router.add({'GET'}, '/example1', http_request_callback)

uvicorn.run(app, port=9010)

```

The next example serves files below a given directory.

```python
import os.path
import uvicorn
from bareasgi import Application
from bareasgi_static import StaticFiles

here = os.path.abspath(os.path.dirname(__file__))
static_files = StaticFiles(os.path.join(here, 'www'), index_filename='index.html')

app = Application()
app.http_router.add({'GET'}, '/{rest:path}', static_files)

uvicorn.run(app, port=9010)
```