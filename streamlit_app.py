from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'timothy_kabo_graphic_school_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_cms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin' or 'staff'
    full_name = db.Column(db.String(100), nullable=False)

class NewsPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.String(30), nullable=False)

# HTML Template (Single-file template rendered by Flask)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timothy Kabo Graphic School Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">

    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-link navbar-brand fw-bold" href="{{ url_for('index') }}">
                <i class="fas fa-graduation-cap me-2"></i>Timothy Kabo Graphic School
            </a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('index') }}">Home</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('news') }}">News Feed</a></li>
                    {% if session.get('user_id') %}
                        {% if session.get('role') == 'admin' %}
                            <li class="nav-item"><a class="nav-link text-warning" href="{{ url_for('admin_dashboard') }}">Admin Portal</a></li>
                        {% endif %}
                        <li class="nav-item"><a class="nav-link text-info" href="{{ url_for('staff_dashboard') }}">Publisher Workspace</a></li>
                        <li class="nav-item"><a class="nav-link text-danger" href="{{ url_for('logout') }}">Logout ({{ session['username'] }})</a></li>
                    {% else %}
                        <li class="nav-item"><a class="btn btn-primary btn-sm ms-2" href="{{ url_for('login') }}">Login</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <!-- Flashed Messages -->
    <div class="container mt-3">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <!-- Main Content Dynamic Container -->
    <div class="container my-4">
        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# App Routes
@app.route('/')
def index():
    recent_news = NewsPost.query.order_by(NewsPost.id.desc()).limit(3).all()
    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="p-5 mb-4 bg-primary text-white rounded-3">
        <h1 class="display-5 fw-bold">Welcome to Timothy Kabo Graphic School</h1>
        <p class="col-md-8 fs-4">Excellence in visual design, creative arts, and digital technology.</p>
        <a class="btn btn-light btn-lg fw-bold" href="{{ url_for('news') }}">View All News & Announcements</a>
    </div>
    
    <h3 class="fw-bold mb-3">Latest Updates</h3>
    <div class="row g-4">
        {% for post in posts %}
        <div class="col-md-4">
            <div class="card h-100 shadow-sm border-0">
                <div class="card-body">
                    <span class="badge bg-secondary mb-2">{{ post.category }}</span>
                    <h5 class="card-title fw-bold">{{ post.title }}</h5>
                    <p class="card-text text-muted">{{ post.content[:100] }}...</p>
                </div>
                <div class="card-footer bg-transparent border-0 text-muted small">
                    By {{ post.author }} on {{ post.date_posted }}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endblock %}
    """
    return render_template_string(HTML_TEMPLATE.replace('{% block content %}{% endblock %}', content), posts=recent_news)

@app.route('/news')
def news():
    all_news = NewsPost.query.order_by(NewsPost.id.desc()).all()
    content = """
    {% extends "base.html" %}
    {% block content %}
    <h2 class="fw-bold mb-4"><i class="fas fa-newspaper me-2"></i>School Announcements & News</h2>
    <div class="row g-4">
        {% for post in posts %}
        <div class="col-md-6">
            <div class="card shadow-sm border-0">
                <div class="card-body">
                    <span class="badge bg-primary mb-2">{{ post.category }}</span>
                    <h4 class="card-title fw-bold">{{ post.title }}</h4>
                    <p class="card-text">{{ post.content }}</p>
                </div>
                <div class="card-footer bg-transparent border-0 text-muted small d-flex justify-content-between">
                    <span><i class="fas fa-user me-1"></i> {{ post.author }}</span>
                    <span><i class="fas fa-calendar-alt me-1"></i> {{ post.date_posted }}</span>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endblock %}
    """
    return render_template_string(HTML_TEMPLATE.replace('{% block content %}{% endblock %}', content), posts=all_news)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            flash('Logged in successfully!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('staff_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="row justify-content-center">
        <div class="col-md-4">
            <div class="card p-4 shadow-sm border-0">
                <h4 class="fw-bold text-center mb-3">System Login</h4>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" name="username" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" name="password" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 fw-bold">Sign In</button>
                </form>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(HTML_TEMPLATE.replace('{% block content %}{% endblock %}', content))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form['role']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'warning')
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password_hash=hashed_pw, role=role, full_name=full_name)
            db.session.add(new_user)
            db.session.commit()
            flash(f'Account created for {full_name} ({role})!', 'success')

    users = User.query.all()
    content = """
    {% extends "base.html" %}
    {% block content %}
    <h2 class="fw-bold mb-4"><i class="fas fa-user-shield me-2"></i>Admin Dashboard</h2>
    
    <div class="card p-4 shadow-sm border-0 mb-4">
        <h5 class="fw-bold">Create Staff / Admin User Account</h5>
        <form method="POST" class="row g-3 mt-1">
            <div class="col-md-3">
                <input type="text" name="full_name" class="form-control" placeholder="Full Name" required>
            </div>
            <div class="col-md-3">
                <input type="text" name="username" class="form-control" placeholder="Username" required>
            </div>
            <div class="col-md-3">
                <input type="password" name="password" class="form-control" placeholder="Password" required>
            </div>
            <div class="col-md-3">
                <select name="role" class="form-select">
                    <option value="staff">Publishing Staff</option>
                    <option value="admin">Administrator</option>
                </select>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-success fw-bold">Add Account</button>
            </div>
        </form>
    </div>

    <h4 class="fw-bold">System Users</h4>
    <ul class="list-group">
        {% for u in users %}
        <li class="list-group-item d-flex justify-content-between align-items-center">
            {{ u.full_name }} ({{ u.username }})
            <span class="badge bg-{{ 'danger' if u.role == 'admin' else 'info' }}">{{ u.role }}</span>
        </li>
        {% endfor %}
    </ul>
    {% endblock %}
    """
    return render_template_string(HTML_TEMPLATE.replace('{% block content %}{% endblock %}', content), users=users)

@app.route('/staff', methods=['GET', 'POST'])
def staff_dashboard():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        content_text = request.form['content']
        from datetime import date
        today = date.today().strftime("%B %d, %Y")

        new_post = NewsPost(
            title=title,
            category=category,
            content=content_text,
            author=session.get('full_name', session['username']),
            date_posted=today
        )
        db.session.add(new_post)
        db.session.commit()
        flash('News article published successfully!', 'success')
        return redirect(url_for('news'))

    content = """
    {% extends "base.html" %}
    {% block content %}
    <h2 class="fw-bold mb-4"><i class="fas fa-edit me-2"></i>Publishing Staff Workspace</h2>
    
    <div class="card p-4 shadow-sm border-0">
        <h5 class="fw-bold">Post New Article</h5>
        <form method="POST" class="mt-3">
            <div class="mb-3">
                <label class="form-label fw-bold">Title</label>
                <input type="text" name="title" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label fw-bold">Category</label>
                <select name="category" class="form-select">
                    <option>Announcement</option>
                    <option>Academic News</option>
                    <option>Event</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label fw-bold">Article Content</label>
                <textarea name="content" class="form-control" rows="5" required></textarea>
            </div>
            <button type="submit" class="btn btn-success fw-bold">Publish News</button>
        </form>
    </div>
    {% endblock %}
    """
    return render_template_string(HTML_TEMPLATE.replace('{% block content %}{% endblock %}', content))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# Database Initialization
def init_db():
    with app.app_context():
        db.create_all()
        # Create Default Admin if none exists
        if not User.query.filter_by(username='admin').first():
            default_admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                full_name='System Director'
            )
            default_staff = User(
                username='staff',
                password_hash=generate_password_hash('staff123'),
                role='staff',
                full_name='Editorial Staff'
            )
            db.session.add(default_admin)
            db.session.add(default_staff)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
