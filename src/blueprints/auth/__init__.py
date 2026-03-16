from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

# Import routes at the bottom to avoid circular dependencies
from . import routes