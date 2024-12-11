from flask import Flask
from dotenv import load_dotenv

# Import our routes:
from routes.api_routes import api_routes
from routes.misc import misc

app = Flask(__name__) ; load_dotenv()
app.register_blueprint(api_routes)
app.register_blueprint(misc)