from flask import Flask, jsonify
from flask_cors import CORS
from datetime import timedelta
from flask_restful import Api
from flasgger import Swagger

# try:
#     from routes.blueprint_routes import mod
# except (ImportError, ModuleNotFoundError):
#     from api.routes.blueprint_routes import mod

try:
    from routes.chat_routes import chat_bp
except (ImportError, ModuleNotFoundError):
    from api.routes.chat_routes import chat_bp

try:
    from routes.book_routes import book_bp
except (ImportError, ModuleNotFoundError):
    from api.routes.book_routes import book_bp

try:
    from routes.file_routes import file_bp
except (ImportError, ModuleNotFoundError):
    from api.routes.file_routes import file_bp

try:
    from routes.user_routes import user_bp
except (ImportError, ModuleNotFoundError):
    from api.routes.user_routes import user_bp

app = Flask(__name__)
api = Api(app)

# api.add_resource(chatbot, '/chatbot')

# Swagger config (auto-generates swagger.json at /apidocs/swagger.json)
app.config['SWAGGER'] = {
    'title': "My Bookworm Flask API",
    'uiversion': 3  # Swagger UI version 3
}
swagger = Swagger(app)  # Initialize Flasgger

# CORS setup
CORS(app, supports_credentials=True, origins=["http://localhost:19260"])

app.config.update(
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_SECURE=True,
)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
app.secret_key = 'your-very-secure-secret-key'  # Replace with env var in prod


@app.route('/', methods=['GET'])
def home():

    """
    Home endpoint
    ---
    get:
      description: Welcome message to verify deployment
      responses:
        200:
          description: Returns a success message
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: Bookworm App is successfully deployed!
    """

    return jsonify({"message": "Bookworm App is successfully deployed!"})


# Register your other routes
# app.register_blueprint(mod, url_prefix='')
app.register_blueprint(chat_bp, url_prefix="")
app.register_blueprint(book_bp, url_prefix="")
app.register_blueprint(file_bp, url_prefix="")
app.register_blueprint(user_bp, url_prefix="")

if __name__ == '__main__':

    # http://localhost:5000/apidocs/
    app.run(debug=True)
