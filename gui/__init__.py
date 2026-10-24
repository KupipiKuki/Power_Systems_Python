"""Facade package marker; REPO_ROOT is where faultCalculationClass finds CSVs."""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
