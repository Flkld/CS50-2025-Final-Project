# Library

#### Video Demo:
[Link to the video here]

#### Description

My project is a reading tracker application that allows users to manage their personal library.  

- You can **search for books** using the Google Books API and import them into the database.  
- The user can **add a book**, update the **reading time** and the **current page**.  
- Once finished, they can **rate the book** with a score and write a **comment** about the reading.  
- It also allows you to **re-read the book** and track the progress again.  
- During registration, the user chooses an **accent color** that customizes the interface.  

The application is developed with **Flask** and **Bootstrap**.

---

### How to use it
- Setup requeriments:
```
pip install -r requirements.txt
```
1. The user can **register** at `/reg`.  
2. Log in at `/login`.  
3. Search for books in the search field located in the **top right bar**.  
4. Add them to the library and track their reading progress.  

---

### Main files

- **db.py** → database connection.  
- **app.py** → main Flask application.  
- **auth.py** → registration, login and logout.  
- **helper.py** → contains the `login_required` decorator.  
- **layout.html** → base template (header and footer).  
- **reg.html** → registration form.  
- **login.html** → login form.  
- **index.html** → main page, shows the reading progress.  
- **biblioteca.html** → section with all added books.  
- **resultado.html** → search results from Google Books.  

---

### Database schema

```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    edad INTEGER NOT NULL,
    hash TEXT NOT NULL,
    acento TEXT NOT NULL,
    tiempo_leyendo INTEGER NOT NULL DEFAULT 0,
    media_ph INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE generos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE usuario_genero (
    id_usuario INTEGER NOT NULL,
    id_genero INTEGER NOT NULL,
    PRIMARY KEY (id_usuario, id_genero),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY (id_genero) REFERENCES generos(id)
);

CREATE TABLE libro_genero (
    id_libro INTEGER NOT NULL,
    id_genero INTEGER NOT NULL,
    PRIMARY KEY (id_libro, id_genero),
    FOREIGN KEY (id_libro) REFERENCES libros(id),
    FOREIGN KEY (id_genero) REFERENCES generos(id)
);

CREATE TABLE lectura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_libro INTEGER NOT NULL,
    id_usuario INTEGER NOT NULL,
    tiempo INTEGER NOT NULL DEFAULT 0 CHECK (tiempo >= 0),
    nota INTEGER CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    estado TEXT NOT NULL DEFAULT 'To Be Read'
           CHECK (estado IN ('To Be Read', 'Reading', 'Read')),
    paginas_leidas INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (id_libro) REFERENCES libros(id),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

CREATE TABLE libros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn13 TEXT UNIQUE,
    titulo TEXT NOT NULL,
    autor TEXT,
    paginas INTEGER NOT NULL CHECK (paginas >= 0),
    editorial TEXT,
    ano_edicion TEXT,
    url_portada TEXT
);
```
### Notes:
ChatGPT was used to resolve doubts related to new functions (wraps, Blueprint, PIL, fetchone and fetchall, Google API…), as well as general layout with Bootstrap.