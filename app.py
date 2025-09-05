from flask import Flask, render_template, request, redirect, session, g
from flask_session import Session
from auth import auth, login_required
from db import get_db, close_db
import requests
import json
from helper import obtener_isbn13



app=Flask(__name__)
app.secret_key = "pYdqut-fyndo7-wozdex"


# Sesión
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# Blueprint para dividir las funciones en archivos
app.register_blueprint(auth)
@app.teardown_appcontext
def teardown_db(exception):
    close_db()


# Página principal, index
@app.route("/")
def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    db=get_db()
    user=db.execute("select nombre, acento from usuarios where id=?", (user_id,)).fetchone()
    if user is None:
        session.clear()
        return redirect("/login")
    leyendo=db.execute("select l.id, l.titulo, l.autor, l.url_portada,lec.tiempo, lec.paginas_leidas, lec.estado from lectura lec join libros l ON l.id = lec.id_libro where lec.id_usuario = ? and lec.estado = 'Reading'", (user_id,)).fetchall()
    leidos=db.execute("select l.id, l.titulo, l.autor, l.url_portada,lec.tiempo, lec.paginas_leidas, lec.estado, lec.nota, lec.comentario from lectura lec join libros l ON l.id = lec.id_libro where lec.id_usuario = ? and lec.estado = 'Read'", (user_id,)).fetchall()

    return render_template("index.html", nombre=user["nombre"], acento=[user["acento"]], leyendo=leyendo, leidos=leidos)
    

@app.route("/search", methods=["GET", "POST"])#realiza la busqueda en la api de google
@login_required
def search():
    if request.method=="GET":
        return render_template("index.html")
    consulta=(request.form.get("search") or "").strip()
    if not consulta:
        return "No se buscó nada", 400
    busqueda= requests.get("https://www.googleapis.com/books/v1/volumes", params={"q":consulta})
    if busqueda.status_code != 200:
        return "Error de conexion", 502
    respuesta= busqueda.json().get("items", [])
    resultados=[]
    for libros in respuesta:
        datos=libros.get("volumeInfo", {})
        resultados.append({
            "titulo": datos.get("title", "Sin título"),
        "autor": ", ".join(datos.get("authors", ["Desconocido"])),
        "editorial": datos.get("publisher", "N/D"),
        "paginas": datos.get("pageCount", 0) or 0,
        "anio": (datos.get("publishedDate") or "N/D"),
        "isbn13": (obtener_isbn13(datos)),
        "generos": ", ".join(datos.get("categories", []) or ["N/D"]),
        "portada": (datos.get("imageLinks", {}) or {}).get("thumbnail", "")
        })    
    return render_template("resultado.html", resultados=resultados, consulta=consulta)

@app.route("/nuevo_libro", methods=["post"]) #añade el resultado de la busqueda a la base de datos
@login_required
def nuevo_libro():
    user_id= session.get("user_id")
    #Cargar el JSON
    libro_json =request.form.get("libro")
    if not libro_json:
        return "Datos insuficientes", 400
    try:
        datos=json.loads(libro_json)
    except ValueError:
        return "Error al parsear los datos desde el json", 400
    titulo =datos.get("titulo")
    autor=datos.get("autor")
    genero_string = datos.get("generos") or "N/D"
    if not titulo or not autor:
        return "Datos insuficientes", 400
    #conectar a la base de datos y cargar en ella el libro
    db=get_db()
    db.execute("insert into libros (isbn13, titulo, autor, paginas, editorial, ano_edicion, url_portada) values (?, ?, ?, ?, ?, ?, ?)", (datos["isbn13"], datos["titulo"], datos["autor"], datos["paginas"], datos["editorial"], datos["anio"], datos["portada"]))
    libro_id=db.execute("select last_insert_rowid() as id").fetchone()["id"]
    db.execute("insert or ignore into generos (nombre) values (?)", (genero_string,))
    
    #obtener y asignar genero
    genero_id=db.execute("select id from generos where nombre=?",(genero_string,)).fetchone()["id"]
    db.execute("insert or ignore into libro_genero (id_libro, id_genero) values (?,?)", (libro_id, genero_id))
    db.execute("insert into lectura (id_libro, id_usuario, tiempo, nota, comentario, estado, paginas_leidas) ""Values (?, ?, 0, NULL, NULL, 'To Be Read', 0)", (libro_id, user_id))
    db.commit()
    return redirect("/biblioteca")

@app.route("/biblioteca", methods=["get", "post"]) #carga los libros en biblioteca
@login_required
def biblioteca():
    user_id= session.get("user_id")
    if not user_id:
        return redirect("/login")
    
    db = get_db()
    filas = db.execute("select l.id, l.titulo, l.autor, l.url_portada, l.paginas, g.nombre as genero, lec.estado, lec.paginas_leidas, lec.tiempo from libros l left join libro_genero lg on lg.id_libro = l.id left join generos g on g.id = lg.id_genero left join lectura lec on lec.id_libro = l.id and lec.id_usuario = ?", (user_id,)).fetchall()
    return render_template("biblioteca.html", libros=filas)

@app.route("/cambiar_estado/<int:libro_id>", methods=["post"]) #cambia el estado de los libros desde la biblioteca
@login_required
def cambiar_estado(libro_id):
    user_id=session.get("user_id")
    if not user_id:
        return redirect("/login")
    
    db=get_db()
    obtener_estado=db.execute("select estado from lectura where id_usuario= ? and id_libro=?", (user_id, libro_id)).fetchone()
    if obtener_estado is None:
        db.execute("insert into lectura (id_libro, id_usuario, tiempo, nota, comentario, estado, paginas_leidas) values (?,?, 0, NULL, NULL, 'To Be Read', 0)", (libro_id, user_id))
        estado_actual="To Be Read"
    else:
        estado_actual=obtener_estado["estado"]
    nuevo_estado={"To Be Read": "Reading", "Reading": "Read", "Read": "To Be Read"}.get(estado_actual, "To Be Read")
    db.execute("UPDATE lectura SET estado = ? WHERE id_usuario = ? AND id_libro = ?",(nuevo_estado, user_id, libro_id))
    db.commit()
    return redirect("/biblioteca")

@app.route("/tiempo/<int:libro_id>", methods=["post"]) #actualiza el tiempo leyendo, por libro y en total
@login_required
def cambiar_tiempo(libro_id):
    user_id=session.get("user_id")
    db=get_db()
    minutos=request.form.get("minutos")
    if minutos:
        minutos=int(minutos)
        db.execute("update lectura set tiempo=tiempo+ ? where id_libro =? and id_usuario = ?", (int(minutos), libro_id, user_id))
        db.execute("update usuarios set tiempo_leyendo = tiempo_leyendo + ? where id = ?", (int(minutos), user_id ))
        session["tiempo_leyendo"] = session["tiempo_leyendo"] + minutos
    if request.form.get("accion") == "terminar":
        nota=request.form.get("nota")
        comentario=request.form.get("comentario")
        db.execute("update lectura set estado = 'Read', nota= ?, comentario=? where id_libro = ? and id_usuario = ?", (int(nota), comentario, libro_id, user_id))
    paginas=request.form.get("paginas")
    if paginas:
        db.execute("update lectura set paginas_leidas=? where id_libro = ? and id_usuario =?", (int(paginas), libro_id, user_id))
    db.commit()
    return redirect("/")


