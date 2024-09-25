from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import random
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key

# Set an admin password (you can change this to any password you want)
ADMIN_PASSWORD = 'password_1234'

# Dictionary to store game instances
games = {}

def create_game(num_players, num_murderers):
    game_id = str(uuid.uuid4())  # Unique identifier for each game
    roles = ['Murderer'] * num_murderers + ['Citizen'] * (num_players - num_murderers)
    random.shuffle(roles)
    games[game_id] = {
        'roles': roles,
        'players': {str(uuid.uuid4()): {'name': None, 'role': None} for _ in range(num_players)}
    }
    return game_id

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        num_players = int(request.form['players'])
        num_murderers = int(request.form['murderers'])
        game_id = create_game(num_players, num_murderers)
        return redirect(url_for('display_links', game_id=game_id))
    return render_template('admin.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_records'))
        else:
            flash('Incorrect password. Please try again.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/records')
def admin_records():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_records.html', games=games)

@app.route('/links/<game_id>')
def display_links(game_id):
    game = games.get(game_id)
    if game:
        game_links = [url_for('player', game_id=game_id, player_id=player_id, _external=True) for player_id in game['players'].keys()]
        return render_template('links.html', game_links=game_links)
    return "Game not found!", 404

@app.route('/player/<game_id>/<player_id>', methods=['GET', 'POST'])
def player(game_id, player_id):
    game = games.get(game_id)
    if game and player_id in game['players']:
        if request.method == 'POST':
            name = request.form['name']
            if game['players'][player_id]['name'] is None:  # First time entry
                game['players'][player_id]['name'] = name
                game['players'][player_id]['role'] = game['roles'].pop()  # Assign a random role
            
            player_role = game['players'][player_id]['role']
            return render_template('player.html', role=player_role, name=name)
        return render_template('enter_name.html')
    return "Invalid link!", 404

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

if __name__ == '__main__':
    app.run(debug=True)
