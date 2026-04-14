from flask import Blueprint

data_geojson_bp = Blueprint('data_geojson', __name__)

# Import routes at the bottom to avoid circular dependencies
from . import routes