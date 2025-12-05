import os
import sys

# Ensure the local project root is on sys.path so ``import libot`` works during tests
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
