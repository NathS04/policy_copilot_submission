__all__ = ["main"]


def main(*args, **kwargs):
    # Lazy import keeps streamlit optional for lightweight core installs.
    from .streamlit_app import main as _main
    return _main(*args, **kwargs)
