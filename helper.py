from flask import redirect, session
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def obtener_isbn13(info:dict):
    for x in (info.get ("industryIdentifiers") or []):
        if x.get("type") == "ISBN_13":
            return x.get("identifier")
    return None