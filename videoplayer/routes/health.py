from __future__ import annotations

from flask import Blueprint, jsonify
from ..extensions import limiter

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
@limiter.limit("10 per minute")
def health():
    # Liveness: process is up
    return jsonify(status="ok"), 200