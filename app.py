from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'super_eco_secret_key_123'

# Умное подключение: если есть облачная база - берем ее, если нет - создаем локальную
db_url = os.environ.get('DATABASE_URL', 'sqlite:///volunteers.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    motivation = db.Column(db.String(300))
    points = db.Column(db.Integer, default=10)
    is_blocked = db.Column(db.Boolean, default=False)
    time_joined = db.Column(db.String(20))

with app.app_context():
    db.create_all()

EVENT_INFO = {
    "title": "Эко-десант: Очистка парка",
    "date": "2026-05-20 10:00:00",
    "location": "г. Фергана, Центральный парк (вход у фонтана)",
    "description": "Присоединяйся к нам! За регистрацию даем 10 баллов, за участие — 50 баллов."
}

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html', event=EVENT_INFO)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    
    if not name or not phone:
        flash('Имя и телефон обязательны!', 'error')
        return redirect(url_for('index'))

    existing = Volunteer.query.filter_by(phone=phone).first()
    if existing:
        flash('Этот номер уже зарегистрирован. Войдите ниже!', 'error')
        return redirect(url_for('index'))

    new_v = Volunteer(name=name, phone=phone, motivation=email, time_joined=datetime.now().strftime("%H:%M"))
    db.session.add(new_v)
    db.session.commit()
    
    session['user_id'] = new_v.id
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    phone = request.form.get('login_phone')
    user = Volunteer.query.filter_by(phone=phone).first()
    if user:
        if user.is_blocked:
            flash('Ваш аккаунт заблокирован администратором.', 'error')
            return redirect(url_for('index'))
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    
    flash('Номер не найден. Зарегистрируйтесь!', 'error')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user = Volunteer.query.get(session['user_id'])
    if not user or user.is_blocked:
        session.pop('user_id', None)
        return redirect(url_for('index'))
    
    # Берем топ-5 волонтеров для доски почета
    top_volunteers = Volunteer.query.filter_by(is_blocked=False).order_by(Volunteer.points.desc()).limit(5).all()
        
    return render_template('dashboard.html', user=user, event=EVENT_INFO, top_volunteers=top_volunteers)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if request.args.get('key') != 'admin123':
        return "Доступ запрещен! Введите правильный ключ в ссылку.", 403
    all_volunteers = Volunteer.query.order_by(Volunteer.points.desc()).all()
    return render_template('admin.html', volunteers=all_volunteers)

@app.route('/admin/points/<int:v_id>/<int:amount>')
def add_points(v_id, amount):
    if request.args.get('key') != 'admin123': return "Доступ запрещен!", 403
    v = Volunteer.query.get(v_id)
    if v:
        v.points += amount
        db.session.commit()
    return redirect(url_for('admin', key='admin123'))

@app.route('/admin/block/<int:v_id>')
def toggle_block(v_id):
    if request.args.get('key') != 'admin123': return "Доступ запрещен!", 403
    v = Volunteer.query.get(v_id)
    if v:
        v.is_blocked = not v.is_blocked
        db.session.commit()
    return redirect(url_for('admin', key='admin123'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
