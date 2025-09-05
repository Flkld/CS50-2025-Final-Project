from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from db import get_db
from functools import wraps
from PIL import ImageColor
auth = Blueprint("auth", __name__)

#Registro de usuario

@auth.route("/reg", methods=["GET", "POST"])
def reg():
    if request.method=="GET":
        return render_template("reg.html")
    data= {
    "nombre":   (request.form.get("nombre") or "").strip(),
    "apellidos":(request.form.get("apellidos") or "").strip(),
    "correo":   (request.form.get("correo") or "").strip().lower(),
    "edad":     (request.form.get("edad") or "").strip(),
    "password": request.form.get("password") or "",
    "acento":   request.form.get("acento") or ""
    }
    missing=[k for k, v in data.items() if not v]
    if missing:
        return "Faltan campos: " + ", ".join(missing), 400
    try: 
        edad= int(data["edad"])
        if edad < 0:
            return "Edad inválida", 400
    except ValueError:
        return "Edad inválida", 400    
    hash2 = generate_password_hash(data["password"], method="scrypt", salt_length=16)
    try:
        db=get_db()
        db.execute("insert into usuarios (nombre, apellidos, correo, edad, hash, acento) values (?, ?, ?, ?, ?, ?)", (data["nombre"], data["apellidos"], data["correo"], edad, hash2, data["acento"]))
        db.commit()
    except sqlite3.IntegrityError:
        return"Correo ya registrado", 400
    return redirect("/login")

#Inicio de sesión

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="GET":
        return render_template("login.html")
    correo=(request.form.get("correo") or "").strip().lower()
    password=request.form.get("password") or ""
    if not correo:
        return "Correo inválido", 400
    if not password:
        return "Contraseña inválida", 400   
    try: 
        consulta_login=get_db().execute ("select id, hash, acento, tiempo_leyendo from usuarios where correo=?", (correo,)).fetchone()
    except ValueError:
        return "Usuario inexistente", 403
    if consulta_login is None:
        return "Usuario inexistente", 403
    if not check_password_hash(consulta_login["hash"], password):
        return "Contraseña incorrecta", 403
    session.clear()
    session["user_id"] = consulta_login["id"]
    r,g,b = ImageColor.getrgb(consulta_login["acento"])
    r, g, b = [max(0, c - 30) for c in (r, g, b)]
    session["acento"] = consulta_login["acento"]
    session["tiempo_leyendo"] = consulta_login["tiempo_leyendo"]
    session["acento2"]=f"#{r:02x}{g:02x}{b:02x}"



    return redirect("/")

#Cierre de sesión
@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

#Función que delimita las funciones a usuarios logueados
def login_required(f): 
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
