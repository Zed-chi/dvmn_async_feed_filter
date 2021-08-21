from aiohttp import web

routes = web.RouteTableDef()

@routes.get('/')
async def hello(request):    
    urls_line = request.rel_url.query['urls']
    urls = urls_line.split(",")
    result = {
        "urls":urls
    }
    return web.json_response(result)

app = web.Application()
app.add_routes(routes)
web.run_app(app, host="127.0.0.1", port=5000)