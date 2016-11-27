import json
import logging
import random
import string
import functools
import asyncio

import aiohttp_jinja2
from aiohttp import web

from . import text

log = logging.getLogger(__name__)


async def index(request):
    resp = web.WebSocketResponse()
    ok, protocol = resp.can_start(request)
    if not ok:
        return aiohttp_jinja2.render_template('index.html', request, {})

    await resp.prepare(request)
    name = (random.choice(string.ascii_uppercase) + ''.join(random.sample(string.ascii_lowercase * 10, 10)))
    log.info('%s joined.', name)
    resp.send_str(json.dumps({'action': 'connect', 'name': name}))
    for ws in request.app['sockets'].values():
        ws.send_str(json.dumps({'action': 'join', 'name': name}))
    request.app['sockets'][name] = resp

    while True:
        msg = await resp.receive()

        if msg.type == web.MsgType.text:
            for ws in request.app['sockets'].values():
                if ws is not resp:
                    ws.send_str(json.dumps({'action': 'sent', 'name': name, 'text': msg.data}))

            # s = '%s: %s' % (name, msg.data)
            s = msg.data
            f = functools.partial(text.scroll, s, y=25, font='fonts/10x20.bdf')
            # await request.app.loop.run_in_executor(None, f)
            f()
        else:
            break

    del request.app['sockets'][name]
    log.info('%s disconnected.', name)
    for ws in request.app['sockets'].values():
        ws.send_str(json.dumps({'action': 'disconnect', 'name': name}))
    return resp


def setup(app):
    app.router.add_get('/', index)