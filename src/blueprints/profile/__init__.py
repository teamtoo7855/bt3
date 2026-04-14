from flask import Blueprint

profile_bp = Blueprint('profile', __name__)

# Import routes at the bottom to avoid circular dependencies
from . import routes