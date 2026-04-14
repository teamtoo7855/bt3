from flask import Flask
from config import Config

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.profile import profile_bp
from blueprints.dashboard import dashboard_bp
from blueprints.api import api_bp
from blueprints.data_geojson import data_geojson_bp
from utils.logging_config import logging_setup
import logging

app = Flask(__name__)
app.config.from_object(Config)
logging_setup()
logger = logging.getLogger(__name__)

# Register blueprints
app.register_blueprint(dashboard_bp)  # Handles root route /
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(api_bp)
app.register_blueprint(data_geojson_bp)

if __name__ == "__main__":
    logger.info("Starting app")
    app.run(host="0.0.0.0", port=8080, debug=True)

