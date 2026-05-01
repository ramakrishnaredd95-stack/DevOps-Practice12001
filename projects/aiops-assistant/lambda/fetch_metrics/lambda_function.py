"""
Compatibility note.

The active implementation is now:
  ../../azure-functions/fetch-metrics/__init__.py
"""


def handler(event=None, context=None):
    return {
        "status": "moved",
        "message": "Use azure-functions/fetch-metrics instead.",
    }
