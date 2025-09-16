from flask import Blueprint


mod = Blueprint('blueprints', __name__)

try:
    from routes.chat_routes import routes as chat_routes
except (ImportError, ModuleNotFoundError):
    from api.routes.chat_routes import routes as chat_routes

try:
    from routes.user_routes import routes as user_routes
except (ImportError, ModuleNotFoundError):
    from api.routes.user_routes import routes as user_routes

try:
    from routes.book_routes import routes as book_routes
except (ImportError, ModuleNotFoundError):
    from api.routes.book_routes import routes as book_routes

try:
    from routes.file_routes import routes as file_routes
except (ImportError, ModuleNotFoundError):
    from api.routes.file_routes import routes as file_routes

routes = (chat_routes + user_routes + book_routes + file_routes)

for r in routes:
    mod.add_url_rule(
        r['rule'],
        endpoint=r.get('endpoint', None),
        view_func=r['view_func'],
        **r.get('options', {}))
