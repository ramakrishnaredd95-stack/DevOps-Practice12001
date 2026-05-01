"""
Compatibility note.

The active implementation is now:
  ../../azure-functions/fetch-health/__init__.py
"""


def handler(event=None, context=None):
    return {
        "status": "moved",
        "message": "Use azure-functions/fetch-health instead.",
    }
