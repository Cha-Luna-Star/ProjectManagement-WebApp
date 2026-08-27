from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import os
from database import init_db, get_db
from utils import hash_password, verify_password
from datetime import date, timedelta
from flask_wtf.csrf import CSRFProtect
import sqlite3

load_dotenv()

app = Flask(__name__)
print(app.template_folder)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

csrf = CSRFProtect(app)

@app.route("/", methods=["GET", "POST"])
def login():


    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        connection.close()

        if user and verify_password(password, user["password"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")
    

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        connection.close()

        if user and verify_password(password, user["password"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")
    

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        connection.close()

        if user and verify_password(password, user["password"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

    flash("Invalid username or password.", "error") 
    return render_template("login.html")
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    groups = connection.execute("""
        SELECT
            groups.*,
            group_members.role
        FROM groups
        JOIN group_members
            ON groups.id = group_members.group_id
        WHERE group_members.user_id = ?
        ORDER BY groups.created_at DESC
    """, (session["user_id"],)).fetchall()

    projects = connection.execute("""
        SELECT
            projects.*,
            groups.name AS group_name,
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
        LEFT JOIN groups
            ON projects.group_id = groups.id
        LEFT JOIN group_members
            ON projects.group_id = group_members.group_id
            AND group_members.user_id = ?
        WHERE projects.user_id = ?
        OR group_members.user_id IS NOT NULL
        GROUP BY projects.id
        ORDER BY projects.created_at DESC
    """, (
        session["user_id"],
        session["user_id"]
    )).fetchall()
    
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
        LEFT JOIN group_members
            ON projects.group_id = group_members.group_id
            AND group_members.user_id = ?
        WHERE projects.user_id = ?
        OR group_members.user_id IS NOT NULL
    """, (
        session["user_id"],
        session["user_id"]
    )).fetchone()

    connection.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        projects=projects,
        groups=groups,
        stats=stats
    )
    
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        connection = get_db()

        try:

            connection.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hash_password(password))
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            flash("Username already exists.", "error")
            return redirect(url_for("register"))

        connection.close()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        connection.close()

        if user and verify_password(password, user["password"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

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

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Project name is required.", "error")
            return render_template("create_project.html")

        if len(name) > 100:
            flash("Project name must be 100 characters or less.", "error")
            return render_template("create_project.html")

        if len(description) > 1000:
            flash("Project description must be 1000 characters or less.", "error")
            return render_template("create_project.html")
        
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

        flash("Project created successfully!", "success")

        return redirect(url_for("dashboard"))
    return render_template("create_project.html")

@app.route("/projects/<int:project_id>")
def project(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    status = request.args.get("status")
    priority = request.args.get("priority")
    sort = request.args.get("sort", "newest")

    connection = get_db()

    project = connection.execute("""
        SELECT projects.*
        FROM projects
        LEFT JOIN group_members
            ON projects.group_id = group_members.group_id
            AND group_members.user_id = ?
        WHERE projects.id = ?
        AND (
            projects.user_id = ?
            OR group_members.user_id IS NOT NULL
        )
    """, (
        session["user_id"],
        project_id,
        session["user_id"]
    )).fetchone()

    if project is None:
        connection.close()
        return "Project not found", 404

    task_counts = connection.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed
        FROM tasks
        WHERE project_id = ?
    """, (project_id,)).fetchone()

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

    return render_template(
        "project.html",
        project=project,
        tasks=tasks,
        task_counts=task_counts,
        username=session["username"]
    )
    

    status = request.args.get("status")
    priority = request.args.get("priority")
    sort = request.args.get("sort", "newest")
    
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

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Project name is required.", "error")
            connection.close()
            return render_template(
                "edit_project.html",
                project=project
            )

        if len(name) > 100:
            flash("Project name must be 100 characters or less.", "error")
            connection.close()
            return render_template(
                "edit_project.html",
                project=project
            )

        if len(description) > 1000:
            flash("Project description must be 1000 characters or less.", "error")
            connection.close()
            return render_template(
                "edit_project.html",
                project=project
            )

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

        flash("Project updated successfully!", "success")

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

@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    project = connection.execute("""
        SELECT projects.*
        FROM projects
        LEFT JOIN group_members
            ON projects.group_id = group_members.group_id
            AND group_members.user_id = ?
        WHERE projects.id = ?
        AND (
            projects.user_id = ?
            OR group_members.user_id IS NOT NULL
        )
    """, (
        session["user_id"],
        project_id,
        session["user_id"]
    )).fetchone()

    if project is None:
        connection.close()
        return "Project not found", 404

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            connection.close()
            flash("Project name is required.", "error")
            return render_template(
                "edit_project.html",
                project=project
            )

        if len(name) > 100:
            connection.close()
            flash(
                "Project name must be 100 characters or less.",
                "error"
            )
            return render_template(
                "edit_project.html",
                project=project
            )

        if len(description) > 1000:
            connection.close()
            flash(
                "Project description must be 1000 characters or less.",
                "error"
            )
            return render_template(
                "edit_project.html",
                project=project
            )

        connection.execute("""
            UPDATE projects
            SET name = ?, description = ?
            WHERE id = ?
        """, (
            name,
            description,
            project_id
        ))

        connection.commit()
        connection.close()

        flash("Project updated successfully!", "success")

        return redirect(url_for(
            "project",
            project_id=project_id
        ))

    connection.close()

    return render_template(
        "edit_project.html",
        project=project
    )
    
@app.route("/projects/<int:project_id>/delete", methods=["POST"])
def delete_project(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    project = connection.execute("""
        SELECT projects.*
        FROM projects
        LEFT JOIN groups
            ON projects.group_id = groups.id
        WHERE projects.id = ?
        AND (
            (
                projects.group_id IS NULL
                AND projects.user_id = ?
            )
            OR
            (
                projects.group_id IS NOT NULL
                AND groups.created_by = ?
            )
        )
    """, (
        project_id,
        session["user_id"],
        session["user_id"]
    )).fetchone()
    
    if project is None:
        connection.close()
        return "Project not found or you do not have permission", 403

    connection.execute("""
        DELETE FROM tasks
        WHERE project_id = ?
    """, (project_id,))

    connection.execute("""
        DELETE FROM projects
        WHERE id = ?
    """, (project_id,))

    connection.commit()
    connection.close()

    flash("Project deleted successfully!", "success")

    return redirect(url_for("dashboard"))

@app.route("/projects/<int:project_id>/tasks/create", methods=["GET", "POST"])
def create_task(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    project = connection.execute("""
        SELECT projects.*
        FROM projects
        LEFT JOIN group_members
            ON projects.group_id = group_members.group_id
            AND group_members.user_id = ?
        WHERE projects.id = ?
        AND (
            projects.user_id = ?
            OR group_members.user_id IS NOT NULL
        )
    """, (
        session["user_id"],
        project_id,
        session["user_id"]
    )).fetchone()

    if project is None:
        connection.close()
        return "Project not found", 404

    if request.method == "POST":

        title = request.form["title"].strip()
        description = request.form["description"].strip()
        due_date = request.form.get("due_date", "").strip()
        priority = request.form.get("priority", "").strip()

        allowed_priorities = [
            "Low",
            "Medium",
            "High"
        ]

        if not title:
            connection.close()
            flash("Task title is required.", "error")
            return render_template(
                "create_task.html",
                project=project
            )

        if priority not in allowed_priorities:
            connection.close()
            flash("Invalid priority.", "error")
            return render_template(
                "create_task.html",
                project=project
            )

        if due_date:
            try:
                date.fromisoformat(due_date)
            except ValueError:
                connection.close()
                flash("Invalid due date.", "error")
                return render_template(
                    "create_task.html",
                    project=project
                )

        connection.execute("""
            INSERT INTO tasks (
                project_id,
                title,
                description,
                priority,
                due_date
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            project_id,
            title,
            description,
            priority,
            due_date
        ))

        connection.commit()
        connection.close()

        flash("Task created successfully!", "success")

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

    project = connection.execute("""
        SELECT projects.*
        FROM projects
        LEFT JOIN group_members
            ON projects.group_id = group_members.group_id
            AND group_members.user_id = ?
        WHERE projects.id = ?
        AND (
            projects.user_id = ?
            OR group_members.user_id IS NOT NULL
        )
    """, (
        session["user_id"],
        project_id,
        session["user_id"]
    )).fetchone()

    if project is None:
        connection.close()
        return "Project not found", 404

    task = connection.execute("""
        SELECT *
        FROM tasks
        WHERE id = ?
        AND project_id = ?
    """, (
        task_id,
        project_id
    )).fetchone()

    if task is None:
        connection.close()
        return "Task not found", 404

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status")
        priority = request.form.get("priority")
        due_date = request.form.get("due_date")

        allowed_statuses = [
            "Pending",
            "In Progress",
            "Completed"
        ]

        allowed_priorities = [
            "Low",
            "Medium",
            "High"
        ]

        if not title:
            connection.close()
            flash("Task title is required.", "error")
            return render_template(
                "edit_task.html",
                task=task,
                project=project
            )

        if status not in allowed_statuses:
            connection.close()
            return "Invalid status", 400

        if priority not in allowed_priorities:
            connection.close()
            return "Invalid priority", 400

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

        flash("Task updated successfully!", "success")

        return redirect(url_for(
            "project",
            project_id=project_id
        ))

    connection.close()

    return render_template(
        "edit_task.html",
        task=task,
        project=project
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
        LEFT JOIN group_members
            ON projects.group_id = group_members.group_id
            AND group_members.user_id = ?
        WHERE tasks.id = ?
        AND tasks.project_id = ?
        AND (
            projects.user_id = ?
            OR group_members.user_id IS NOT NULL
        )
    """, (
        session["user_id"],
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

    flash("Task marked as completed!", "success")

    return redirect(url_for(
        "project",
        project_id=project_id
    ))
    
@app.route("/projects/<int:project_id>/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(project_id, task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    task = connection.execute("""
        SELECT tasks.id
        FROM tasks
        JOIN projects
            ON tasks.project_id = projects.id
        LEFT JOIN group_members
            ON projects.group_id = group_members.group_id
            AND group_members.user_id = ?
        WHERE tasks.id = ?
        AND tasks.project_id = ?
        AND (
            projects.user_id = ?
            OR group_members.user_id IS NOT NULL
        )
    """, (
        session["user_id"],
        task_id,
        project_id,
        session["user_id"]
    )).fetchone()

    if task is None:
        connection.close()
        return "Task not found or you do not have permission", 403

    connection.execute("""
        DELETE FROM tasks
        WHERE id = ?
        AND project_id = ?
    """, (
        task_id,
        project_id
    ))

    connection.commit()
    connection.close()

    flash("Task deleted successfully!", "success")

    return redirect(url_for(
        "project",
        project_id=project_id
    ))

@app.route(
    "/projects/<int:project_id>/tasks/<int:task_id>/status",
    methods=["POST"]
)
def update_task_status(project_id, task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    status = request.form["status"]

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Completed"
    ]

    if status not in allowed_statuses:
        return "Invalid status", 400

    connection = get_db()

    task = connection.execute("""
        SELECT tasks.id
        FROM tasks
        JOIN projects
            ON tasks.project_id = projects.id
        LEFT JOIN group_members
            ON projects.group_id = group_members.group_id
            AND group_members.user_id = ?
        WHERE tasks.id = ?
        AND tasks.project_id = ?
        AND (
            projects.user_id = ?
            OR group_members.user_id IS NOT NULL
        )
    """, (
        session["user_id"],
        task_id,
        project_id,
        session["user_id"]
    )).fetchone()

    if task is None:
        connection.close()
        return "Task not found", 404

    connection.execute("""
        UPDATE tasks
        SET status = ?
        WHERE id = ?
          AND project_id = ?
    """, (
        status,
        task_id,
        project_id
    ))

    connection.commit()
    connection.close()

    flash("Task status updated!", "success")

    return redirect(url_for(
        "project",
        project_id=project_id
    ))

@app.route("/groups/create", methods=["GET", "POST"])
def create_group():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Group name is required.", "error")
            return render_template(
                "create_group.html"
            )

        if len(name) > 100:
            flash("Group name must be 100 characters or less.", "error")
            return render_template(
                "create_group.html"
            )

        if len(description) > 1000:
            flash(
                "Group description must be 1000 characters or less.",
                "error"
            )
            return render_template(
                "create_group.html"
            )

        connection = get_db()

        cursor = connection.execute("""
            INSERT INTO groups (
                name,
                description,
                created_by
            )
            VALUES (?, ?, ?)
        """, (
            name,
            description,
            session["user_id"]
        ))

        group_id = cursor.lastrowid

        connection.execute("""
            INSERT INTO group_members (
                group_id,
                user_id,
                role
            )
            VALUES (?, ?, 'Owner')
        """, (
            group_id,
            session["user_id"]
        ))

        connection.commit()
        connection.close()

        flash("Group created successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("create_group.html")

@app.route("/groups/<int:group_id>")
def group(group_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
    """, (group_id,)).fetchone()

    if group is None:
        connection.close()
        return "Group not found", 404

    member = connection.execute("""
        SELECT *
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        session["user_id"]
    )).fetchone()

    if member is None:
        connection.close()
        return "You are not a member of this group", 403

    members = connection.execute("""
        SELECT
            group_members.*,
            users.username
        FROM group_members
        JOIN users
            ON group_members.user_id = users.id
        WHERE group_members.group_id = ?
        ORDER BY group_members.joined_at ASC
    """, (group_id,)).fetchall()

    projects = connection.execute("""
        SELECT *
        FROM projects
        WHERE group_id = ?
        ORDER BY created_at DESC
    """, (group_id,)).fetchall()

    connection.close()

    return render_template(
        "group.html",
        group=group,
        member=member,
        members=members,
        projects=projects,
        username=session["username"]
    )

@app.route("/groups/<int:group_id>/projects/create", methods=["GET", "POST"])
def create_group_project(group_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    member = connection.execute("""
        SELECT group_members.*
        FROM group_members
        JOIN groups
            ON group_members.group_id = groups.id
        WHERE group_members.group_id = ?
        AND group_members.user_id = ?
    """, (
        group_id,
        session["user_id"]
    )).fetchone()

    if member is None:
        connection.close()
        return "You are not a member of this group", 403
    
    if member["role"] not in ["Owner", "Admin"]:
        connection.close()
        return "You do not have permission to create projects in this group", 403

    group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
    """, (group_id,)).fetchone()

    if group is None:
        connection.close()
        return "Group not found", 404

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            connection.close()
            flash("Project name is required.", "error")
            return render_template(
                "create_project.html",
                group=group
            )

        connection.execute("""
            INSERT INTO projects (
                user_id,
                group_id,
                name,
                description
            )
            VALUES (?, ?, ?, ?)
        """, (
            session["user_id"],
            group_id,
            name,
            description
        ))

        connection.commit()
        connection.close()

        flash("Project created successfully!", "success")

        return redirect(url_for(
            "group",
            group_id=group_id
        ))

    connection.close()

    return render_template(
        "create_project.html",
        group=group
    )
    
@app.route("/groups/<int:group_id>/members/add", methods=["POST"])
def add_group_member(group_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    username = request.form.get("username", "").strip()

    if not username:
        flash("Username is required.", "error")
        return redirect(url_for(
            "group",
            group_id=group_id
        ))

    connection = get_db()

    # Check that the current user is Owner or Admin
    group = connection.execute("""
        SELECT groups.*
        FROM groups
        JOIN group_members
            ON groups.id = group_members.group_id
        WHERE groups.id = ?
        AND group_members.user_id = ?
        AND group_members.role IN ('Owner', 'Admin')
    """, (
        group_id,
        session["user_id"]
    )).fetchone()
    if group is None:
        connection.close()
        return "You do not have permission to manage this group", 403

    # Find the user
    user = connection.execute("""
        SELECT id, username
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    if user is None:
        connection.close()
        flash("User not found.", "error")
        return redirect(url_for(
            "group",
            group_id=group_id
        ))

    # Check if the user is already a member
    existing_member = connection.execute("""
        SELECT id
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        user["id"]
    )).fetchone()

    if existing_member:
        connection.close()
        flash("User is already a member of this group.", "error")
        return redirect(url_for(
            "group",
            group_id=group_id
        ))

    # Add the user
    connection.execute("""
        INSERT INTO group_members (
            group_id,
            user_id,
            role
        )
        VALUES (?, ?, 'Member')
    """, (
        group_id,
        user["id"]
    ))

    connection.commit()
    connection.close()

    flash(
        f"{user['username']} was added to the group!",
        "success"
    )

    return redirect(url_for(
        "group",
        group_id=group_id
    ))

@app.route("/groups/<int:group_id>/members/<int:user_id>/promote", methods=["POST"])
def promote_group_member(group_id, user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
        AND created_by = ?
    """, (
        group_id,
        session["user_id"]
    )).fetchone()

    if group is None:
        connection.close()
        return "Only the group owner can promote members", 403

    member = connection.execute("""
        SELECT *
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        user_id
    )).fetchone()

    if member is None:
        connection.close()
        return "Member not found", 404

    if member["role"] != "Member":
        connection.close()
        flash("This user is already an Admin or Owner.", "error")
        return redirect(url_for(
            "group",
            group_id=group_id
        ))

    connection.execute("""
        UPDATE group_members
        SET role = 'Admin'
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        user_id
    ))

    connection.commit()
    connection.close()

    flash("Member promoted to Admin.", "success")

    return redirect(url_for(
        "group",
        group_id=group_id
    ))

@app.route("/groups/<int:group_id>/members/<int:user_id>/demote", methods=["POST"])
def demote_group_member(group_id, user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
        AND created_by = ?
    """, (
        group_id,
        session["user_id"]
    )).fetchone()

    if group is None:
        connection.close()
        return "Only the group owner can demote members", 403

    member = connection.execute("""
        SELECT *
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        user_id
    )).fetchone()

    if member is None:
        connection.close()
        return "Member not found", 404

    if member["role"] != "Admin":
        connection.close()
        flash("This user is not an Admin.", "error")
        return redirect(url_for(
            "group",
            group_id=group_id
        ))

    connection.execute("""
        UPDATE group_members
        SET role = 'Member'
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        user_id
    ))

    connection.commit()
    connection.close()

    flash("Admin demoted to Member.", "success")

    return redirect(url_for(
        "group",
        group_id=group_id
    ))

@app.route("/groups/<int:group_id>/members/<int:user_id>/remove", methods=["POST"])
def remove_group_member(group_id, user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    current_member = connection.execute("""
        SELECT role
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        session["user_id"]
    )).fetchone()

    if current_member is None:
        connection.close()
        return "You are not a member of this group", 403

    if current_member["role"] not in ["Owner", "Admin"]:
        connection.close()
        return "You do not have permission to remove members", 403

    target_member = connection.execute("""
        SELECT role
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        user_id
    )).fetchone()

    if target_member is None:
        connection.close()
        return "Member not found", 404

    if target_member["role"] == "Owner":
        connection.close()
        return "The group owner cannot be removed", 403

    if (
        current_member["role"] == "Admin"
        and target_member["role"] == "Admin"
    ):
        connection.close()
        return "Admins cannot remove other Admins", 403

    connection.execute("""
        DELETE FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        user_id
    ))

    connection.commit()
    connection.close()

    flash("Member removed successfully!", "success")

    return redirect(url_for(
        "group",
        group_id=group_id
    ))

@app.route("/groups/<int:group_id>/leave", methods=["POST"])
def leave_group(group_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    member = connection.execute("""
        SELECT role
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        session["user_id"]
    )).fetchone()

    if member is None:
        connection.close()
        return "You are not a member of this group", 403

    if member["role"] == "Owner":
        connection.close()
        return "The group owner cannot leave the group", 403

    connection.execute("""
        DELETE FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    flash("You left the group.", "success")

    return redirect(url_for("dashboard"))

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    member = connection.execute("""
        SELECT role
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        session["user_id"]
    )).fetchone()

    if member is None:
        connection.close()
        return "You are not a member of this group", 403

    if member["role"] == "Owner":
        connection.close()
        flash("The group owner cannot leave the group.", "error")
        return redirect(url_for(
            "group",
            group_id=group_id
        ))

    connection.execute("""
        DELETE FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    flash("You left the group.", "success")

    return redirect(url_for("dashboard"))

@app.route("/groups/<int:group_id>/delete", methods=["POST"])
def delete_group(group_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
        AND created_by = ?
    """, (
        group_id,
        session["user_id"]
    )).fetchone()

    if group is None:
        connection.close()
        return "You do not have permission to delete this group", 403

    connection.execute("""
        DELETE FROM tasks
        WHERE project_id IN (
            SELECT id
            FROM projects
            WHERE group_id = ?
        )
    """, (group_id,))

    connection.execute("""
        DELETE FROM projects
        WHERE group_id = ?
    """, (group_id,))

    connection.execute("""
        DELETE FROM group_members
        WHERE group_id = ?
    """, (group_id,))

    connection.execute("""
        DELETE FROM groups
        WHERE id = ?
    """, (group_id,))

    connection.commit()
    connection.close()

    flash("Group deleted successfully!", "success")

    return redirect(url_for("dashboard"))

@app.route("/groups/<int:group_id>/projects/create", methods=["GET", "POST"])
def create_group_project(group_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()

    member = connection.execute("""
        SELECT *
        FROM group_members
        WHERE group_id = ?
        AND user_id = ?
    """, (
        group_id,
        session["user_id"]
    )).fetchone()

    if member is None:
        connection.close()
        return "You are not a member of this group", 403

    group = connection.execute("""
        SELECT *
        FROM groups
        WHERE id = ?
    """, (group_id,)).fetchone()

    if group is None:
        connection.close()
        return "Group not found", 404

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            connection.close()
            flash("Project name is required.", "error")
            return render_template(
                "create_project.html",
                group=group
            )

        connection.execute("""
            INSERT INTO projects (
                user_id,
                group_id,
                name,
                description
            )
            VALUES (?, ?, ?, ?)
        """, (
            session["user_id"],
            group_id,
            name,
            description
        ))

        connection.commit()
        connection.close()

        flash("Project created successfully!", "success")

        return redirect(url_for(
            "group",
            group_id=group_id
        ))

    connection.close()

    return render_template(
        "create_project.html",
        group=group
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)