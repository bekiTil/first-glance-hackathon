from fastapi import HTTPException


def todo(owner: str, what: str) -> HTTPException:
    """Return value for unimplemented routes: `raise todo("Bereket", "create watch")`."""
    return HTTPException(501, f"Not implemented yet: TODO({owner}) {what}")
