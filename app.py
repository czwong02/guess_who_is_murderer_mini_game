from flask import Flask, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, firestore
import os
import random
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Set an admin password (you can change this to any password you want)
ADMIN_PASSWORD = 'password_1234'

# Initialize Firebase Admin SDK
cred = credentials.Certificate('guess-who-is-murderer-game-firebase-adminsdk-sglzn-dbd5559f79.json')  # Download this file from Firebase Console
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/clear_records', methods=['POST'])
def clear_records():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Clear all game records from Firestore
    games_ref = db.collection('games')
    docs = games_ref.stream()  # Get all documents in the 'games' collection

    # Delete each document
    for doc in docs:
        games_ref.document(doc.id).delete()
    
    flash('All game records have been cleared.', 'success')
    return redirect(url_for('admin_records'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        num_players = int(request.form['players'])
        num_murderers = int(request.form['murderers'])
        game_id = str(uuid.uuid4())
        roles = ['Murderer'] * num_murderers + ['Citizen'] * (num_players - num_murderers)
        random.shuffle(roles)

        # Save to Firestore
        game_data = {
            'num_players': num_players,
            'num_murderers': num_murderers,
            'roles': roles,
            'players': {f'player_{i}': {'name': '', 'role': roles[i]} for i in range(num_players)}
        }
        db.collection('games').document(game_id).set(game_data)

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
    
    games_ref = db.collection('games')
    games = games_ref.stream()  # Fetch all game records from Firestore

    return render_template('admin_records.html', games=games)

@app.route('/links/<game_id>')
def display_links(game_id):
    game_ref = db.collection('games').document(game_id)
    game = game_ref.get()
    if game.exists:
        game_data = game.to_dict()
        game_links = [url_for('player', game_id=game_id, player_id=player_id, _external=True) for player_id in game_data['players'].keys()]
        return render_template('links.html', game_links=game_links)
    return "Game not found!", 404

@app.route('/player/<game_id>/<player_id>', methods=['GET', 'POST'])
def player(game_id, player_id):
    game_ref = db.collection('games').document(game_id)
    game = game_ref.get()
    if game.exists:
        game_data = game.to_dict()
        if player_id in game_data['players']:
            if request.method == 'POST':
                name = request.form['name']
                if game_data['players'][player_id]['name'] == '':  # First time entry
                    game_data['players'][player_id]['name'] = name
                    game_data['players'][player_id]['role'] = game_data['roles'].pop()  # Assign a random role
                    game_ref.set(game_data)  # Update Firestore with new player name and role
                
                player_role = game_data['players'][player_id]['role']
                return render_template('player.html', role=player_role, name=name)
            return render_template('enter_name.html')
    return "Invalid link!", 404

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

if __name__ == '__main__':
    app.run(debug=True)
