__version__ = "0.1.3"


def _print_type(t):
    if t is None:
        return ""
    elif isinstance(t, tuple):
        try:
            return ".".join(t)
        except:
            return str(t)
    elif hasattr(t, "__name__"):
        return t.__name__
    else:
        return type(t).__name__
