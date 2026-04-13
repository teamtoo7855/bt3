from flask import Flask
from config import Config

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.profile import profile_bp
from blueprints.dashboard import dashboard_bp
from blueprints.api import api_bp
from blueprints.data_geojson import data_geojson_bp

app = Flask(__name__)
app.config.from_object(Config)


# Register blueprints
app.register_blueprint(dashboard_bp)  # Handles root route /
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(api_bp)
app.register_blueprint(data_geojson_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

