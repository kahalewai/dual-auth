"""
dual-auth API Call Utilities

API call handlers for in-session and out-of-session scenarios.

Author: kahalewai (https://www.github.com/kahalewai)
License: Apache 2.0
Version: 1.0.1
"""

from .insession_api_call import InSessionAPICall
from .outofsession_api_call import OutOfSessionAPICall

__all__ = [
    'InSessionAPICall',
    'OutOfSessionAPICall'
]
