from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "clave_secreta"

DB_HOST = os.environ.get('MYSQL_HOST')
DB_USER = os.environ.get('MYSQL_USER', 'root')
DB_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root')
DB_NAME = os.environ.get('MYSQL_DB', 'salas_db')

# Conexión a la DB
def get_db_connection():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    return conn

# Crear la tabla al iniciar la aplicación (sin esperar request)
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS salas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                capacidad INT NOT NULL,
                estado VARCHAR(50) NOT NULL,
                usuario VARCHAR(255) NOT NULL
            )
        ''')
        conn.commit()
        print("Tabla 'salas' verificada/creada exitosamente.")  # Para debug
    except mysql.connector.Error as err:
        print(f"Error al crear la tabla: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Ejecutar la inicialización AHORA (al cargar el módulo)
with app.app_context():
    init_db()

USUARIOS = {
    "Patricio": "1234",
    "Mateo": "abcd",
    "Johan": "0000"
}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        if usuario in USUARIOS and USUARIOS[usuario] == password:
            session["usuario"] = usuario
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM salas")
    total_salas = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    return render_template("dashboard.html", usuario=session["usuario"], total=total_salas)

@app.route("/salas", methods=["GET", "POST"])
def salas():
    if "usuario" not in session:
        return redirect(url_for("login"))

    error = None
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        nombre = request.form["nombre"]
        codigo = request.form["codigo"]
        capacidad = request.form["capacidad"]
        estado = request.form["estado"]
        usuario = session["usuario"]

        # Validar código único
        cursor.execute("SELECT * FROM salas WHERE codigo = %s", (codigo,))
        if cursor.fetchone():
            error = "El código de la sala ya existe"
        else:
            cursor.execute("""
                INSERT INTO salas (nombre, codigo, capacidad, estado, usuario)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre, codigo, int(capacidad), estado, usuario))
            conn.commit()

        if not error:
            return redirect(url_for("salas"))

    # Obtener todas las salas
    cursor.execute("SELECT * FROM salas")
    salas_db = cursor.fetchall()
    salas = [{"id": s[0], "nombre": s[1], "codigo": s[2], "capacidad": s[3], "estado": s[4], "usuario": s[5]} for s in salas_db]

    cursor.close()
    conn.close()

    return render_template("salas.html", salas=salas, error=error)

@app.route("/perfiles")
def perfiles():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Resumen por usuario
    cursor.execute("""
        SELECT usuario, COUNT(*) as total, GROUP_CONCAT(codigo) as salas
        FROM salas
        GROUP BY usuario
    """)
    resumen_db = cursor.fetchall()
    resumen = {}
    for row in resumen_db:
        usuario = row[0]
        resumen[usuario] = {
            "total": row[1],
            "salas": row[2].split(',') if row[2] else []
        }

    cursor.close()
    conn.close()

    return render_template("perfiles.html", resumen=resumen)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)