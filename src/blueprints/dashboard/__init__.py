from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__)

# Import routes at the bottom to avoid circular dependencies
from . import routes