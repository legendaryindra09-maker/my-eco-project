from flask import Flask, render_template, request, redirect
from datetime import datetime
import os

app = Flask(__name__)

EVENT_INFO = {
    "title": "Эко-десант: Очистка парка",
    "date": "2026-05-20 10:00:00",
    "location": "Центральный парк, главный вход",
    "description": "Собираемся, чтобы очистить зону отдыха. Инвентарь выдаем!"
}

volunteers = []

@app.route('/')
def index():
    return render_template('index.html', event=EVENT_INFO)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    
    if name and phone and email:
        volunteers.append({
            "name": name, 
            "phone": phone, 
            "message": email,
            "time": datetime.now().strftime("%H:%M")
        })
        return redirect('/admin')
    return "Заполни все поля!", 400

@app.route('/admin')
def admin():
    return render_template('admin.html', volunteers=volunteers)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
