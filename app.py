print("Flask app is starting...")
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os, json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

USER_DATA_FILE = 'data/users.json'
BOSS_DATA_FILE = 'data/boss_users.json'
TASK_DATA_FILE = 'data/tasks.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# --- Helper Functions ---
def load_users():
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w') as f:
            json.dump([], f)
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def find_user(username):
    return next((u for u in load_users() if u['username'] == username), None)

def load_tasks():
    if not os.path.exists(TASK_DATA_FILE):
        with open(TASK_DATA_FILE, 'w') as f:
            json.dump([], f)
    with open(TASK_DATA_FILE, 'r') as f:
        return json.load(f)

def save_tasks(data):
    with open(TASK_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_boss_users():
    if not os.path.exists(BOSS_DATA_FILE):
        with open(BOSS_DATA_FILE, 'w') as f:
            json.dump([], f)
    with open(BOSS_DATA_FILE, 'r') as f:
        return json.load(f)

def save_boss_users(data):
    with open(BOSS_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# --- User Routes ---
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        department = request.form['department']
        id_card = request.form['id_card']
        photo = request.files['photo']

        if find_user(username):
            flash("Username already exists.")
            return redirect(url_for('signup'))

        filename = secure_filename(photo.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)

        new_user = {
            'username': username,
            'password': password,
            'role': role,
            'department': department,
            'id_card': id_card,
            'photo': photo_path
        }

        users = load_users()
        users.append(new_user)
        save_users(users)

        flash('Signup successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = find_user(username)
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = find_user(session['username'])
    return render_template('dashboard.html', user=user)

@app.route('/dashboard/home')
def dashboard_home():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = find_user(session['username'])
    all_tasks = load_tasks()
    user_tasks = [t for t in all_tasks if t['username'] == session['username']]
    completed = sum(1 for t in user_tasks if t['status'] == 'Completed')
    pending = sum(1 for t in user_tasks if t['status'] == 'Pending')

    return render_template('dashboard_home.html',
                           user=user,
                           all_tasks=user_tasks,
                           completed=completed,
                           pending=pending)

@app.route('/logout')
def user_logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('login'))

@app.route('/task/entry', methods=['GET', 'POST'])
def task_entry():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        task_ids = request.form.getlist('task_id')
        descriptions = request.form.getlist('description')
        clients = request.form.getlist('client')
        locations = request.form.getlist('location')
        dates = request.form.getlist('date')
        statuses = request.form.getlist('status')

        all_tasks = load_tasks()
        submitted_locations = []

        for i in range(len(task_ids)):
            if all([task_ids[i], descriptions[i], clients[i], locations[i], dates[i]]):
                task = {
                    'username': session['username'],
                    'task_id': task_ids[i],
                    'description': descriptions[i],
                    'client': clients[i],
                    'location': locations[i],
                    'date': dates[i],
                    'status': statuses[i]
                }
                all_tasks.append(task)
                if dates[i] == datetime.today().strftime('%Y-%m-%d'):
                    submitted_locations.append({'username': session['username'], 'location': locations[i]})

        save_tasks(all_tasks)
        session['recent_locations'] = submitted_locations
        flash("Tasks submitted successfully!")
        return redirect(url_for('dashboard_home'))

    return render_template('task_entry.html', user=session['username'])

@app.route('/task/pending')
def view_pending():
    if 'username' not in session:
        return redirect(url_for('login'))

    tasks = load_tasks()
    user_tasks = [t for t in tasks if t['username'] == session['username'] and t['status'] == 'Pending']
    return render_template('task_view.html', tasks=user_tasks, title="Pending Tasks")

@app.route('/task/completed')
def view_completed():
    if 'username' not in session:
        return redirect(url_for('login'))

    tasks = load_tasks()
    user_tasks = [t for t in tasks if t['username'] == session['username'] and t['status'] == 'Completed']
    return render_template('task_view.html', tasks=user_tasks, title="Completed Tasks")

@app.route('/task/history', methods=['GET', 'POST'])
def view_history():
    if 'username' not in session:
        return redirect(url_for('login'))

    tasks = load_tasks()
    user_tasks = [t for t in tasks if t['username'] == session['username']]
    filtered_tasks = user_tasks

    if request.method == 'POST':
        ft = request.form['filter_type']
        if ft == 'day':
            val = request.form['filter_day']
            filtered_tasks = [t for t in user_tasks if t['date'] == val]
        elif ft == 'month':
            val = request.form['filter_month']
            filtered_tasks = [t for t in user_tasks if t['date'][:7] == val]
        elif ft == 'year':
            val = request.form['filter_year']
            filtered_tasks = [t for t in user_tasks if t['date'][:4] == val]

    return render_template('task_history.html', tasks=filtered_tasks)

@app.route('/task/update/<int:index>', methods=['POST'])
def update_task(index):
    if 'username' not in session:
        return redirect(url_for('login'))

    tasks = load_tasks()
    user_tasks = [t for t in tasks if t['username'] == session['username']]
    if index < len(user_tasks):
        task = user_tasks[index]
        real_index = tasks.index(task)
        tasks[real_index].update({
            'task_id': request.form['task_id'],
            'description': request.form['description'],
            'client': request.form['client'],
            'date': request.form['date'],
            'status': request.form['status']
        })
        save_tasks(tasks)
        flash("Task updated.")
    return redirect(url_for('view_history'))

@app.route('/task/delete/<int:index>')
def delete_task(index):
    if 'username' not in session:
        return redirect(url_for('login'))

    tasks = load_tasks()
    user_tasks = [t for t in tasks if t['username'] == session['username']]
    if index < len(user_tasks):
        task_to_delete = user_tasks[index]
        tasks.remove(task_to_delete)
        save_tasks(tasks)
        flash("Task deleted.")
    return redirect(url_for('view_history'))

# --- Boss Routes ---
@app.route('/boss/signup', methods=['GET', 'POST'])
def boss_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        boss_users = load_boss_users()

        if any(b['username'] == username for b in boss_users):
            flash("Boss username already exists.")
            return redirect(url_for('boss_signup'))

        boss_users.append({'username': username, 'password': password})
        save_boss_users(boss_users)
        flash('Boss account created.')
        return redirect(url_for('boss_login'))

    return render_template('boss_signup.html')

@app.route('/boss/login', methods=['GET', 'POST'])
def boss_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        boss_users = load_boss_users()

        boss = next((b for b in boss_users if b['username'] == username and b['password'] == password), None)
        if boss:
            session['boss'] = username
            return redirect(url_for('boss_dashboard'))

        flash("Invalid boss credentials.")
    return render_template('boss_login.html')

@app.route('/boss/dashboard', methods=['GET', 'POST'])
def boss_dashboard():
    if 'boss' not in session:
        return redirect(url_for('boss_login'))

    boss_username = session.get('boss')  # ✅ This will be available as {{ boss }} in template

    tasks = load_tasks()
    today = datetime.today().strftime('%Y-%m-%d')
    today_locations = []
    seen_users = set()

    for task in tasks:
        if task.get('date') == today and task.get('location') and task.get('username') not in seen_users:
            today_locations.append({'username': task['username'], 'location': task['location']})
            seen_users.add(task['username'])

    clients = sorted(set(t['client'] for t in tasks if t.get('client')))
    users = sorted(set(t['username'] for t in tasks))

    filtered_tasks = tasks
    if request.method == 'POST':
        ft = request.form.get('filter_type')
        client = request.form.get('filter_client')
        user = request.form.get('filter_user')

        if ft == 'day':
            val = request.form.get('filter_day')
            filtered_tasks = [t for t in filtered_tasks if t['date'] == val]
        elif ft == 'month':
            val = request.form.get('filter_month')
            filtered_tasks = [t for t in filtered_tasks if t['date'][:7] == val]
        elif ft == 'year':
            val = request.form.get('filter_year')
            filtered_tasks = [t for t in filtered_tasks if t['date'][:4] == val]

        if client and client != 'all':
            filtered_tasks = [t for t in filtered_tasks if t['client'] == client]
        if user and user != 'all':
            filtered_tasks = [t for t in filtered_tasks if t['username'] == user]

    user_tasks_map = {}
    for task in filtered_tasks:
        user_tasks_map.setdefault(task['username'], []).append(task)

    return render_template(
        'boss_dashboard.html',
        today_locations=today_locations,
        clients=clients,
        users=users,
        user_tasks_map=user_tasks_map,
        boss=boss_username  # ✅ Fix
    )
@app.route('/boss/logout')
def boss_logout():
    session.pop('boss', None)
    flash("Boss logged out.")
    return redirect(url_for('boss_login'))

# --- Run ---
if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))