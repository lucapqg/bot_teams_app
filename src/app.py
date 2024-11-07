"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity
from http import HTTPStatus
from aiohttp import web
from botbuilder.core.integration import aiohttp_error_middleware
from bot import TeamsBot
from config import Config

config = Config()
routes = web.RouteTableDef()
bot = TeamsBot()


# Configurar o adaptador
settings = BotFrameworkAdapterSettings(config.APP_ID, config.APP_PASSWORD)
adapter = BotFrameworkAdapter(settings)

@routes.post("/api/messages")
async def on_messages(req: web.Request) -> web.Response:
    
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return web.Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    response = await adapter.process_activity(activity, auth_header, bot.on_turn)
    if response:
        return web.Response(status=response.status)
    return web.Response(status=200)

app = web.Application(middlewares=[aiohttp_error_middleware])
app.add_routes(routes)

from config import Config

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=Config.PORT)