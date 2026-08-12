from flask import Flask, render_template, request, redirect, url_for, session
from database import init_db, get_db
from utils import hash_password

app = Flask(__name__)
app.secret_key = "your-secret-key"


@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = hash_password(request.form["password"])

        connection = get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        connection.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]\
            
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()
    
    projects = connection.execute("""
            SELECT *
            FROM projects
            WHERE user_id = ?
            ORDER BY created_at DESC
    """, (session["user_id"],)).fetchall()
    
    connection.close()
    
    return render_template(
        "dashboard.html",
        username=session["username"],
        projects = projects
    )
    
@app.route("/register", methods=["GET", "POST"])

def register():

    if request.method == "POST":

        username = request.form["username"]
        password = hash_password(request.form["password"])

        connection = get_db()

        try:

            connection.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            connection.commit()

        except Exception:
            connection.close()
            return "Username already exists."

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    
    session.clear()
    
    return redirect(url_for("login"))

@app.route("/projects/create", methods = ["GET", "POST"])
def create_project():
    
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        
        connection = get_db()
        
        connection.execute(""" 
                INSERT INTO projects (user_id, name, description)
                VALUES (?, ?, ?)        
        """, (
            session["user_id"],
            name,
            description
        ))
        
        connection.commit()
        connection.close()
        
        return redirect(url_for("dashboard"))
    
    return render_template("create_project.html")



if __name__ == "__main__":
    init_db()
    app.run(debug=True)