import os
import asyncio
import uvicorn

from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

ADMIN_LISTEN_HOST = os.getenv('ADMIN_LISTEN_HOST', '127.0.0.1')
ADMIN_LISTEN_PORT = int(os.getenv('ADMIN_LISTEN_PORT', 5000))

async def stats(request):
    return JSONResponse(
        {
            "queue": request.app.ctx['scheduler'].qsize(),
            "errors": request.app.ctx['errors'],
            # XXX etc...
        }
    )

# ...
async def pause(request):
    scheduler = request.app.ctx["scheduler"].scheduler
    scheduler.pause()
    return JSONResponse({})


async def resume(request):
    scheduler = request.app.ctx["scheduler"].scheduler
    scheduler.resume()
    return JSONResponse({})


async def get_conf(request):
    return JSONResponse({'data': str(request.app.ctx['config'])})


app = Starlette(debug=True, routes=[
    Route('/stats', stats),
    Route('/pause', pause),
    Route('/resume', resume),
    Route('/conf', get_conf),
])


import threading
import uvicorn


class AdminServer:

    class Server(uvicorn.Server):
        def install_signal_handlers(self):
            pass

    server = None
    thread = None

    def start(self, ctx):
        app.ctx = ctx
        config = uvicorn.Config(app, host=ADMIN_LISTEN_HOST, port=ADMIN_LISTEN_PORT, log_level="info")
        self.server = AdminServer.Server(config=config)
        self.thread = threading.Thread(target=self.server.run)
        self.thread.start()

    def stop(self):
        self.server.should_exit = True
        self.thread.join()


async def start_server(stuff):
    app.stuff = stuff
    config = uvicorn.Config(app, host=ADMIN_LISTEN_HOST, port=ADMIN_LISTEN_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
