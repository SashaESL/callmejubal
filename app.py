from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import csv
import io
import os
import random
import json
import pyttsx3
import threading
import secrets
from flask_mail import Mail, Message

app = Flask(__name__)
# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'callmejubal@gmail.com')
app.config['MAIL_PASSWORD'] = 'ijsq xltn qkvu xfse'
mail = Mail(app)
app.secret_key = 'MbvyK2z3xzzC9ne4p4RB4mGzF3Q9yLg8eKeLDBCbxtA'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# ------------------------------------------------------------
# USER MODEL
# ------------------------------------------------------------
class ResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='reset_tokens')
    
    def is_valid(self):
        return datetime.utcnow() < self.expires_at

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
    definition = db.Column(db.Text)  # ← ADD THIS!
    category = db.Column(db.String(100))
    folder = db.Column(db.String(100), default='general')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    correct_count = db.Column(db.Integer, default=0)
    wrong_count = db.Column(db.Integer, default=0)
    last_practiced = db.Column(db.DateTime)
    
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
            'definition': self.definition,  # ← ADD THIS!
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
# EMAIL FUNCTION
# ------------------------------------------------------------
def send_reset_email(email, token):
    reset_url = url_for('reset_password', token=token, _external=True)
    try:
        msg = Message('Password Reset - Call Me Jubal',
                      sender='noreply@callmejubal.com',
                      recipients=[email])
        msg.body = f'''To reset your password, click the link below:

{reset_url}

If you didn't request this, please ignore this email.

This link will expire in 1 hour.
'''
        mail.send(msg)
        print(f"Reset email sent to {email}")
    except Exception as e:
        print(f"Email error: {e}")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists!', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email, folder='general')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        # --------------------------------------------
        # ADD 9-LANGUAGE TERMS FOR NEW USER
        # --------------------------------------------
        all_terms = [
            {
                'english': 'blood pressure',
                'russian': 'кровяное давление',
                'spanish': 'presión arterial',
                'arabic': 'ضغط الدم',
                'french': 'tension artérielle',
                'german': 'Blutdruck',
                'chinese': '血压',
                'thai': 'ความดันโลหิต',
                'filipino': 'presyon ng dugo',
                'category': 'vitals',
                'definition': 'Force of blood against artery walls'
            },
            {
                'english': 'heart attack',
                'russian': 'инфаркт',
                'spanish': 'ataque al corazón',
                'arabic': 'نوبة قلبية',
                'french': 'crise cardiaque',
                'german': 'Herzinfarkt',
                'chinese': '心脏病发作',
                'thai': 'หัวใจวาย',
                'filipino': 'atake sa puso',
                'category': 'emergency',
                'definition': 'Blockage of blood flow to the heart'
            },
            {
                'english': 'fever',
                'russian': 'лихорадка',
                'spanish': 'fiebre',
                'arabic': 'حمى',
                'french': 'fièvre',
                'german': 'Fieber',
                'chinese': '发烧',
                'thai': 'ไข้',
                'filipino': 'lagnat',
                'category': 'symptom',
                'definition': 'Body temperature above normal'
            },
            {
                'english': 'headache',
                'russian': 'головная боль',
                'spanish': 'dolor de cabeza',
                'arabic': 'صداع',
                'french': 'maux de tête',
                'german': 'Kopfschmerzen',
                'chinese': '头痛',
                'thai': 'ปวดหัว',
                'filipino': 'sakit ng ulo',
                'category': 'symptom',
                'definition': 'Pain in the head'
            },
            {
                'english': 'cough',
                'russian': 'кашель',
                'spanish': 'tos',
                'arabic': 'سعال',
                'french': 'toux',
                'german': 'Husten',
                'chinese': '咳嗽',
                'thai': 'ไอ',
                'filipino': 'ubo',
                'category': 'symptom',
                'definition': 'Reflex to clear airways'
            },
            {
                'english': 'diabetes',
                'russian': 'диабет',
                'spanish': 'diabetes',
                'arabic': 'السكري',
                'french': 'diabète',
                'german': 'Diabetes',
                'chinese': '糖尿病',
                'thai': 'โรคเบาหวาน',
                'filipino': 'diabetes',
                'category': 'chronic',
                'definition': 'High blood sugar levels'
            },
            {
                'english': 'allergy',
                'russian': 'аллергия',
                'spanish': 'alergia',
                'arabic': 'حساسية',
                'french': 'allergie',
                'german': 'Allergie',
                'chinese': '过敏',
                'thai': 'ภูมิแพ้',
                'filipino': 'alergiya',
                'category': 'general',
                'definition': 'Immune response to a substance'
            },
            {
                'english': 'prescription',
                'russian': 'рецепт',
                'spanish': 'receta médica',
                'arabic': 'وصفة طبية',
                'french': 'ordonnance',
                'german': 'Verschreibung',
                'chinese': '处方',
                'thai': 'ใบสั่งยา',
                'filipino': 'reseta',
                'category': 'pharmacy',
                'definition': 'Written order for medication'
            },
            {
                'english': 'surgery',
                'russian': 'хирургия',
                'spanish': 'cirugía',
                'arabic': 'جراحة',
                'french': 'chirurgie',
                'german': 'Operation',
                'chinese': '手术',
                'thai': 'การผ่าตัด',
                'filipino': 'operasyon',
                'category': 'procedure',
                'definition': 'Medical operation'
            },
            {
                'english': 'vaccine',
                'russian': 'вакцина',
                'spanish': 'vacuna',
                'arabic': 'لقاح',
                'french': 'vaccin',
                'german': 'Impfstoff',
                'chinese': '疫苗',
                'thai': 'วัคซีน',
                'filipino': 'bakuna',
                'category': 'prevention',
                'definition': 'Substance that stimulates immunity'
            },
            {
                'english': 'Medicare Summary Notice (MSN)',
                'russian': 'Объяснение льгот',
                'spanish': 'Aviso de Resumen de Medicare',
                'arabic': 'إشعار ملخص ميديكير',
                'french': 'Explication des avantages',
                'german': 'Leistungsübersicht',
                'chinese': '医疗保险摘要',
                'thai': 'สรุปสิทธิประโยชน์',
                'filipino': 'Paalala ng mga Benepisyo',
                'category': 'Insurance',
                'definition': 'Explanation of benefits sent to the beneficiary'
            },
            {
                'english': 'Order of Benefit Determination (OBD)',
                'russian': 'Правила определения порядка оплаты',
                'spanish': 'Determinación del Orden de Beneficios',
                'arabic': 'تحديد ترتيب الاستحقاق',
                'french': 'Règles de détermination de l\'ordre',
                'german': 'Regeln zur Bestimmung der Reihenfolge',
                'chinese': '福利确定顺序',
                'thai': 'การกำหนดลำดับสิทธิประโยชน์',
                'filipino': 'Pagpapasiya ng Pagkakasunod-sunod ng Benepisyo',
                'category': 'Insurance',
                'definition': 'Rules that determine order of payment'
            },
            {
                'english': 'Concurrent Review',
                'russian': 'Обоснованность сроков пребывания',
                'spanish': 'Revisión Concurrente',
                'arabic': 'المراجعة المتزامنة',
                'french': 'Vérification des durées de séjour',
                'german': 'Prüfung der Aufenthaltsdauer',
                'chinese': '同时审查',
                'thai': 'การทบทวนระหว่างการรักษา',
                'filipino': 'Pagsusuri habang nasa Ospital',
                'category': 'Insurance',
                'definition': 'Determines if inpatient stay is justified'
            },
            {
                'english': 'Retrospective Review',
                'russian': 'Медицинская необходимость госпитализации',
                'spanish': 'Revisión Retrospectiva',
                'arabic': 'المراجعة بأثر رجعي',
                'french': 'Nécessité médicale de l\'hospitalisation',
                'german': 'Prüfung der Krankenhausaufnahme',
                'chinese': '回顾性审查',
                'thai': 'การทบทวนหลังจำหน่าย',
                'filipino': 'Pagsusuri pagkatapos ng Paglabas',
                'category': 'Insurance',
                'definition': 'Determines if treatment was medically necessary'
            },
            {
                'english': 'Preauthorization',
                'russian': 'Предварительное разрешение',
                'spanish': 'Preautorización',
                'arabic': 'التفويض المسبق',
                'french': 'Pré-autorisation',
                'german': 'Vorautorisierung',
                'chinese': '预先授权',
                'thai': 'การอนุมัติล่วงหน้า',
                'filipino': 'Paunang Awtorisasyon',
                'category': 'Insurance',
                'definition': 'Approval needed before procedure'
            },
            {
                'english': 'Formulary',
                'russian': 'Список лекарств',
                'spanish': 'Formulario',
                'arabic': 'قائمة الأدوية المغطاة',
                'french': 'Liste de médicaments',
                'german': 'Medikamentenliste',
                'chinese': '药品目录',
                'thai': 'บัญชียา',
                'filipino': 'Listahan ng Gamot',
                'category': 'Insurance',
                'definition': 'List of covered drugs'
            },
            {
                'english': 'Copayment',
                'russian': 'Фиксированная оплата',
                'spanish': 'Copago',
                'arabic': 'الدفع المشترك',
                'french': 'Participation fixe',
                'german': 'Zuzahlung',
                'chinese': '共付额',
                'thai': 'การจ่ายร่วม',
                'filipino': 'Co-payment',
                'category': 'Insurance',
                'definition': 'Fixed amount patient pays for service'
            },
            {
                'english': 'Deductible',
                'russian': 'Сумма до начала страховки',
                'spanish': 'Deducible',
                'arabic': 'الخصم',
                'french': 'Franchise',
                'german': 'Selbstbeteiligung',
                'chinese': '免赔额',
                'thai': 'ค่าใช้จ่ายส่วนแรก',
                'filipino': 'Idedusable',
                'category': 'Insurance',
                'definition': 'Amount patient pays before insurance starts'
            },
            {
                'english': 'Coinsurance',
                'russian': 'Процент оплаты после вычета',
                'spanish': 'Coaseguro',
                'arabic': 'التأمين المشترك',
                'french': 'Coassurance',
                'german': 'Krankenversicherungsbeitrag',
                'chinese': '共保',
                'thai': 'การร่วมจ่ายเปอร์เซ็นต์',
                'filipino': 'Ko-insurance',
                'category': 'Insurance',
                'definition': 'Percentage patient pays after deductible'
            },
            {
                'english': 'Out-of-Pocket Maximum',
                'russian': 'Максимальная годовая оплата',
                'spanish': 'Máximo de Gastos de Bolsillo',
                'arabic': 'الحد الأقصى للنفقات الجيبية',
                'french': 'Dépenses maximales de poche',
                'german': 'Maximale Eigenbeteiligung',
                'chinese': '自付费用上限',
                'thai': 'ค่าสูงสุดที่ต้องจ่ายเอง',
                'filipino': 'Maksimum na Gastos sa Sariling Bulsa',
                'category': 'Insurance',
                'definition': 'Maximum patient pays per year'
            },
        ]
        
        for term in all_terms:
            card = Flashcard(
                user_id=new_user.id,
                english=term['english'],
                russian=term['russian'],
                spanish=term['spanish'],
                arabic=term['arabic'],
                french=term['french'],
                german=term['german'],
                chinese=term['chinese'],
                thai=term['thai'],
                filipino=term['filipino'],
                category=term['category'],
                definition=term['definition'],
                folder='general'
            )
            db.session.add(card)
        
        db.session.commit()
        # --------------------------------------------
        
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        flash('Registration successful! Welcome! 9-language terms added!', 'success')
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

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('No account found with that email.', 'danger')
            return redirect(url_for('forgot_password'))
        
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        reset_token = ResetToken(user_id=user.id, token=token, expires_at=expires_at)
        db.session.add(reset_token)
        db.session.commit()
        
        send_reset_email(user.email, token)
        
        flash('Password reset link sent to your email!', 'success')
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = ResetToken.query.filter_by(token=token).first()
    
    if not reset_token or not reset_token.is_valid():
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        user = User.query.get(reset_token.user_id)
        user.set_password(password)
        
        db.session.delete(reset_token)
        db.session.commit()
        
        flash('Password reset successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

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
# MAIN ROUTES
# ------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('public.html')
    
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
        
        # Check if file is CSV or Excel
        if file.filename.endswith('.csv'):
            # Handle CSV
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.reader(stream)
            headers = [h.lower().strip() for h in next(csv_input)]
            rows = list(csv_input)
            
        elif file.filename.endswith('.xlsx'):
            # Handle Excel
            try:
                import openpyxl
                workbook = openpyxl.load_workbook(file.stream)
                sheet = workbook.active
                headers = [str(cell.value).lower().strip() if cell.value else '' for cell in sheet[1]]
                rows = []
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    rows.append(row)
            except ImportError:
                return render_template('upload.html', error="Excel support not installed. Please install openpyxl.", user=user)
            except Exception as e:
                return render_template('upload.html', error=f"Error reading Excel file: {str(e)}", user=user)
        else:
            return render_template('upload.html', error="Please upload a CSV or Excel (.xlsx) file!", user=user)
        
        # Check if 'english' column exists
        if 'english' not in headers:
            return render_template('upload.html', error="File must have an 'english' column!", user=user)
        
        count = 0
        for row in rows:
            row_dict = dict(zip(headers, row))
            
            if not row_dict.get('english', '').strip():
                continue
            
            card = Flashcard(
                user_id=user_id,
                folder=user.folder,
                english=str(row_dict.get('english', '')).strip(),
                russian=str(row_dict.get('russian', '')).strip(),
                spanish=str(row_dict.get('spanish', '')).strip(),
                arabic=str(row_dict.get('arabic', '')).strip(),
                french=str(row_dict.get('french', '')).strip(),
                german=str(row_dict.get('german', '')).strip(),
                chinese=str(row_dict.get('chinese', '')).strip(),
                thai=str(row_dict.get('thai', '')).strip(),
                filipino=str(row_dict.get('filipino', '')).strip(),
                definition=str(row_dict.get('definition', '')).strip(),
                category=str(row_dict.get('category', 'general')).strip() or 'general'
            )
            db.session.add(card)
            count += 1
        
        db.session.commit()
        return render_template('upload.html', success=True, count=count, filename=file.filename, user=user)
    
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

@app.route('/test')
def test():
    if 'user_id' not in session:
        flash('Please login to take a test!', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('test.html', user=user)

@app.route('/api/test-questions')
def test_questions():
    if 'user_id' not in session:
        return jsonify([])
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    lang = user.language if user and user.language else 'russian'
    cards = Flashcard.query.filter_by(user_id=user_id, folder=user.folder).all()
    
    if not cards:
        return jsonify([])
    
    import random
    selected = random.sample(cards, min(len(cards), 10))
    questions = []
    
    for card in selected:
        translation = getattr(card, lang, card.russian)
        if not translation:
            translation = card.russian
        
        other_cards = [c for c in cards if c.id != card.id]
        wrong_options = []
        
        if other_cards:
            for c in random.sample(other_cards, min(3, len(other_cards))):
                wrong_trans = getattr(c, lang, c.russian)
                if wrong_trans and wrong_trans != translation:
                    wrong_options.append(wrong_trans)
        
        while len(wrong_options) < 3:
            placeholders = ["otra opción", "otra traducción", "opción incorrecta"]
            wrong_options.append(placeholders[len(wrong_options) % 3])
        
        options = [translation] + wrong_options[:3]
        random.shuffle(options)
        
        questions.append({
            'english': card.english,
            'options': options,
            'correct': options.index(translation)
        })
    
    return jsonify(questions)

@app.route('/api/study/<int:card_id>/<lang>/<result>')
def record_result(card_id, lang, result):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    card = Flashcard.query.get_or_404(card_id)
    
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
        definition=row_dict.get('definition', '').strip(),  # ← ADD THIS!
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
    
    if card.user_id != session['user_id']:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    db.session.delete(card)
    db.session.commit()
    return jsonify({'status': 'success'})

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

# ------------------------------------------------------------
# RUN THE APP
# ------------------------------------------------------------
@app.route('/set-language', methods=['POST'])
def set_language():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    data = request.get_json()
    language = data.get('language')
    
    if language not in ['english', 'russian', 'spanish', 'arabic', 'french', 'german', 'chinese', 'thai', 'filipino']:
        return jsonify({'status': 'error', 'message': 'Invalid language'})
    
    user = User.query.get(session['user_id'])
    user.language = language
    session['language'] = language
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': f'Language updated to {language}'})
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)