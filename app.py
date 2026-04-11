import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ultra_secret_key_for_eco_project'

# --- БАЗА ДАННЫХ ---
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///eco_project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- МОДЕЛИ ---
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
    summary = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    date_added = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d.%m.%Y"))

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ И СТАТЕЙ ---
with app.app_context():
    # Если на Render будет ошибка 500 из-за старой базы, 
    # раскомментируй строку ниже (убери решетку) на ОДИН запуск:
    # db.drop_all() 
    
    db.create_all()
    
    # Автоматически добавляем статьи, если база пустая
    if not Article.query.first():
        art1 = Article(
            title="🌳 Почему Фергане нужны деревья?",
            summary="Деревья — это легкие нашего региона. Узнайте, как одно посаженное дерево влияет на микроклимат города.",
            content="Озеленение городских пространств снижает температуру воздуха летом на 2-4 градуса. В условиях жаркого климата Узбекистана деревья не просто создают тень, они фильтруют пыль и вырабатывают кислород. Присоединяйтесь к нашим акциям по посадке саженцев — это инвестиция в здоровье будущих поколений!",
            image_url="https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?q=80&w=800"
        )
        art2 = Article(
            title="💧 Вода — источник жизни. Как её сберечь?",
            summary="Загрязнение рек пластиком и отходами достигло критической отметки. Что может сделать каждый из нас?",
            content="Пластиковые бутылки разлагаются более 400 лет, выделяя микропластик в воду, которую мы пьем. Наша недавняя акция по уборке берегов показала: 80% мусора — это одноразовый пластик. Отказ от пластиковых пакетов и сортировка отходов дома — первый шаг к чистым водоемам.",
            image_url="https://images.unsplash.com/photo-1506450226056-a05d8f61e893?q=80&w=800"
        )
        art3 = Article(
            title="♻️ Правила сортировки мусора для новичков",
            summary="Сортировать отходы проще, чем кажется. Разбираем основные виды пластика и бумаги.",
            content="Начните с простого: заведите отдельную коробку для макулатуры (бумага, картон) и пакет для чистых пластиковых бутылок (PET). Смятая бутылка занимает в 3 раза меньше места! Сдавая отходы на переработку, вы не только спасаете природу, но и зарабатываете эко-баллы в нашей системе.",
            image_url="https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?q=80&w=800"
        )
        db.session.add_all([art1, art2, art3])
        db.session.commit()

# --- МАРШРУТЫ ---

@app.route('/')
def index():
    # ВОТ ОНО: решение проблемы с ошибкой 500!
    event_data = {"title": "Чистая Фергана"}
    
    if 'user_id' in session:
        user = Volunteer.query.get(session['user_id'])
        if user:
            articles = Article.query.order_by(Article.id.desc()).all()
            return render_template('home_member.html', user=user, articles=articles, event=event_data)
        else:
            session.pop('user_id', None) # Если юзер удален
            
    return render_template('index.html', event=event_data)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    phone = request.form.get('phone')
    motivation = request.form.get('motivation')
    
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
    if 'user_id' not in session: return redirect(url_for('index'))
    user = Volunteer.query.get(session['user_id'])
    leaders = Volunteer.query.order_by(Volunteer.points.desc()).limit(5).all()
    return render_template('dashboard.html', user=user, leaders=leaders)

@app.route('/article/<int:article_id>')
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('article_detail.html', article=article)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

    # --- АДМИН-ПАНЕЛЬ ---
@app.route('/admin')
def admin_panel():
    key = request.args.get('key')
    if key != 'admin123':
        return "Доступ закрыт", 403
    
    # Загружаем всех волонтеров, чтобы ты мог дать им баллы
    volunteers = Volunteer.query.order_by(Volunteer.points.desc()).all()
    total_points = sum(v.points for v in volunteers) if volunteers else 0
    
    return render_template('admin.html', volunteers=volunteers, total_points=total_points)

@app.route('/add_points/<int:user_id>', methods=['POST'])
def add_points(user_id):
    key = request.args.get('key')
    if key != 'admin123':
        return "Доступ закрыт", 403
        
    user = Volunteer.query.get_or_404(user_id)
    points_to_add = int(request.form.get('points', 0))
    user.points += points_to_add
    db.session.commit()
    
    return redirect(url_for('admin_panel', key='admin123'))
    if __name__ == '__main__':
    app.run(debug=True)
