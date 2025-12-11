# app.py — Full Student Portfolio App
import os
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------
# App Configuration
# -----------------------
app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SECRET_KEY'] = 'replace_with_your_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -----------------------
# Database Models
# -----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    course = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    # Contact Information
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    # Professional Info
    skills = db.Column(db.Text)  # Comma-separated or newline-separated
    experience = db.Column(db.Text)  # Detailed experience description
    education = db.Column(db.Text)  # Education details
    is_admin = db.Column(db.Boolean, default=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    image_file = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# -----------------------
# Login Manager
# -----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper for uploads
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------
# Routes
# -----------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing = User.query.filter((User.email == email) | (User.username == username)).first()
        
        if existing:
            flash('User or email already exists.', 'danger')
            return redirect(url_for('register'))
        
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pw = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, pw):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', projects=projects)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.course = request.form['course']
        current_user.bio = request.form['bio']
        current_user.phone = request.form.get('phone', '')
        current_user.address = request.form.get('address', '')
        current_user.skills = request.form.get('skills', '')
        current_user.experience = request.form.get('experience', '')
        current_user.education = request.form.get('education', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid conflicts
                filename = f"profile_{current_user.id}_{datetime.utcnow().timestamp()}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_picture = filename
        
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        file = request.files['image']
        filename = None
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        project = Project(title=title, description=desc, image_file=filename, user_id=current_user.id)
        db.session.add(project)
        db.session.commit()
        flash('Project added.', 'success')
        return redirect(url_for('projects'))
    
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('projects.html', projects=projects)

@app.route('/projects/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    project = Project.query.get_or_404(id)
    
    if project.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('projects'))
    
    if request.method == 'POST':
        project.title = request.form['title']
        project.description = request.form['description']
        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for('projects'))
    
    return render_template('edit_project.html', project=project)

@app.route('/projects/delete/<int:id>')
@login_required
def delete_project(id):
    project = Project.query.get_or_404(id)
    
    if project.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('projects'))
    
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'info')
    return redirect(url_for('projects'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    projects = Project.query.all()
    return render_template('admin_dashboard.html', users=users, projects=projects)

@app.route('/portfolio/<username>')
def public_portfolio(username):
    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('home'))
    
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('public_portfolio.html', user=user, projects=projects)

@app.route('/download_portfolio/<username>')
def download_portfolio(username):
    user = User.query.filter_by(username=username).first()
    projects = Project.query.filter_by(user_id=user.id).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(f"{user.username}'s Portfolio", styles['Title']))
    elements.append(Spacer(1, 12))
    
    for p in projects:
        elements.append(Paragraph(f"<b>{p.title}</b>", styles['Heading3']))
        elements.append(Paragraph(p.description or '', styles['Normal']))
        elements.append(Spacer(1, 12))
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"{user.username}_portfolio.pdf")

if __name__ == '__main__':
    app.run(debug=True)
