"""Pytest defaults — quiet Matrix UX during unit tests."""

import os

os.environ.setdefault("MATRIX_NO_COLOR", "1")
os.environ.setdefault("MATRIX_NO_RAIN", "1")
os.environ.setdefault("MATRIX_SOUND", "0")
os.environ.setdefault("MATRIX_STREAM", "0")
os.environ.setdefault("MATRIX_PACE", "0")
os.environ.setdefault("MATRIX_DASHBOARD", "0")
os.environ.setdefault("MATRIX_VERTICAL", "0")
os.environ.setdefault("MATRIX_FAST", "1")

from matrix import config as matrix_config

matrix_config.config = matrix_config.Config.from_env()
