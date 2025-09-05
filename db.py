from flask import g
import sqlite3
 
#conexión a la base de datos
DB_PATH = "libros.db"
def get_db():
    if "db" not in g:
        conexion = sqlite3.connect(DB_PATH)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys=ON")
        g.db = conexion
    return g.db
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
