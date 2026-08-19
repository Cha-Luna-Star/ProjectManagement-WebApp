from flask import Flask, render_template, request, redirect, url_for, session
from database import init_db, get_db
from utils import hash_password
from datetime import date, timedelta

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
        SELECT
            projects.*,
            COUNT(tasks.id) AS total_tasks,
            SUM(
                CASE
                    WHEN tasks.status = 'Completed'
                    THEN 1
                    ELSE 0
                END
            ) AS completed_tasks
        FROM projects
        LEFT JOIN tasks
            ON projects.id = tasks.project_id
        WHERE projects.user_id = ?
        GROUP BY projects.id
        ORDER BY projects.created_at DESC
    """, (session["user_id"],)).fetchall()

    projects = [dict(project) for project in projects]

    for project in projects:

        total_tasks = project["total_tasks"] or 0
        completed_tasks = project["completed_tasks"] or 0

        if total_tasks > 0:
            project["progress"] = (completed_tasks / total_tasks) * 100
        else:
            project["progress"] = 0
            
    stats = connection.execute("""
        SELECT
            COUNT(DISTINCT projects.id) AS total_projects,
            COUNT(tasks.id) AS total_tasks,
            SUM(
                CASE
                    WHEN tasks.status = 'Completed'
                    THEN 1
                    ELSE 0
                END
            ) AS completed_tasks,
            SUM(
                CASE
                    WHEN tasks.status = 'Pending'
                    THEN 1
                    ELSE 0
                END
            ) AS pending_tasks
        FROM projects
        LEFT JOIN tasks
            ON projects.id = tasks.project_id
        WHERE projects.user_id = ?
    """, (session["user_id"],)).fetchone()

    connection.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        projects=projects,
        stats=stats
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

    # Get tasks
    tasks = connection.execute("""
        SELECT *
        FROM tasks
        WHERE project_id = ?
        ORDER BY created_at DESC
    """, (project_id,)).fetchall()

    # Due date status
    today = date.today()
    soon = today + timedelta(days=3)

    tasks = [dict(task) for task in tasks]

    for task in tasks:

        task["due_status"] = "none"

        if task["due_date"] and task["status"] != "Completed":

            due_date = date.fromisoformat(task["due_date"])

            if due_date < today:
                task["due_status"] = "overdue"

            elif due_date <= soon:
                task["due_status"] = "soon"

            else:
                task["due_status"] = "normal"

    connection.close()

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

    # Get tasks
    tasks = connection.execute("""
        SELECT *
        FROM tasks
        WHERE project_id = ?
        ORDER BY created_at DESC
    """, (project_id,)).fetchall()

    # Due date status
    today = date.today()
    soon = today + timedelta(days=3)

    tasks = [dict(task) for task in tasks]

    for task in tasks:

        task["due_status"] = "none"

        if task["due_date"] and task["status"] != "Completed":

            due_date = date.fromisoformat(task["due_date"])

            if due_date < today:
                task["due_status"] = "overdue"

            elif due_date <= soon:
                task["due_status"] = "soon"

            else:
                task["due_status"] = "normal"

    connection.close()

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

    tasks = connection.execute("""
        SELECT *
        FROM tasks
        WHERE project_id = ?
        ORDER BY created_at DESC
    """, (project_id,)).fetchall()


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
    priority = request.args.get("priority")

    query = """
        SELECT *
        FROM tasks
        WHERE project_id = ?
    """

    params = [project_id]

    if status in ["Pending", "In Progress", "Completed"]:
        query += " AND status = ?"
        params.append(status)

    if priority in ["Low", "Medium", "High"]:
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY created_at DESC"

    tasks = connection.execute(
        query,
        params
    ).fetchall()

    connection.close()

    # -------------------------
    # DUE DATE STATUS
    # -------------------------

    today = date.today()
    soon = today + timedelta(days=3)

    tasks = [dict(task) for task in tasks]

    for task in tasks:

        task["due_status"] = "none"

        if task["due_date"] and task["status"] != "Completed":

            due_date = date.fromisoformat(task["due_date"])

            if due_date < today:
                task["due_status"] = "overdue"

            elif due_date <= soon:
                task["due_status"] = "soon"

            else:
                task["due_status"] = "normal"


    connection.close()
    
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

        status = request.args.get("status")
        priority = request.args.get("priority")
        sort = request.args.get("sort", "newest")

        query = """
            SELECT *
            FROM tasks
            WHERE project_id = ?
        """

        params = [project_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        if priority:
            query += " AND priority = ?"
            params.append(priority)


        if sort == "oldest":
            query += " ORDER BY created_at ASC"

        elif sort == "priority":
            query += """
                ORDER BY
                CASE priority
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                    ELSE 4
                END
            """

        elif sort == "status":
            query += """
                ORDER BY
                CASE status
                    WHEN 'Pending' THEN 1
                    WHEN 'In Progress' THEN 2
                    WHEN 'Completed' THEN 3
                    ELSE 4
                END
            """

        else:
            query += " ORDER BY created_at DESC"


        tasks = connection.execute(
            query,
            params
        ).fetchall()
    connection.close()


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
        tasks=tasks,
        task_counts=task_counts,
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
        due_date = request.form["due_date"]
        priority = request.form["priority"]

        connection.execute("""
            INSERT INTO tasks (
                project_id,
                title,
                description,
                due_date
            )
            VALUES (?, ?, ?, ?)
        """, (
            project_id,
            title,
            description,
            due_date
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
        priority = request.form["priority"]
        due_date = request.form["due_date"]


        connection.execute("""
            UPDATE tasks
            SET title = ?,
                description = ?,
                status = ?,
                priority = ?,
                due_date = ?
            WHERE id = ?
            AND project_id = ?
        """, (
            title,
            description,
            status,
            priority,
            due_date,
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

@app.route(
    "/projects/<int:project_id>/tasks/<int:task_id>/complete",
    methods=["POST"]
)
def complete_task(project_id, task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    task = connection.execute("""
        SELECT tasks.id
        FROM tasks
        JOIN projects
            ON tasks.project_id = projects.id
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
        UPDATE tasks
        SET status = 'Completed'
        WHERE id = ?
          AND project_id = ?
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