from flask import Flask, render_template, request, redirect
from datetime import datetime

app = Flask(__name__)

# Данные о предстоящем ивенте (можешь менять здесь)
EVENT_INFO = {
    "title": "Большая уборка берега",
    "date": "2026-05-20 10:00:00",
    "location": "Центральный парк, вход со стороны реки",
    "description": "Очищаем зону отдыха от пластика и мусора. Инвентарь выдаем!"
}

volunteers = []

@app.route('/')
def index():
    # Считаем время до ивента
    event_date = datetime.strptime(EVENT_INFO['date'], "%2026-%m-%d %H:%M:%S")
    return render_template('index.html', event=EVENT_INFO)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email') # Это поле для мотивации
    
    if name and phone and email:
        volunteers.append({
            "name": name, 
            "phone": phone, 
            "message": email,
            "time": datetime.now().strftime("%H:%M")
        })
        return render_template('success.html')
    return "Пожалуйста, заполни все поля! <a href='/'>Назад</a>", 400

@app.route('/admin')
def admin():
    return render_template('admin.html', volunteers=volunteers)

if __name__ == '__main__':
    app.run(debug=True)
