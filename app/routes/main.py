"""
INSYTE — Main Web Route Blueprint
Serves the responsive single-page evaluation dashboard.
"""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")
