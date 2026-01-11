from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "clave_secreta"

# Usuarios quemados
USUARIOS = {
    "Patricio": "1234",
    "Mateo": "abcd",
    "Johan": "0000"
}

# Lista global de salas
SALAS = []

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

    total_salas = len(SALAS)
    return render_template("dashboard.html", usuario=session["usuario"], total=total_salas)


@app.route("/salas", methods=["GET", "POST"])
def salas():
    if "usuario" not in session:
        return redirect(url_for("login"))

    error = None

    if request.method == "POST":
        nombre = request.form["nombre"]
        codigo = request.form["codigo"]
        capacidad = request.form["capacidad"]
        estado = request.form["estado"]

        # Validar código único
        for sala in SALAS:
            if sala["codigo"] == codigo:
                error = "El código de la sala ya existe"
                break

        if not error:
            SALAS.append({
                "nombre": nombre,
                "codigo": codigo,
                "capacidad": int(capacidad),
                "estado": estado,
                "usuario": session["usuario"]
            })
            return redirect(url_for("salas"))

    return render_template("salas.html", salas=SALAS, error=error)

@app.route("/perfiles")
def perfiles():
    if "usuario" not in session:
        return redirect(url_for("login"))

    resumen = {}

    for sala in SALAS:
        usuario = sala["usuario"]
        if usuario not in resumen:
            resumen[usuario] = {
                "total": 0,
                "salas": []
            }
        resumen[usuario]["total"] += 1
        resumen[usuario]["salas"].append(sala["codigo"])

    return render_template("perfiles.html", resumen=resumen)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
