import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'ultra_secret_key_for_eco_project'

# --- НАСТРОЙКИ ДОСТУПА В АДМИНКУ ---
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'sherdoraka' # <--- ИЗМЕНИ ЭТО!

# Настройка базы данных
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///eco_project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- МОДЕЛИ ДАННЫХ ---

class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    motivation = db.Column(db.String(500))
    points = db.Column(db.Integer, default=10)
    time_joined = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d.%m.%Y"))

    def get_rank(self):
        if self.points >= 100: return "Эко-Герой"
        if self.points >= 50: return "Активист"
        return "Новичок"

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d.%m.%Y"))

# --- ЗАЩИТА АДМИНКИ ---

def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def authenticate():
    return Response('Нужна авторизация', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

with app.app_context():
    db.create_all()

# --- МАРШРУТЫ ---

@app.route('/')
def index():
    articles = Article.query.order_by(Article.id.desc()).all()
    event = {"title": "Чистый Ферганский Парк"}
    return render_template('index.html', event=event, articles=articles)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    phone = request.form.get('phone')
    motivation = request.form.get('motivation')

    if not name or not phone:
        flash('Укажите имя и телефон!', 'error')
        return redirect(url_for('index'))

    existing = Volunteer.query.filter_by(phone=phone).first()
    if existing:
        session['user_id'] = existing.id
        return redirect(url_for('dashboard'))

    new_v = Volunteer(name=name, phone=phone, motivation=motivation)
    db.session.add(new_v)
    db.session.commit()
    session['user_id'] = new_v.id
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user = Volunteer.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/admin')
@requires_auth
def admin_panel():
    volunteers = Volunteer.query.all()
    total_points = sum(v.points for v in volunteers)
    return render_template('admin.html', volunteers=volunteers, total_points=total_points)

@app.route('/admin/update_points/<int:v_id>/<action>')
@requires_auth
def update_points(v_id, action):
    v = Volunteer.query.get_or_404(v_id)
    if action == 'add': v.points += 10
    elif action == 'sub': 
        v.points -= 10
        if v.points < 0: v.points = 0
    db.session.commit()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
