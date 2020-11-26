import sys

if sys.version_info < (3, 8):
    import importlib_metadata as metadata
else:
    from importlib import metadata

VERSION = metadata.version('timezone-converter')
