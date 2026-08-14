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

@app.route("/projects/<int:project_id>")
def project(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    project = connection.execute("""
        SELECT *
        FROM projects
        WHERE id = ? AND user_id = ?
    """, (project_id, session["user_id"])).fetchone()

    if project is None:
        connection.close()
        return "Project not found", 404

    # Get task counts
    task_counts = connection.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed
        FROM tasks
        WHERE project_id = ?
    """, (project_id,)).fetchone()

    # Get selected status from URL
    status = request.args.get("status")

    if status in ["Pending", "In Progress", "Completed"]:

        tasks = connection.execute("""
            SELECT *
            FROM tasks
            WHERE project_id = ? AND status = ?
            ORDER BY created_at DESC
        """, (project_id, status)).fetchall()

    else:

        tasks = connection.execute("""
            SELECT *
            FROM tasks
            WHERE project_id = ?
            ORDER BY created_at DESC
        """, (project_id,)).fetchall()

    connection.close()

    return render_template(
        "project.html",
        project=project,
        tasks=tasks,
        task_counts=task_counts,
        username=session["username"]
    )

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    project = connection.execute("""
        SELECT *
        FROM projects
        WHERE id = ? AND user_id = ?
    """, (project_id, session["user_id"])).fetchone()

    if project is None:
        connection.close()
        return "Project not found", 404

    status = request.args.get("status")

    if status in ["Pending", "In Progress", "Completed"]:

        tasks = connection.execute("""
            SELECT *
            FROM tasks
            WHERE project_id = ? AND status = ?
            ORDER BY created_at DESC
        """, (project_id, status)).fetchall()

    else:

        tasks = connection.execute("""
            SELECT *
            FROM tasks
            WHERE project_id = ?
            ORDER BY created_at DESC
        """, (project_id,)).fetchall()
    connection.close()

    return render_template(
        "project.html",
        project=project,
        tasks=tasks,
        username=session["username"]
    )

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    project = connection.execute("""
        SELECT *
        FROM projects
        WHERE id = ? AND user_id = ?
    """, (project_id, session["user_id"])).fetchone()

    connection.close()

    if project is None:
        return "Project not found", 404

    return render_template(
        "project.html",
        project=project,
        username=session["username"]
    )
    
@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    project = connection.execute("""
        SELECT *
        FROM projects
        WHERE id = ? AND user_id = ?
    """, (project_id, session["user_id"])).fetchone()

    if project is None:
        connection.close()
        return "Project not found", 404

    if request.method == "POST":

        name = request.form["name"]
        description = request.form["description"]

        connection.execute("""
            UPDATE projects
            SET name = ?, description = ?
            WHERE id = ? AND user_id = ?
        """, (
            name,
            description,
            project_id,
            session["user_id"]
        ))

        connection.commit()
        connection.close()

        return redirect(url_for(
            "project",
            project_id=project_id
        ))

    connection.close()

    return render_template(
        "edit_project.html",
        project=project
    )

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    project = connection.execute("""
        SELECT *
        FROM projects
        WHERE id = ? AND user_id = ?
    """, (project_id, session["user_id"])).fetchone()

    if project is None:
        connection.close()
        return "Project not found", 404

    if request.method == "POST":

        name = request.form["name"]
        description = request.form["description"]

        connection.execute("""
            UPDATE projects
            SET name = ?, description = ?
            WHERE id = ? AND user_id = ?
        """, (
            name,
            description,
            project_id,
            session["user_id"]
        ))

        connection.commit()
        connection.close()

        return redirect(url_for(
            "project",
            project_id=project_id
        ))

    connection.close()

    return render_template(
        "edit_project.html",
        project=project
    )

@app.route("/projects/<int:project_id>/delete", methods=["GET", "POST"])
def delete_project(project_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    connection = get_db()

    connection.execute("""
            DELETE FROM projects
            WHERE id =? AND user_id = ?
    """, (project_id, session["user_id"]))
    
    connection.commit()
    connection.close()
    
    return render_template(url_for("dashboard"))

@app.route("/projects/<int:project_id>/tasks/create", methods=["GET", "POST"])
def create_task(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    project = connection.execute("""
        SELECT *
        FROM projects
        WHERE id = ? AND user_id = ?
    """, (project_id, session["user_id"])).fetchone()

    if project is None:
        connection.close()
        return "Project not found", 404

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]

        connection.execute("""
            INSERT INTO tasks (project_id, title, description)
            VALUES (?, ?, ?)
        """, (
            project_id,
            title,
            description
        ))

        connection.commit()
        connection.close()

        return redirect(url_for(
            "project",
            project_id=project_id
        ))

    connection.close()

    return render_template(
        "create_task.html",
        project=project
    )

@app.route("/projects/<int:project_id>/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(project_id, task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    # Make sure the task belongs to the project
    # and the project belongs to the logged-in user
    task = connection.execute("""
        SELECT tasks.*
        FROM tasks
        JOIN projects ON tasks.project_id = projects.id
        WHERE tasks.id = ?
        AND tasks.project_id = ?
        AND projects.user_id = ?
    """, (
        task_id,
        project_id,
        session["user_id"]
    )).fetchone()

    if task is None:
        connection.close()
        return "Task not found", 404

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        status = request.form["status"]

        connection.execute("""
            UPDATE tasks
            SET title = ?, description = ?, status = ?
            WHERE id = ? AND project_id = ?
        """, (
            title,
            description,
            status,
            task_id,
            project_id
        ))

        connection.commit()
        connection.close()

        return redirect(url_for(
            "project",
            project_id=project_id
        ))

    connection.close()

    return render_template(
        "edit_task.html",
        task=task,
        project_id=project_id
    )

@app.route("/projects/<int:project_id>/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(project_id, task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    # Make sure the task belongs to the project
    # and the project belongs to the logged-in user
    task = connection.execute("""
        SELECT tasks.id
        FROM tasks
        JOIN projects ON tasks.project_id = projects.id
        WHERE tasks.id = ?
        AND tasks.project_id = ?
        AND projects.user_id = ?
    """, (
        task_id,
        project_id,
        session["user_id"]
    )).fetchone()

    if task is None:
        connection.close()
        return "Task not found", 404

    connection.execute("""
        DELETE FROM tasks
        WHERE id = ? AND project_id = ?
    """, (
        task_id,
        project_id
    ))

    connection.commit()
    connection.close()

    return redirect(url_for(
        "project",
        project_id=project_id
    ))
    
if __name__ == "__main__":
    init_db()
    app.run(debug=True)