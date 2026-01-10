"""Shared middleware for all services"""
from .request_id import RequestIDMiddleware

__all__ = ["RequestIDMiddleware"]
