import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Секретный ключ нужен для работы всплывающих сообщений (flash)
app.config['SECRET_KEY'] = 'super-secret-key-123'

# Настройка базы данных
# Если мы на Render, он создаст файл в текущей папке
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'participants.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модель участника (таблица в базе данных)
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Participant {self.name}>'

# Автоматическое создание базы данных при запуске
with app.app_context():
    db.create_all()

# ГЛАВНАЯ СТРАНИЦА (Форма регистрации)
@app.route('/')
def index():
    return render_template('index.html')

# ОБРАБОТКА ФОРМЫ
@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    if name and email and phone:
        new_participant = Participant(name=name, email=email, phone=phone)
        try:
            db.session.add(new_participant)
            db.session.commit()
            return "<h1>Успешно!</h1><p>Спасибо за регистрацию. <a href='/'>Вернуться назад</a></p>"
        except Exception as e:
            return f"Произошла ошибка при сохранении: {e}"
    
    return "Пожалуйста, заполни все поля! <a href='/'>Назад</a>"

# СТРАНИЦА АДМИНА (Список участников)
@app.route('/admin')
def admin():
    # Получаем всех из базы данных
    all_participants = Participant.query.all()
    
    # Чтобы не создавать новый HTML-файл, я выведу список простым текстом в красивой обертке
    html_output = """
    <style>
        body { font-family: sans-serif; padding: 40px; background: #f4f4f4; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #009879; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .back { margin-bottom: 20px; display: inline-block; text-decoration: none; color: #009879; font-weight: bold; }
    </style>
    <a href="/" class="back">← На главную</a>
    <h2>Список зарегистрированных волонтеров</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Имя</th>
            <th>Email</th>
            <th>Телефон</th>
        </tr>
    """
    
    for p in all_participants:
        html_output += f"<tr><td>{p.id}</td><td>{p.name}</td><td>{p.email}</td><td>{p.phone}</td></tr>"
    
    html_output += "</table>"
    
    if not all_participants:
        return "<h1>Участников пока нет</h1><a href='/'>Назад</a>"
        
    return html_output

if __name__ == '__main__':
    # На Render порт задается автоматически, но для локальной разработки оставим 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)