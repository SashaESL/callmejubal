from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import csv
import io
import os
import random
import json
import pyttsx3
import threading

app = Flask(__name__)
app.secret_key = 'MbvyK2z3xzzC9ne4p4RB4mGzF3Q9yLg8eKeLDBCbxtA'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# ------------------------------------------------------------
# USER MODEL
# ------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    language = db.Column(db.String(20), default='english')
    folder = db.Column(db.String(100), default='general')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'language': self.language,
            'folder': self.folder
        }

# ------------------------------------------------------------
# DATABASE MODEL
# ------------------------------------------------------------
class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    english = db.Column(db.String(200), nullable=False)
    russian = db.Column(db.String(200))
    spanish = db.Column(db.String(200))
    arabic = db.Column(db.String(200))
    french = db.Column(db.String(200))
    german = db.Column(db.String(200))
    chinese = db.Column(db.String(200))
    thai = db.Column(db.String(200))
    filipino = db.Column(db.String(200))
    category = db.Column(db.String(100))
    folder = db.Column(db.String(100), default='general')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    correct_count = db.Column(db.Integer, default=0)
    wrong_count = db.Column(db.Integer, default=0)
    last_practiced = db.Column(db.DateTime)
    
    # Relationship
    user = db.relationship('User', backref='cards')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'english': self.english,
            'russian': self.russian,
            'spanish': self.spanish,
            'arabic': self.arabic,
            'french': self.french,
            'german': self.german,
            'chinese': self.chinese,
            'thai': self.thai,
            'filipino': self.filipino,
            'category': self.category,
            'folder': self.folder,
            'correct_count': self.correct_count,
            'wrong_count': self.wrong_count,
        }

# ------------------------------------------------------------
# INITIALIZE DATABASE
# ------------------------------------------------------------
with app.app_context():
    db.create_all()
    print("✅ Database created! No sample cards added — users will add their own.")

# ------------------------------------------------------------
# AUTHENTICATION ROUTES
# ------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists!', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(username=username, email=email, folder='general')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        # Log them in
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        flash('Registration successful! Welcome!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out!', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        language = request.form.get('language')
        folder = request.form.get('folder')
        if language:
            user.language = language
            session['language'] = language
        if folder:
            user.folder = folder
        db.session.commit()
        flash('Preferences updated!', 'success')
    
    languages = ['english', 'russian', 'spanish', 'arabic', 'french', 'german', 'chinese', 'thai', 'filipino']
    folders = ['general', 'medical', 'insurance', 'legal', 'oncology', 'cardiology', 'emergency']
    return render_template('profile.html', user=user, languages=languages, folders=folders)

# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' not in session:
        # Show public page with login/register buttons
        return render_template('public.html')
    
    # Get user's cards only
    user_id = session['user_id']
    user = User.query.get(user_id)
    cards = Flashcard.query.filter_by(user_id=user_id).all()
    categories = db.session.query(Flashcard.category).distinct().filter_by(user_id=user_id).all()
    categories = [c[0] for c in categories if c[0]]
    
    languages = ['english', 'russian', 'spanish', 'arabic', 'french', 'german', 'chinese', 'thai', 'filipino']
    
    return render_template('index.html', 
                         cards=cards, 
                         categories=categories,
                         languages=languages,
                         username=session.get('username'),
                         user=user)
@app.route('/study')
def study():
    if 'user_id' not in session:
        flash('Please login to study!', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    cards = Flashcard.query.filter_by(user_id=user_id, folder=user.folder).all()
    languages = ['english', 'russian', 'spanish', 'arabic', 'french', 'german', 'chinese', 'thai', 'filipino']
    
    return render_template('study.html', cards=cards, languages=languages, user=user)

@app.route('/api/cards')
def get_cards():
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Flashcard.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Flashcard.english.contains(search) | 
                           Flashcard.russian.contains(search) |
                           Flashcard.spanish.contains(search) |
                           Flashcard.thai.contains(search) |
                           Flashcard.filipino.contains(search))
    
    cards = query.all()
    return jsonify([c.to_dict() for c in cards])

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash('Please login to upload!', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.reader(stream)
            
            headers = [h.lower().strip() for h in next(csv_input)]
            
            if 'english' not in headers:
                return render_template('upload.html', error="CSV must have an 'english' column!", user=user)
            
            count = 0
            for row in csv_input:
                row_dict = dict(zip(headers, row))
                
                if not row_dict.get('english', '').strip():
                    continue
                
                card = Flashcard(
                    user_id=user_id,
                    folder=user.folder,
                    english=row_dict.get('english', '').strip(),
                    russian=row_dict.get('russian', '').strip(),
                    spanish=row_dict.get('spanish', '').strip(),
                    arabic=row_dict.get('arabic', '').strip(),
                    french=row_dict.get('french', '').strip(),
                    german=row_dict.get('german', '').strip(),
                    chinese=row_dict.get('chinese', '').strip(),
                    thai=row_dict.get('thai', '').strip(),
                    filipino=row_dict.get('filipino', '').strip(),
                    category=row_dict.get('category', 'general').strip() or 'general'
                )
                db.session.add(card)
                count += 1
            
            db.session.commit()
            return render_template('upload.html', success=True, count=count, filename=file.filename, user=user)
        else:
            return render_template('upload.html', error="Please upload a CSV file!", user=user)
    
    return render_template('upload.html', user=user)

@app.route('/stats')
def stats():
    if 'user_id' not in session:
        flash('Please login to view stats!', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    total = Flashcard.query.filter_by(user_id=user_id, folder=user.folder).count()
    mastered = Flashcard.query.filter_by(user_id=user_id, folder=user.folder).filter(Flashcard.correct_count >= 3).count()
    needs_review = Flashcard.query.filter_by(user_id=user_id, folder=user.folder).filter(Flashcard.wrong_count > Flashcard.correct_count).count()
    
    categories = db.session.query(
        Flashcard.category, 
        db.func.count(Flashcard.id)
    ).filter_by(user_id=user_id, folder=user.folder).group_by(Flashcard.category).all()
    
    return render_template('stats.html', 
                         total=total,
                         mastered=mastered,
                         needs_review=needs_review,
                         categories=categories,
                         user=user)

@app.route('/api/study/<int:card_id>/<lang>/<result>')
def record_result(card_id, lang, result):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    card = Flashcard.query.get_or_404(card_id)
    
    # Make sure the card belongs to the user
    if card.user_id != session['user_id']:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    if result == 'correct':
        card.correct_count += 1
    else:
        card.wrong_count += 1
    card.last_practiced = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/add', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    card = Flashcard(
        user_id=user_id,
        folder=user.folder,
        english=request.form.get('english', ''),
        russian=request.form.get('russian', ''),
        spanish=request.form.get('spanish', ''),
        arabic=request.form.get('arabic', ''),
        french=request.form.get('french', ''),
        german=request.form.get('german', ''),
        chinese=request.form.get('chinese', ''),
        thai=request.form.get('thai', ''),
        filipino=request.form.get('filipino', ''),
        category=request.form.get('category', 'general')
    )
    db.session.add(card)
    db.session.commit()
    flash('Card added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:card_id>')
def delete_card(card_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    card = Flashcard.query.get_or_404(card_id)
    
    # Make sure the card belongs to the user
    if card.user_id != session['user_id']:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    db.session.delete(card)
    db.session.commit()
    return jsonify({'status': 'success'})
# ------------------------------------------------------------
# RUN THE APP
# ------------------------------------------------------------
@app.route('/api/test-questions')
def test_questions():
    if 'user_id' not in session:
        return jsonify([])
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get user's language (default to russian)
    lang = user.language if user and user.language else 'russian'
    
    # Get cards from user's current folder
    cards = Flashcard.query.filter_by(user_id=user_id, folder=user.folder).all()
    
    if not cards:
        return jsonify([])
    
    import random
    
    # Select up to 10 random cards
    selected = random.sample(cards, min(len(cards), 10))
    questions = []
    
    for card in selected:
        # Get translation in user's language
        translation = getattr(card, lang, card.russian)
        
        # If translation is empty, fallback to russian
        if not translation:
            translation = card.russian
        
        # Get wrong options from other cards in the same folder
        other_cards = [c for c in cards if c.id != card.id]
        wrong_options = []
        
        if other_cards:
            # Get translations from other cards in user's language
            for c in random.sample(other_cards, min(3, len(other_cards))):
                wrong_trans = getattr(c, lang, c.russian)
                if wrong_trans and wrong_trans != translation:
                    wrong_options.append(wrong_trans)
        
        # If we don't have enough wrong options, add some placeholders
        while len(wrong_options) < 3:
            placeholders = [
                "otra opción",
                "otra traducción",
                "opción incorrecta"
            ]
            wrong_options.append(placeholders[len(wrong_options) % 3])
        
        # Build options
        options = [translation] + wrong_options[:3]
        random.shuffle(options)
        
        questions.append({
            'english': card.english,
            'options': options,
            'correct': options.index(translation)
        })
    
    return jsonify(questions)

@app.route('/test')
def test():
    if 'user_id' not in session:
        flash('Please login to take a test!', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('test.html', user=user)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)