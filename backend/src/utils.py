"""Utility functions for the Perplexity OSS application."""

import os
from typing import Union


def strtobool(val: Union[str, bool]) -> bool:
    """Convert string representation of truth to True or False."""
    if isinstance(val, bool):
        return val
    return val.lower() in ("true", "1", "t", "yes", "on")


# Configuration constants
PRO_MODE_ENABLED = strtobool(os.environ.get("NEXT_PUBLIC_PRO_MODE_ENABLED", "true"))
