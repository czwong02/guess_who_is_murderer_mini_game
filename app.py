from flask import Flask, render_template, redirect, request, session, url_for
import random, uuid

app = Flask(__name__)
app.secret_key = 'some_secret_key'

players = {}
roles = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if request.method == 'POST':
        num_players = int(request.form['players'])
        num_murderers = int(request.form['murderers'])
        assign_roles(num_players, num_murderers)
        return redirect('/links')
    return render_template('admin.html')

def assign_roles(num_players, num_murderers):
    global roles, players
    roles = ['Murderer'] * num_murderers + ['Citizen'] * (num_players - num_murderers)
    random.shuffle(roles)
    players = {str(uuid.uuid4()): {'name': None, 'role': None} for _ in range(num_players)}  # Generate unique IDs

@app.route('/links')
def display_links():
    game_links = [url_for('player', player_id=player_id, _external=True) for player_id in players.keys()]
    return render_template('links.html', game_links=game_links)

@app.route('/player/<player_id>', methods=['GET', 'POST'])
def player(player_id):
    if player_id in players:
        if request.method == 'POST':
            name = request.form['name']
            if players[player_id]['name'] is None:  # First time entry
                players[player_id]['name'] = name
                players[player_id]['role'] = roles.pop()  # Assign a random role
            
            player_role = players[player_id]['role']
            return render_template('player.html', role=player_role, name=name)
        return render_template('enter_name.html')
    return "Invalid link!", 404

@app.route('/admin/records')
def show_records():
    return render_template('records.html', players=players)

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

if __name__ == '__main__':
    app.run(debug=True)
