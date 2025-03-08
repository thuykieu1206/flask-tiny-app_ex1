from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    blocked = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)

    @property
    def is_active(self):
        return not self.blocked

    @property
    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id

    def reset_password(self, new_password):
        self.password = generate_password_hash(new_password)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    checked = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@app.route("/home")
@login_required
def home():
    if current_user.blocked:
        flash("Your account is blocked.")
        return redirect(url_for("login"))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    todos_query = Todo.query.filter_by(user_id=current_user.id)
    pagination = todos_query.paginate(page=page, per_page=per_page)
    
    return render_template("index.html", items=pagination.items, pagination=pagination)

@app.route("/add_todo", methods=["POST"])
@login_required
def add_todo():
    todo_name = request.form["todo_name"]
    if todo_name:
        new_todo = Todo(name=todo_name, user_id=current_user.id)
        db.session.add(new_todo)
        db.session.commit()
        flash("Task added successfully!")
    else:
        flash("Task name cannot be empty.")
    return redirect(url_for("home"))

@app.route("/checked/<int:todo_id>", methods=["POST"])
@login_required
def checked_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo:
        todo.checked = not todo.checked  
        db.session.commit()
        flash("Task updated successfully!")
    else:
        flash("Task not found!")
    return redirect(url_for("home"))

@app.route("/delete_tasks", methods=["POST"])
@login_required
def delete_tasks():
    task_ids = request.form.getlist("task_ids")
    if not task_ids:
        flash("No tasks selected for deletion.")
        return redirect(url_for("home"))
    
    for task_id in task_ids:
        task = Todo.query.get(task_id)
        if task and task.user_id == current_user.id:
            db.session.delete(task)
        else:
            flash(f"Task ID {task_id} not found or you do not have permission to delete.")
    
    db.session.commit()
    flash("Tasks deleted successfully!")
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if user.blocked:
                flash("Your account is blocked.")
                return redirect(url_for("login"))
            login_user(user)
            if user.is_admin:
                return redirect(url_for("admin"))
            return redirect(url_for("home"))
        flash("Invalid username or password.")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have logged out successfully.")
    return redirect(url_for("login"))

@app.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for("home"))
    users = User.query.all()
    return render_template("admin.html", users=users)

@app.route("/block_user/<int:user_id>", methods=["POST"])
@login_required
def block_user(user_id):
    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for("home"))
    user = User.query.get(user_id)
    if user:
        user.blocked = True
        db.session.commit()
        flash(f"User {user.username} has been blocked.")
    else:
        flash("User not found.")
    return redirect(url_for("admin"))

@app.route("/reset_password/<int:user_id>", methods=["POST"])
@login_required
def reset_password(user_id):
    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for("home"))
    user = User.query.get(user_id)
    new_password = request.form["new_password"]
    if user:
        user.reset_password(new_password)
        db.session.commit()
        flash(f"Password for {user.username} has been reset.")
    else:
        flash("User not found.")
    return redirect(url_for("admin"))

@app.route("/unblock_user/<int:user_id>", methods=["POST"])
@login_required
def unblock_user(user_id):
    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for("home"))
    
    user = User.query.get(user_id)
    if user:
        user.blocked = False
        db.session.commit()
        flash(f"User {user.username} has been unblocked.")
    else:
        flash("User not found.")
    
    return redirect(url_for("admin"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Tạo tài khoản admin
        admin_username = "ThuyKieu"
        admin_password = "120604"
        new_admin = User.query.filter_by(username=admin_username).first()
        if not new_admin:
            new_admin = User(username=admin_username, password=admin_password)
            new_admin.is_admin = True
            db.session.add(new_admin)
            db.session.commit()
            print("Admin account created successfully!")

        # Thêm dữ liệu giả lập cho 100 nhiệm vụ
        if Todo.query.count() == 0:  # Chỉ thêm nếu chưa có nhiệm vụ nào
            for i in range(1, 101):
                new_todo = Todo(name=f"Task {i}", user_id=new_admin.id)
                db.session.add(new_todo)
            db.session.commit()
            print("Sample tasks created successfully!")

    app.run(debug=True)