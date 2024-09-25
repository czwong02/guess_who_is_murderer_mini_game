from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import random
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///games.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Set an admin password (you can change this to any password you want)
ADMIN_PASSWORD = 'password_1234'

# Define a model for the game records
class Game(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # Unique game ID
    num_players = db.Column(db.Integer, nullable=False)
    num_murderers = db.Column(db.Integer, nullable=False)
    roles = db.Column(db.Text, nullable=False)  # Store roles as a string
    players = db.Column(db.Text, nullable=False)  # Store players as a string

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()  # This will create tables based on your models

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        num_players = int(request.form['players'])
        num_murderers = int(request.form['murderers'])
        game_id = str(uuid.uuid4())
        roles = ['Murderer'] * num_murderers + ['Citizen'] * (num_players - num_murderers)
        random.shuffle(roles)

        # Save to database
        new_game = Game(id=game_id, num_players=num_players, num_murderers=num_murderers,
                        roles=','.join(roles), players=','.join([''] * num_players))  # Empty names initially
        db.session.add(new_game)
        db.session.commit()
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
    
    games = Game.query.all()  # Fetch all game records from the database
    return render_template('admin_records.html', games=games)

@app.route('/links/<game_id>')
def display_links(game_id):
    game = Game.query.filter_by(id=game_id).first()  # Fetch the game by ID
    if game:
        players = game.players.split(',')  # Split players string into list
        game_links = [url_for('player', game_id=game_id, player_id=i, _external=True) for i in range(len(players))]
        return render_template('links.html', game_links=game_links)
    return "Game not found!", 404

@app.route('/admin/clear_records', methods=['POST'])
def clear_records():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Clear all game records
    db.session.query(Game).delete()
    db.session.commit()
    flash('All game records have been cleared.', 'success')
    return redirect(url_for('admin_records'))

@app.route('/player/<game_id>/<int:player_id>', methods=['GET', 'POST'])
def player(game_id, player_id):
    game = Game.query.filter_by(id=game_id).first()  # Fetch the game by ID
    if game:
        players = game.players.split(',')  # Convert players string back to a list
        if player_id < len(players):
            if request.method == 'POST':
                name = request.form['name']
                if not players[player_id]:  # First time entry
                    players[player_id] = name  # Assign name
                    roles = game.roles.split(',')  # Split roles string into list
                    assigned_role = roles[player_id]  # Assign role based on player_id
                    players[player_id] = {'name': name, 'role': assigned_role}  # Store name and role
                    game.roles = ','.join(roles)  # Update roles in the game record
                    db.session.commit()
                
                player_role = players[player_id]['role']
                return render_template('player.html', role=player_role, name=name)
            return render_template('enter_name.html')
    return "Invalid link!", 404

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

if __name__ == '__main__':
    app.run(debug=True)
