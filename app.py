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

premium_terms = [
    {
        'english': 'Acute condition',
        'russian': 'Острое состояние',
        'spanish': 'Condición aguda',
        'arabic': 'حالة حادة',
        'french': 'Affection aiguë',
        'german': 'Akuter Zustand',
        'chinese': '急性状态',
        'thai': 'ภาวะเฉียบพลัน',
        'filipino': 'Kondisyon talamak',
        'category': 'general',
        'definition': 'A condition that develops suddenly'
    },
    {
        'english': 'Adjuvant Therapy',
        'russian': 'Адъювантная терапия',
        'spanish': 'Terapia adyuvante',
        'arabic': 'العلاج المساعد',
        'french': 'Thérapie adjuvante',
        'german': 'Adjuvante Therapie',
        'chinese': '辅助治疗',
        'thai': 'การรักษาเสริม',
        'filipino': 'Terapyong pantulong',
        'category': 'oncology',
        'definition': 'Treatment given after primary treatment'
    },
    {
        'english': 'Amniocentesis',
        'russian': 'Амниоцентез',
        'spanish': 'Amniocentesis',
        'arabic': 'بزل السلى',
        'french': 'Amniocentèse',
        'german': 'Amniozentese',
        'chinese': '羊膜穿刺术',
        'thai': 'การเจาะน้ำคร่ำ',
        'filipino': 'Amniocentesis',
        'category': 'gynecology',
        'definition': 'A procedure to test amniotic fluid'
    },
    {
        'english': 'Anesthesia',
        'russian': 'Анестезия',
        'spanish': 'Anestesia',
        'arabic': 'تخدير',
        'french': 'Anesthésie',
        'german': 'Anästhesie',
        'chinese': '麻醉',
        'thai': 'การวางยาสลบ',
        'filipino': 'Anesthesia',
        'category': 'procedure',
        'definition': 'Medical treatment to prevent pain'
    },
    {
        'english': 'Anti-coagulate',
        'russian': 'Антикоагулянт',
        'spanish': 'Anticoagulante',
        'arabic': 'مضاد التخثر',
        'french': 'Anticoagulant',
        'german': 'Antikoagulans',
        'chinese': '抗凝血剂',
        'thai': 'ยาต้านการแข็งตัวของเลือด',
        'filipino': 'Anticoagulant',
        'category': 'pharmacy',
        'definition': 'Substance that prevents blood clotting'
    },
    {
        'english': 'Anti-histamine',
        'russian': 'Антигистамин',
        'spanish': 'Antihistamínico',
        'arabic': 'مضاد الهيستامين',
        'french': 'Antihistaminique',
        'german': 'Antihistaminikum',
        'chinese': '抗组胺药',
        'thai': 'ยาแก้แพ้',
        'filipino': 'Antihistamine',
        'category': 'pharmacy',
        'definition': 'Substance that blocks histamine'
    },
    {
        'english': 'Anti-inflammatory',
        'russian': 'Противовоспалительное',
        'spanish': 'Antiinflamatorio',
        'arabic': 'مضاد التهاب',
        'french': 'Anti-inflammatoire',
        'german': 'Entzündungshemmer',
        'chinese': '抗炎药',
        'thai': 'ยาต้านการอักเสบ',
        'filipino': 'Anti-namumugâ',
        'category': 'pharmacy',
        'definition': 'Substance that reduces inflammation'
    },
    {
        'english': 'Appendectomy',
        'russian': 'Аппендэктомия',
        'spanish': 'Apendicectomía',
        'arabic': 'استئصال الزائدة',
        'french': 'Appendicectomie',
        'german': 'Appendektomie',
        'chinese': '阑尾切除术',
        'thai': 'การตัดไส้ติ่ง',
        'filipino': 'Appendectomy',
        'category': 'procedure',
        'definition': 'Surgical removal of the appendix'
    },
    {
        'english': 'Appendix',
        'russian': 'Аппендикс',
        'spanish': 'Apéndice',
        'arabic': 'الزائدة',
        'french': 'Appendice',
        'german': 'Blinddarm',
        'chinese': '阑尾',
        'thai': 'ไส้ติ่ง',
        'filipino': 'Appendix',
        'category': 'general',
        'definition': 'A small pouch attached to the large intestine'
    },
    {
        'english': 'Arrhythmia',
        'russian': 'Аритмия',
        'spanish': 'Arritmia',
        'arabic': 'عدم انتظام ضربات القلب',
        'french': 'Arythmie',
        'german': 'Herzrhythmusstörung',
        'chinese': '心律失常',
        'thai': 'ภาวะหัวใจเต้นผิดจังหวะ',
        'filipino': 'Arrhythmia',
        'category': 'cardiology',
        'definition': 'Irregular heart rhythm'
    },
    {
        'english': 'Artery',
        'russian': 'Артерия',
        'spanish': 'Arteria',
        'arabic': 'شريان',
        'french': 'Artère',
        'german': 'Arterie',
        'chinese': '动脉',
        'thai': 'หลอดเลือดแดง',
        'filipino': 'Artery',
        'category': 'anatomy',
        'definition': 'Blood vessel that carries blood away from the heart'
    },
    {
        'english': 'Atherosclerosis',
        'russian': 'Атеросклероз',
        'spanish': 'Aterosclerosis',
        'arabic': 'تصلب الشرايين',
        'french': 'Athérosclérose',
        'german': 'Arteriosklerose',
        'chinese': '动脉粥样硬化',
        'thai': 'ภาวะหลอดเลือดแข็ง',
        'filipino': 'Atherosclerosis',
        'category': 'cardiology',
        'definition': 'Buildup of plaque in the arteries'
    },
    {
        'english': 'Atrophy',
        'russian': 'Атрофия',
        'spanish': 'Atrofia',
        'arabic': 'ضمور',
        'french': 'Atrophie',
        'german': 'Atrophie',
        'chinese': '萎缩',
        'thai': 'การฝ่อ',
        'filipino': 'Atrophy',
        'category': 'general',
        'definition': 'Wasting away or decrease in size'
    },
    {
        'english': 'Barium Swallow',
        'russian': 'Бариевое глотание',
        'spanish': 'Deglución de bario',
        'arabic': 'ابتلاع الباريوم',
        'french': 'Déglutition barytée',
        'german': 'Bariumschluck',
        'chinese': '钡餐',
        'thai': 'การกลืนแบเรียม',
        'filipino': 'Barium swallow',
        'category': 'diagnostics',
        'definition': 'X-ray test of the esophagus and stomach'
    },
    {
        'english': 'Biopsy',
        'russian': 'Биопсия',
        'spanish': 'Biopsia',
        'arabic': 'خزعة',
        'french': 'Biopsie',
        'german': 'Biopsie',
        'chinese': '活检',
        'thai': 'การตรวจชิ้นเนื้อ',
        'filipino': 'Biopsy',
        'category': 'procedure',
        'definition': 'Removal of tissue for examination'
    },
    {
        'english': 'Bipolar Disorder',
        'russian': 'Биполярное расстройство',
        'spanish': 'Trastorno bipolar',
        'arabic': 'الاضطراب ثنائي القطب',
        'french': 'Trouble bipolaire',
        'german': 'Bipolare Störung',
        'chinese': '双相情感障碍',
        'thai': 'โรคไบโพลาร์',
        'filipino': 'Bipolar disorder',
        'category': 'psychiatry',
        'definition': 'Mental health condition with mood swings'
    },
    {
        'english': 'Blood Cell Count',
        'russian': 'Подсчет клеток крови',
        'spanish': 'Conteo de células sanguíneas',
        'arabic': 'تعداد خلايا الدم',
        'french': 'Numération des cellules sanguines',
        'german': 'Blutbild',
        'chinese': '血细胞计数',
        'thai': 'การนับเม็ดเลือด',
        'filipino': 'Blood cell count',
        'category': 'diagnostics',
        'definition': 'Measurement of blood cells'
    },
    {
        'english': 'Bone Marrow',
        'russian': 'Костный мозг',
        'spanish': 'Médula ósea',
        'arabic': 'نخاع العظم',
        'french': 'Moelle osseuse',
        'german': 'Knochenmark',
        'chinese': '骨髓',
        'thai': 'ไขกระดูก',
        'filipino': 'Bone marrow',
        'category': 'anatomy',
        'definition': 'Spongy tissue inside bones'
    },
    {
        'english': 'Bronchitis',
        'russian': 'Бронхит',
        'spanish': 'Bronquitis',
        'arabic': 'التهاب الشعب الهوائية',
        'french': 'Bronchite',
        'german': 'Bronchitis',
        'chinese': '支气管炎',
        'thai': 'หลอดลมอักเสบ',
        'filipino': 'Bronchitis',
        'category': 'respiratory',
        'definition': 'Inflammation of the bronchial tubes'
    },
    {
        'english': 'Bursitis',
        'russian': 'Бурсит',
        'spanish': 'Bursitis',
        'arabic': 'التهاب الجراب',
        'french': 'Bursite',
        'german': 'Schleimbeutelentzündung',
        'chinese': '滑囊炎',
        'thai': 'เบอร์ซาอักเสบ',
        'filipino': 'Bursitis',
        'category': 'orthopedics',
        'definition': 'Inflammation of a bursa'
    },
    {
        'english': 'Carcinoma',
        'russian': 'Карцинома',
        'spanish': 'Carcinoma',
        'arabic': 'سرطانة',
        'french': 'Carcinome',
        'german': 'Karzinom',
        'chinese': '癌',
        'thai': 'มะเร็งชนิดคาร์ซิโนมา',
        'filipino': 'Carcinoma',
        'category': 'oncology',
        'definition': 'Cancer that begins in epithelial tissue'
    },
    {
        'english': 'Cardiologist',
        'russian': 'Кардиолог',
        'spanish': 'Cardiólogo',
        'arabic': 'طبيب قلب',
        'french': 'Cardiologue',
        'german': 'Kardiologe',
        'chinese': '心脏病专家',
        'thai': 'แพทย์โรคหัวใจ',
        'filipino': 'Cardiologist',
        'category': 'cardiology',
        'definition': 'Heart specialist'
    },
    {
        'english': 'Cartilage',
        'russian': 'Хрящ',
        'spanish': 'Cartílago',
        'arabic': 'غضروف',
        'french': 'Cartilage',
        'german': 'Knorpel',
        'chinese': '软骨',
        'thai': 'กระดูกอ่อน',
        'filipino': 'Cartilage',
        'category': 'anatomy',
        'definition': 'Flexible connective tissue'
    },
    {
        'english': 'CAT Scan',
        'russian': 'КТ (компьютерная томография)',
        'spanish': 'Tomografía computarizada',
        'arabic': 'التصوير المقطعي',
        'french': 'Scanner',
        'german': 'CT-Scan',
        'chinese': 'CT扫描',
        'thai': 'การตรวจซีที',
        'filipino': 'CAT scan',
        'category': 'diagnostics',
        'definition': 'Cross-sectional imaging test'
    },
    {
        'english': 'Catheter',
        'russian': 'Катетер',
        'spanish': 'Catéter',
        'arabic': 'قسطرة',
        'french': 'Cathéter',
        'german': 'Katheter',
        'chinese': '导管',
        'thai': 'สายสวน',
        'filipino': 'Catheter',
        'category': 'equipment',
        'definition': 'Tube inserted into the body'
    },
    {
        'english': 'Cervix',
        'russian': 'Шейка матки',
        'spanish': 'Cérvix',
        'arabic': 'عنق الرحم',
        'french': 'Col de l\'utérus',
        'german': 'Gebärmutterhals',
        'chinese': '子宫颈',
        'thai': 'ปากมดลูก',
        'filipino': 'Cervix',
        'category': 'gynecology',
        'definition': 'Lower part of the uterus'
    },
    {
        'english': 'Chemotherapy',
        'russian': 'Химиотерапия',
        'spanish': 'Quimioterapia',
        'arabic': 'العلاج الكيميائي',
        'french': 'Chimiothérapie',
        'german': 'Chemotherapie',
        'chinese': '化疗',
        'thai': 'เคมีบำบัด',
        'filipino': 'Chemotherapy',
        'category': 'oncology',
        'definition': 'Cancer treatment using drugs'
    },
    {
        'english': 'Chronic Condition',
        'russian': 'Хроническое состояние',
        'spanish': 'Condición crónica',
        'arabic': 'حالة مزمنة',
        'french': 'Affection chronique',
        'german': 'Chronische Erkrankung',
        'chinese': '慢性病',
        'thai': 'ภาวะเรื้อรัง',
        'filipino': 'Kondisyon talamak',
        'category': 'general',
        'definition': 'Long-lasting condition'
    },
    {
        'english': 'Cirrhosis',
        'russian': 'Цирроз',
        'spanish': 'Cirrosis',
        'arabic': 'تليف الكبد',
        'french': 'Cirrhose',
        'german': 'Zirrhose',
        'chinese': '肝硬化',
        'thai': 'ตับแข็ง',
        'filipino': 'Cirrhosis',
        'category': 'gastroenterology',
        'definition': 'Scarring of the liver'
    },
    {
        'english': 'Colonoscopy',
        'russian': 'Колоноскопия',
        'spanish': 'Colonoscopia',
        'arabic': 'تنظير القولون',
        'french': 'Coloscopie',
        'german': 'Koloskopie',
        'chinese': '结肠镜检查',
        'thai': 'การส่องกล้องลำไส้ใหญ่',
        'filipino': 'Colonoscopy',
        'category': 'procedure',
        'definition': 'Examination of the colon'
    },
    {
        'english': 'Congenital',
        'russian': 'Врожденный',
        'spanish': 'Congénito',
        'arabic': 'خلقي',
        'french': 'Congénital',
        'german': 'Angeboren',
        'chinese': '先天性',
        'thai': 'แต่กำเนิด',
        'filipino': 'Congenital',
        'category': 'general',
        'definition': 'Present at birth'
    },
    {
        'english': 'Congestive Heart Failure',
        'russian': 'Застойная сердечная недостаточность',
        'spanish': 'Insuficiencia cardíaca congestiva',
        'arabic': 'فشل القلب الاحتقاني',
        'french': 'Insuffisance cardiaque congestive',
        'german': 'Herzinsuffizienz',
        'chinese': '充血性心力衰竭',
        'thai': 'ภาวะหัวใจล้มเหลว',
        'filipino': 'Congestive heart failure',
        'category': 'cardiology',
        'definition': 'Heart cannot pump enough blood'
    },
    {
        'english': 'Consent Form',
        'russian': 'Форма согласия',
        'spanish': 'Formulario de consentimiento',
        'arabic': 'نموذج الموافقة',
        'french': 'Formulaire de consentement',
        'german': 'Einwilligungsformular',
        'chinese': '同意书',
        'thai': 'แบบฟอร์มยินยอม',
        'filipino': 'Consent form',
        'category': 'legal',
        'definition': 'Document agreeing to treatment'
    },
    {
        'english': 'Contraceptive',
        'russian': 'Контрацептив',
        'spanish': 'Anticonceptivo',
        'arabic': 'مانع الحمل',
        'french': 'Contraceptif',
        'german': 'Verhütungsmittel',
        'chinese': '避孕药',
        'thai': 'ยาคุมกำเนิด',
        'filipino': 'Contraceptive',
        'category': 'pharmacy',
        'definition': 'Substance preventing pregnancy'
    },
    {
        'english': 'Convulsion',
        'russian': 'Судорога',
        'spanish': 'Convulsión',
        'arabic': 'تشنج',
        'french': 'Convulsion',
        'german': 'Krampfanfall',
        'chinese': '惊厥',
        'thai': 'อาการชัก',
        'filipino': 'Convulsion',
        'category': 'neurology',
        'definition': 'Involuntary muscle contractions'
    },
    {
        'english': 'Cyst',
        'russian': 'Киста',
        'spanish': 'Quiste',
        'arabic': 'كيس',
        'french': 'Kyste',
        'german': 'Zyste',
        'chinese': '囊肿',
        'thai': 'ถุงน้ำ',
        'filipino': 'Cyst',
        'category': 'general',
        'definition': 'Fluid-filled sac'
    },
    {
        'english': 'Dermatologist',
        'russian': 'Дерматолог',
        'spanish': 'Dermatólogo',
        'arabic': 'طبيب الجلدية',
        'french': 'Dermatologue',
        'german': 'Dermatologe',
        'chinese': '皮肤科医生',
        'thai': 'แพทย์ผิวหนัง',
        'filipino': 'Dermatologist',
        'category': 'dermatology',
        'definition': 'Skin specialist'
    },
    {
        'english': 'Diabetes Mellitus',
        'russian': 'Сахарный диабет',
        'spanish': 'Diabetes mellitus',
        'arabic': 'السكري',
        'french': 'Diabète sucré',
        'german': 'Diabetes mellitus',
        'chinese': '糖尿病',
        'thai': 'เบาหวาน',
        'filipino': 'Diabetes mellitus',
        'category': 'endocrinology',
        'definition': 'High blood sugar levels'
    },
    {
        'english': 'Down Syndrome',
        'russian': 'Синдром Дауна',
        'spanish': 'Síndrome de Down',
        'arabic': 'متلازمة داون',
        'french': 'Syndrome de Down',
        'german': 'Down-Syndrom',
        'chinese': '唐氏综合征',
        'thai': 'ดาวน์ซินโดรม',
        'filipino': 'Down syndrome',
        'category': 'genetics',
        'definition': 'Genetic disorder'
    },
    {
        'english': 'Ectopic',
        'russian': 'Внематочный',
        'spanish': 'Ectópico',
        'arabic': 'خارج الرحم',
        'french': 'Ectopique',
        'german': 'Ektopisch',
        'chinese': '异位',
        'thai': 'นอกมดลูก',
        'filipino': 'Ectopic',
        'category': 'gynecology',
        'definition': 'Abnormal position of an organ'
    },
    {
        'english': 'EKG',
        'russian': 'ЭКГ',
        'spanish': 'Electrocardiograma',
        'arabic': 'تخطيط القلب',
        'french': 'Électrocardiogramme',
        'german': 'EKG',
        'chinese': '心电图',
        'thai': 'การตรวจคลื่นไฟฟ้าหัวใจ',
        'filipino': 'EKG',
        'category': 'cardiology',
        'definition': 'Record of heart activity'
    },
    {
        'english': 'Emphysema',
        'russian': 'Эмфизема',
        'spanish': 'Enfisema',
        'arabic': 'انتفاخ الرئة',
        'french': 'Emphysème',
        'german': 'Lungenemphysem',
        'chinese': '肺气肿',
        'thai': 'ถุงลมโป่งพอง',
        'filipino': 'Emphysema',
        'category': 'respiratory',
        'definition': 'Lung condition causing shortness of breath'
    },
    {
        'english': 'Endocrinology',
        'russian': 'Эндокринология',
        'spanish': 'Endocrinología',
        'arabic': 'علم الغدد الصماء',
        'french': 'Endocrinologie',
        'german': 'Endokrinologie',
        'chinese': '内分泌学',
        'thai': 'วิทยาต่อมไร้ท่อ',
        'filipino': 'Endocrinology',
        'category': 'endocrinology',
        'definition': 'Study of hormones and glands'
    },
    {
        'english': 'Endoscopy',
        'russian': 'Эндоскопия',
        'spanish': 'Endoscopia',
        'arabic': 'تنظير داخلي',
        'french': 'Endoscopie',
        'german': 'Endoskopie',
        'chinese': '内窥镜检查',
        'thai': 'การส่องกล้อง',
        'filipino': 'Endoscopy',
        'category': 'procedure',
        'definition': 'Examination with an endoscope'
    },
    {
        'english': 'Epidural',
        'russian': 'Эпидуральная анестезия',
        'spanish': 'Epidural',
        'arabic': 'فوق الجافية',
        'french': 'Péridurale',
        'german': 'Periduralanästhesie',
        'chinese': '硬膜外麻醉',
        'thai': 'การระงับความรู้สึกทางเยื่อหุ้มไขสันหลัง',
        'filipino': 'Epidural',
        'category': 'procedure',
        'definition': 'Anesthesia injected into the epidural space'
    },
    {
        'english': 'Epilepsy',
        'russian': 'Эпилепсия',
        'spanish': 'Epilepsia',
        'arabic': 'الصرع',
        'french': 'Épilepsie',
        'german': 'Epilepsie',
        'chinese': '癫痫',
        'thai': 'โรคลมบ้าหมู',
        'filipino': 'Epilepsy',
        'category': 'neurology',
        'definition': 'Neurological disorder with seizures'
    },
    {
        'english': 'Esophagus',
        'russian': 'Пищевод',
        'spanish': 'Esófago',
        'arabic': 'المريء',
        'french': 'Œsophage',
        'german': 'Speiseröhre',
        'chinese': '食管',
        'thai': 'หลอดอาหาร',
        'filipino': 'Esophagus',
        'category': 'anatomy',
        'definition': 'Tube carrying food to the stomach'
    },
    {
        'english': 'Fallopian tube',
        'russian': 'Фаллопиева труба',
        'spanish': 'Trompa de Falopio',
        'arabic': 'قناة فالوب',
        'french': 'Trompe de Fallope',
        'german': 'Eileiter',
        'chinese': '输卵管',
        'thai': 'ท่อนำไข่',
        'filipino': 'Fallopian tube',
        'category': 'gynecology',
        'definition': 'Tube connecting ovary to uterus'
    },
    {
        'english': 'Femoral Artery',
        'russian': 'Бедренная артерия',
        'spanish': 'Arteria femoral',
        'arabic': 'الشريان الفخذي',
        'french': 'Artère fémorale',
        'german': 'Oberschenkelarterie',
        'chinese': '股动脉',
        'thai': 'หลอดเลือดแดงต้นขา',
        'filipino': 'Femoral artery',
        'category': 'anatomy',
        'definition': 'Main artery of the thigh'
    },
    {
        'english': 'Gall Bladder',
        'russian': 'Желчный пузырь',
        'spanish': 'Vesícula biliar',
        'arabic': 'المرارة',
        'french': 'Vésicule biliaire',
        'german': 'Gallenblase',
        'chinese': '胆囊',
        'thai': 'ถุงน้ำดี',
        'filipino': 'Gall bladder',
        'category': 'anatomy',
        'definition': 'Organ storing bile'
    },
    {
        'english': 'Gangrene',
        'russian': 'Гангрена',
        'spanish': 'Gangrena',
        'arabic': 'الغرغرينا',
        'french': 'Gangrène',
        'german': 'Gangrän',
        'chinese': '坏疽',
        'thai': 'เนื้อตายเน่า',
        'filipino': 'Gangrene',
        'category': 'general',
        'definition': 'Death of body tissue'
    },
    {
        'english': 'Gastroenterologist',
        'russian': 'Гастроэнтеролог',
        'spanish': 'Gastroenterólogo',
        'arabic': 'طبيب الجهاز الهضمي',
        'french': 'Gastroentérologue',
        'german': 'Gastroenterologe',
        'chinese': '胃肠病专家',
        'thai': 'แพทย์ระบบทางเดินอาหาร',
        'filipino': 'Gastroenterologist',
        'category': 'gastroenterology',
        'definition': 'Digestive system specialist'
    },
    {
        'english': 'Genetic Counselor',
        'russian': 'Генетический консультант',
        'spanish': 'Consejero genético',
        'arabic': 'مستشار وراثي',
        'french': 'Conseiller en génétique',
        'german': 'Genetischer Berater',
        'chinese': '遗传咨询师',
        'thai': 'ที่ปรึกษาทางพันธุกรรม',
        'filipino': 'Genetic counselor',
        'category': 'genetics',
        'definition': 'Healthcare professional advising on genetic conditions'
    },
    {
        'english': 'Glucose',
        'russian': 'Глюкоза',
        'spanish': 'Glucosa',
        'arabic': 'جلوكوز',
        'french': 'Glucose',
        'german': 'Glukose',
        'chinese': '葡萄糖',
        'thai': 'กลูโคส',
        'filipino': 'Glucose',
        'category': 'endocrinology',
        'definition': 'Simple sugar in the blood'
    },
    {
        'english': 'Gynecologist',
        'russian': 'Гинеколог',
        'spanish': 'Ginecólogo',
        'arabic': 'طبيب نساء',
        'french': 'Gynécologue',
        'german': 'Gynäkologe',
        'chinese': '妇科医生',
        'thai': 'สูตินรีแพทย์',
        'filipino': 'Gynecologist',
        'category': 'gynecology',
        'definition': 'Women\'s health specialist'
    },
    {
        'english': 'Heart Disease',
        'russian': 'Болезнь сердца',
        'spanish': 'Enfermedad cardíaca',
        'arabic': 'أمراض القلب',
        'french': 'Maladie cardiaque',
        'german': 'Herzkrankheit',
        'chinese': '心脏病',
        'thai': 'โรคหัวใจ',
        'filipino': 'Heart disease',
        'category': 'cardiology',
        'definition': 'Conditions affecting the heart'
    },
    {
        'english': 'Hemorrhage',
        'russian': 'Кровоизлияние',
        'spanish': 'Hemorragia',
        'arabic': 'نزيف',
        'french': 'Hémorragie',
        'german': 'Blutung',
        'chinese': '出血',
        'thai': 'เลือดออก',
        'filipino': 'Hemorrhage',
        'category': 'emergency',
        'definition': 'Heavy bleeding'
    },
    {
        'english': 'Hepatitis',
        'russian': 'Гепатит',
        'spanish': 'Hepatitis',
        'arabic': 'التهاب الكبد',
        'french': 'Hépatite',
        'german': 'Hepatitis',
        'chinese': '肝炎',
        'thai': 'ตับอักเสบ',
        'filipino': 'Hepatitis',
        'category': 'gastroenterology',
        'definition': 'Inflammation of the liver'
    },
    {
        'english': 'Homeopathic',
        'russian': 'Гомеопатический',
        'spanish': 'Homeopático',
        'arabic': 'المعالجة المثلية',
        'french': 'Homéopathique',
        'german': 'Homöopathisch',
        'chinese': '顺势疗法',
        'thai': 'โฮมีโอพาธี',
        'filipino': 'Homeopathic',
        'category': 'alternative',
        'definition': 'Alternative medicine approach'
    },
    {
        'english': 'Hypoxia',
        'russian': 'Гипоксия',
        'spanish': 'Hipoxia',
        'arabic': 'نقص الأكسجين',
        'french': 'Hypoxie',
        'german': 'Hypoxie',
        'chinese': '缺氧',
        'thai': 'ภาวะขาดออกซิเจน',
        'filipino': 'Hypoxia',
        'category': 'respiratory',
        'definition': 'Lack of oxygen in tissues'
    },
    {
        'english': 'Hysterectomy',
        'russian': 'Гистерэктомия',
        'spanish': 'Histerectomía',
        'arabic': 'استئصال الرحم',
        'french': 'Hystérectomie',
        'german': 'Hysterektomie',
        'chinese': '子宫切除术',
        'thai': 'การตัดมดลูก',
        'filipino': 'Hysterectomy',
        'category': 'procedure',
        'definition': 'Surgical removal of the uterus'
    },
    {
        'english': 'Intestine',
        'russian': 'Кишечник',
        'spanish': 'Intestino',
        'arabic': 'الأمعاء',
        'french': 'Intestin',
        'german': 'Darm',
        'chinese': '肠',
        'thai': 'ลำไส้',
        'filipino': 'Intestine',
        'category': 'anatomy',
        'definition': 'Organ for digestion'
    },
    {
        'english': 'Larynx',
        'russian': 'Гортань',
        'spanish': 'Laringe',
        'arabic': 'الحنجرة',
        'french': 'Larynx',
        'german': 'Kehlkopf',
        'chinese': '喉',
        'thai': 'กล่องเสียง',
        'filipino': 'Larynx',
        'category': 'anatomy',
        'definition': 'Voice box'
    },
    {
        'english': 'Leukemia',
        'russian': 'Лейкоз',
        'spanish': 'Leucemia',
        'arabic': 'سرطان الدم',
        'french': 'Leucémie',
        'german': 'Leukämie',
        'chinese': '白血病',
        'thai': 'มะเร็งเม็ดเลือดขาว',
        'filipino': 'Leukemia',
        'category': 'oncology',
        'definition': 'Cancer of the blood'
    },
    {
        'english': 'Living Will',
        'russian': 'завещание о жизни',
        'spanish': 'testamento vital',
        'arabic': 'الوصية الحية',
        'french': 'testament de vie',
        'german': 'Patientenverfügung',
        'chinese': '生前预嘱',
        'thai': 'พินัยกรรมเพื่อชีวิต',
        'filipino': 'buhay na testamento',
        'category': 'legal',
        'definition': 'Document indicating care preferences'
    },
    {
        'english': 'Lumpectomy',
        'russian': 'Люмпэктомия',
        'spanish': 'Lumpectomía',
        'arabic': 'استئصال الكتلة',
        'french': 'Lumpectomie',
        'german': 'Lumpektomie',
        'chinese': '肿块切除术',
        'thai': 'การตัดก้อนเนื้อออก',
        'filipino': 'Lumpectomy',
        'category': 'procedure',
        'definition': 'Surgical removal of a lump'
    },
    {
        'english': 'Lupus',
        'russian': 'Волчанка',
        'spanish': 'Lupus',
        'arabic': 'الذئبة',
        'french': 'Lupus',
        'german': 'Lupus',
        'chinese': '狼疮',
        'thai': 'โรคลูปัส',
        'filipino': 'Lupus',
        'category': 'immunology',
        'definition': 'Autoimmune disease'
    },
    {
        'english': 'Lymph Node',
        'russian': 'Лимфатический узел',
        'spanish': 'Ganglio linfático',
        'arabic': 'عقدة لمفاوية',
        'french': 'Ganglion lymphatique',
        'german': 'Lymphknoten',
        'chinese': '淋巴结',
        'thai': 'ต่อมน้ำเหลือง',
        'filipino': 'Lymph node',
        'category': 'anatomy',
        'definition': 'Small gland in the lymphatic system'
    },
    {
        'english': 'Malaria',
        'russian': 'Малярия',
        'spanish': 'Malaria',
        'arabic': 'الملاريا',
        'french': 'Paludisme',
        'german': 'Malaria',
        'chinese': '疟疾',
        'thai': 'มาลาเรีย',
        'filipino': 'Malaria',
        'category': 'infectious',
        'definition': 'Mosquito-borne disease'
    },
    {
        'english': 'Malnutrition',
        'russian': 'Недоедание',
        'spanish': 'Desnutrición',
        'arabic': 'سوء التغذية',
        'french': 'Malnutrition',
        'german': 'Mangelernährung',
        'chinese': '营养不良',
        'thai': 'ภาวะทุพโภชนาการ',
        'filipino': 'Malnutrition',
        'category': 'general',
        'definition': 'Lack of proper nutrition'
    },
    {
        'english': 'Mammogram',
        'russian': 'Маммограмма',
        'spanish': 'Mamografía',
        'arabic': 'تصوير الثدي',
        'french': 'Mammographie',
        'german': 'Mammogramm',
        'chinese': '乳房X光检查',
        'thai': 'การตรวจแมมโมแกรม',
        'filipino': 'Mammogram',
        'category': 'diagnostics',
        'definition': 'X-ray of the breast'
    },
    {
        'english': 'Miscarriage',
        'russian': 'Выкидыш',
        'spanish': 'Aborto espontáneo',
        'arabic': 'إجهاض',
        'french': 'Fausse couche',
        'german': 'Fehlgeburt',
        'chinese': '流产',
        'thai': 'การแท้งบุตร',
        'filipino': 'Miscarriage',
        'category': 'gynecology',
        'definition': 'Spontaneous loss of pregnancy'
    },
    {
        'english': 'Morning Sickness',
        'russian': 'Тошнота по утрам',
        'spanish': 'Náuseas matutinas',
        'arabic': 'غثيان الصباح',
        'french': 'Nausées matinales',
        'german': 'Morgenübelkeit',
        'chinese': '晨吐',
        'thai': 'อาการแพ้ท้อง',
        'filipino': 'Morning sickness',
        'category': 'gynecology',
        'definition': 'Nausea during pregnancy'
    },
    {
        'english': 'MRI',
        'russian': 'МРТ',
        'spanish': 'IRM',
        'arabic': 'التصوير بالرنين المغناطيسي',
        'french': 'IRM',
        'german': 'MRT',
        'chinese': '核磁共振',
        'thai': 'การตรวจเอ็มอาร์ไอ',
        'filipino': 'MRI',
        'category': 'diagnostics',
        'definition': 'Magnetic resonance imaging'
    },
    {
        'english': 'Multiple Sclerosis',
        'russian': 'Рассеянный склероз',
        'spanish': 'Esclerosis múltiple',
        'arabic': 'التصلب المتعدد',
        'french': 'Sclérose en plaques',
        'german': 'Multiple Sklerose',
        'chinese': '多发性硬化症',
        'thai': 'โรคปลอกประสาทเสื่อมแข็ง',
        'filipino': 'Multiple sclerosis',
        'category': 'neurology',
        'definition': 'Autoimmune disease affecting the nervous system'
    },
    {
        'english': 'Nausea',
        'russian': 'Тошнота',
        'spanish': 'Náuseas',
        'arabic': 'غثيان',
        'french': 'Nausée',
        'german': 'Übelkeit',
        'chinese': '恶心',
        'thai': 'คลื่นไส้',
        'filipino': 'Nausea',
        'category': 'symptom',
        'definition': 'Feeling of sickness'
    },
    {
        'english': 'Neurologist',
        'russian': 'Невролог',
        'spanish': 'Neurólogo',
        'arabic': 'طبيب أعصاب',
        'french': 'Neurologue',
        'german': 'Neurologe',
        'chinese': '神经科医生',
        'thai': 'แพทย์ระบบประสาท',
        'filipino': 'Neurologist',
        'category': 'neurology',
        'definition': 'Nervous system specialist'
    },
    {
        'english': 'Nutritionist',
        'russian': 'Диетолог',
        'spanish': 'Nutricionista',
        'arabic': 'أخصائي تغذية',
        'french': 'Nutritionniste',
        'german': 'Ernährungsberater',
        'chinese': '营养师',
        'thai': 'นักโภชนาการ',
        'filipino': 'Nutritionist',
        'category': 'general',
        'definition': 'Diet and nutrition specialist'
    },
    {
        'english': 'Obstetrician',
        'russian': 'Акушер',
        'spanish': 'Obstetra',
        'arabic': 'طبيب توليد',
        'french': 'Obstétricien',
        'german': 'Geburtshelfer',
        'chinese': '产科医生',
        'thai': 'สูติแพทย์',
        'filipino': 'Obstetrician',
        'category': 'gynecology',
        'definition': 'Pregnancy and childbirth specialist'
    },
    {
        'english': 'Oncologist',
        'russian': 'Онколог',
        'spanish': 'Oncólogo',
        'arabic': 'طبيب الأورام',
        'french': 'Oncologue',
        'german': 'Onkologe',
        'chinese': '肿瘤科医生',
        'thai': 'แพทย์ผู้เชี่ยวชาญด้านมะเร็ง',
        'filipino': 'Oncologist',
        'category': 'oncology',
        'definition': 'Cancer specialist'
    },
    {
        'english': 'Orthopedist',
        'russian': 'Ортопед',
        'spanish': 'Ortopedista',
        'arabic': 'طبيب العظام',
        'french': 'Orthopédiste',
        'german': 'Orthopäde',
        'chinese': '骨科医生',
        'thai': 'แพทย์กระดูก',
        'filipino': 'Orthopedist',
        'category': 'orthopedics',
        'definition': 'Bone and joint specialist'
    },
    {
        'english': 'Ovary',
        'russian': 'Яичник',
        'spanish': 'Ovario',
        'arabic': 'المبيض',
        'french': 'Ovaire',
        'german': 'Eierstock',
        'chinese': '卵巢',
        'thai': 'รังไข่',
        'filipino': 'Ovary',
        'category': 'gynecology',
        'definition': 'Female reproductive organ'
    },
    {
        'english': 'Pacemaker',
        'russian': 'Кардиостимулятор',
        'spanish': 'Marcapasos',
        'arabic': 'جهاز تنظيم ضربات القلب',
        'french': 'Stimulateur cardiaque',
        'german': 'Herzschrittmacher',
        'chinese': '心脏起搏器',
        'thai': 'เครื่องกระตุ้นหัวใจ',
        'filipino': 'Pacemaker',
        'category': 'cardiology',
        'definition': 'Device that regulates heart rhythm'
    },
    {
        'english': 'Pancreas',
        'russian': 'Поджелудочная железа',
        'spanish': 'Páncreas',
        'arabic': 'البنكرياس',
        'french': 'Pancréas',
        'german': 'Bauchspeicheldrüse',
        'chinese': '胰腺',
        'thai': 'ตับอ่อน',
        'filipino': 'Pancreas',
        'category': 'anatomy',
        'definition': 'Organ that produces insulin and digestive enzymes'
    },
    {
        'english': 'Pathology',
        'russian': 'Патология',
        'spanish': 'Patología',
        'arabic': 'علم الأمراض',
        'french': 'Pathologie',
        'german': 'Pathologie',
        'chinese': '病理学',
        'thai': 'พยาธิวิทยา',
        'filipino': 'Pathology',
        'category': 'general',
        'definition': 'Study of disease'
    },
    {
        'english': 'Patient Advocate',
        'russian': 'Адвокат пациента',
        'spanish': 'Defensor del paciente',
        'arabic': 'مدافع عن المريض',
        'french': 'Défenseur des patients',
        'german': 'Patientenfürsprecher',
        'chinese': '患者权益倡导者',
        'thai': 'ผู้สนับสนุนผู้ป่วย',
        'filipino': 'Patient advocate',
        'category': 'legal',
        'definition': 'Person who supports patient rights'
    },
    {
        'english': 'Physiology',
        'russian': 'Физиология',
        'spanish': 'Fisiología',
        'arabic': 'علم وظائف الأعضاء',
        'french': 'Physiologie',
        'german': 'Physiologie',
        'chinese': '生理学',
        'thai': 'สรีรวิทยา',
        'filipino': 'Physiology',
        'category': 'general',
        'definition': 'Study of body functions'
    },
    {
        'english': 'Power of Attorney',
        'russian': 'Доверенность',
        'spanish': 'Poder notarial',
        'arabic': 'توكيل رسمي',
        'french': 'Procuration',
        'german': 'Vollmacht',
        'chinese': '授权书',
        'thai': 'หนังสือมอบอำนาจ',
        'filipino': 'Power of attorney',
        'category': 'legal',
        'definition': 'Legal document authorizing someone to act on your behalf'
    },
    {
        'english': 'Radiation Therapy',
        'russian': 'Лучевая терапия',
        'spanish': 'Radioterapia',
        'arabic': 'العلاج الإشعاعي',
        'french': 'Radiothérapie',
        'german': 'Strahlentherapie',
        'chinese': '放射治疗',
        'thai': 'การฉายรังสี',
        'filipino': 'Radiation therapy',
        'category': 'oncology',
        'definition': 'Cancer treatment using radiation'
    },
    {
        'english': 'Radiologist',
        'russian': 'Радиолог',
        'spanish': 'Radiólogo',
        'arabic': 'أخصائي الأشعة',
        'french': 'Radiologue',
        'german': 'Radiologe',
        'chinese': '放射科医生',
        'thai': 'แพทย์รังสีวิทยา',
        'filipino': 'Radiologist',
        'category': 'diagnostics',
        'definition': 'Imaging specialist'
    },
    {
        'english': 'Sickle Cell Anemia',
        'russian': 'Серповидноклеточная анемия',
        'spanish': 'Anemia falciforme',
        'arabic': 'فقر الدم المنجلي',
        'french': 'Drépanocytose',
        'german': 'Sichelzellanämie',
        'chinese': '镰状细胞贫血',
        'thai': 'โรคโลหิตจางรูปเคียว',
        'filipino': 'Sickle cell anemia',
        'category': 'hematology',
        'definition': 'Genetic blood disorder'
    },
    {
        'english': 'Spina Bifida',
        'russian': 'Расщепление позвоночника',
        'spanish': 'Espina bífida',
        'arabic': 'السنسنة المشقوقة',
        'french': 'Spina bifida',
        'german': 'Spina bifida',
        'chinese': '脊柱裂',
        'thai': 'กระดูกสันหลังแยก',
        'filipino': 'Spina bifida',
        'category': 'neurology',
        'definition': 'Birth defect of the spine'
    },
    {
        'english': 'Schizophrenia',
        'russian': 'Шизофрения',
        'spanish': 'Esquizofrenia',
        'arabic': 'الفصام',
        'french': 'Schizophrénie',
        'german': 'Schizophrenie',
        'chinese': '精神分裂症',
        'thai': 'โรคจิตเภท',
        'filipino': 'Schizophrenia',
        'category': 'psychiatry',
        'definition': 'Severe mental disorder'
    },
    {
        'english': 'Stent',
        'russian': 'Стенд',
        'spanish': 'Stent',
        'arabic': 'دعامة',
        'french': 'Stent',
        'german': 'Stent',
        'chinese': '支架',
        'thai': 'ขดลวด',
        'filipino': 'Stent',
        'category': 'cardiology',
        'definition': 'Tube inserted into a vessel'
    },
    {
        'english': 'Stethoscope',
        'russian': 'Стетоскоп',
        'spanish': 'Estetoscopio',
        'arabic': 'سماعة الطبيب',
        'french': 'Stéthoscope',
        'german': 'Stethoskop',
        'chinese': '听诊器',
        'thai': 'หูฟังแพทย์',
        'filipino': 'Stethoscope',
        'category': 'equipment',
        'definition': 'Medical device for listening to heart and lungs'
    },
    {
        'english': 'Thyroid gland',
        'russian': 'Щитовидная железа',
        'spanish': 'Glándula tiroides',
        'arabic': 'الغدة الدرقية',
        'french': 'Glande thyroïde',
        'german': 'Schilddrüse',
        'chinese': '甲状腺',
        'thai': 'ต่อมไทรอยด์',
        'filipino': 'Thyroid gland',
        'category': 'endocrinology',
        'definition': 'Gland regulating metabolism'
    },
    {
        'english': 'Tinnitus',
        'russian': 'Тиннитус',
        'spanish': 'Tinnitus',
        'arabic': 'طنين الأذن',
        'french': 'Acouphène',
        'german': 'Tinnitus',
        'chinese': '耳鸣',
        'thai': 'หูอื้อ',
        'filipino': 'Tinnitus',
        'category': 'neurology',
        'definition': 'Ringing in the ears'
    },
    {
        'english': 'Tracheotomy',
        'russian': 'Трахеотомия',
        'spanish': 'Traqueotomía',
        'arabic': 'بضع القصبة الهوائية',
        'french': 'Trachéotomie',
        'german': 'Tracheotomie',
        'chinese': '气管切开术',
        'thai': 'การผ่าตัดเปิดหลอดลม',
        'filipino': 'Tracheotomy',
        'category': 'procedure',
        'definition': 'Surgical opening of the trachea'
    },
    {
        'english': 'Tuberculosis',
        'russian': 'Туберкулез',
        'spanish': 'Tuberculosis',
        'arabic': 'السل',
        'french': 'Tuberculose',
        'german': 'Tuberkulose',
        'chinese': '肺结核',
        'thai': 'วัณโรค',
        'filipino': 'Tuberculosis',
        'category': 'infectious',
        'definition': 'Bacterial lung infection'
    },
    {
        'english': 'Urologist',
        'russian': 'Уролог',
        'spanish': 'Urólogo',
        'arabic': 'طبيب مسالك بولية',
        'french': 'Urologue',
        'german': 'Urologe',
        'chinese': '泌尿科医生',
        'thai': 'แพทย์ระบบทางเดินปัสสาวะ',
        'filipino': 'Urologist',
        'category': 'urology',
        'definition': 'Urinary tract specialist'
    },
    {
        'english': 'Lumpectomy',
        'russian': 'Люмпэктомия',
        'spanish': 'Lumpectomía',
        'arabic': 'استئصال الكتلة',
        'french': 'Lumpectomie',
        'german': 'Lumpektomie',
        'chinese': '肿块切除术',
        'thai': 'การตัดก้อนเนื้อออก',
        'filipino': 'Lumpectomy',
        'category': 'procedure',
        'definition': 'Surgical removal of a lump'
    },
    {
        'english': 'Adjuvant therapy',
        'russian': 'Адъювантная терапия',
        'spanish': 'Terapia adyuvante',
        'arabic': 'العلاج المساعد',
        'french': 'Thérapie adjuvante',
        'german': 'Adjuvante Therapie',
        'chinese': '辅助治疗',
        'thai': 'การรักษาเสริม',
        'filipino': 'Terapyong pantulong',
        'category': 'oncology',
        'definition': 'Additional treatment after primary treatment'
    },
    {
        'english': 'Eardrum',
        'russian': 'Барабанная перепонка',
        'spanish': 'Tímpano',
        'arabic': 'طبلة الأذن',
        'french': 'Tympan',
        'german': 'Trommelfell',
        'chinese': '鼓膜',
        'thai': 'แก้วหู',
        'filipino': 'Eardrum',
        'category': 'anatomy',
        'definition': 'Membrane in the ear'
    },
    {
        'english': 'Fullness',
        'russian': 'Ощущение полноты',
        'spanish': 'Plenitud',
        'arabic': 'امتلاء',
        'french': 'Pleur de satiété',
        'german': 'Völlegefühl',
        'chinese': '饱胀感',
        'thai': 'ความรู้สึกอิ่ม',
        'filipino': 'Fullness',
        'category': 'symptom',
        'definition': 'Feeling of being full'
    },
    {
        'english': 'Squeezing sensation',
        'russian': 'Ощущение сдавления',
        'spanish': 'Sensación de opresión',
        'arabic': 'الشعور بالضغط',
        'french': 'Sensation d\'écrasement',
        'german': 'Druckgefühl',
        'chinese': '挤压感',
        'thai': 'ความรู้สึกบีบ',
        'filipino': 'Squeezing sensation',
        'category': 'symptom',
        'definition': 'Feeling of pressure'
    },
    {
        'english': 'Neuropathic pain',
        'russian': 'Нейропатическая боль',
        'spanish': 'Dolor neuropático',
        'arabic': 'ألم عصبي',
        'french': 'Douleur neuropathique',
        'german': 'Neuropathischer Schmerz',
        'chinese': '神经性疼痛',
        'thai': 'อาการปวดเส้นประสาท',
        'filipino': 'Neuropathic pain',
        'category': 'symptom',
        'definition': 'Pain caused by nerve damage'
    },
    {
        'english': 'Nociceptive pain',
        'russian': 'Ноцицептивная боль',
        'spanish': 'Dolor nociceptivo',
        'arabic': 'ألم مسبب للأذى',
        'french': 'Douleur nociceptive',
        'german': 'Nozizeptiver Schmerz',
        'chinese': '伤害性疼痛',
        'thai': 'อาการปวดจากการบาดเจ็บ',
        'filipino': 'Nociceptive pain',
        'category': 'symptom',
        'definition': 'Pain from tissue damage'
    },
    {
        'english': 'Radicular pain',
        'russian': 'Корешковая боль',
        'spanish': 'Dolor radicular',
        'arabic': 'ألم جذري',
        'french': 'Douleur radiculaire',
        'german': 'Radikulärer Schmerz',
        'chinese': '根性疼痛',
        'thai': 'อาการปวดรากประสาท',
        'filipino': 'Radicular pain',
        'category': 'symptom',
        'definition': 'Pain from spinal nerve root'
    },
    {
        'english': 'Sharp',
        'russian': 'Острая боль',
        'spanish': 'Dolor agudo',
        'arabic': 'ألم حاد',
        'french': 'Douleur aiguë',
        'german': 'Scharfer Schmerz',
        'chinese': '尖锐疼痛',
        'thai': 'อาการปวดเฉียบพลัน',
        'filipino': 'Sharp',
        'category': 'symptom',
        'definition': 'Intense, sudden pain'
    },
    {
        'english': 'Achy',
        'russian': 'Ноющая боль',
        'spanish': 'Dolor sordo',
        'arabic': 'ألم خفيف',
        'french': 'Douleur sourde',
        'german': 'Schmerzender Schmerz',
        'chinese': '钝痛',
        'thai': 'อาการปวดเมื่อย',
        'filipino': 'Achy',
        'category': 'symptom',
        'definition': 'Dull, continuous pain'
    },
    {
        'english': 'Dull',
        'russian': 'Тупая боль',
        'spanish': 'Dolor sordo',
        'arabic': 'ألم خفيف',
        'french': 'Douleur sourde',
        'german': 'Stumpfer Schmerz',
        'chinese': '钝痛',
        'thai': 'อาการปวดทึบ',
        'filipino': 'Dull',
        'category': 'symptom',
        'definition': 'Mild, persistent pain'
    },
    {
        'english': 'Stabbing',
        'russian': 'Колющая боль',
        'spanish': 'Dolor punzante',
        'arabic': 'ألم طعن',
        'french': 'Douleur lancinante',
        'german': 'Stechender Schmerz',
        'chinese': '刺痛',
        'thai': 'อาการปวดแทง',
        'filipino': 'Stabbing',
        'category': 'symptom',
        'definition': 'Sharp, intense pain'
    },
    {
        'english': 'Throbbing',
        'russian': 'Пульсирующая боль',
        'spanish': 'Dolor pulsátil',
        'arabic': 'ألم نابض',
        'french': 'Douleur pulsatile',
        'german': 'Pochender Schmerz',
        'chinese': '搏动性疼痛',
        'thai': 'อาการปวดตุบๆ',
        'filipino': 'Throbbing',
        'category': 'symptom',
        'definition': 'Pain that pulses'
    },
    {
        'english': 'Constant',
        'russian': 'Постоянная боль',
        'spanish': 'Dolor constante',
        'arabic': 'ألم مستمر',
        'french': 'Douleur constante',
        'german': 'Ständiger Schmerz',
        'chinese': '持续性疼痛',
        'thai': 'อาการปวดตลอดเวลา',
        'filipino': 'Constant',
        'category': 'symptom',
        'definition': 'Pain that does not stop'
    },
    {
        'english': 'Intermittent',
        'russian': 'Перемежающаяся боль',
        'spanish': 'Dolor intermitente',
        'arabic': 'ألم متقطع',
        'french': 'Douleur intermittente',
        'german': 'Intermittierender Schmerz',
        'chinese': '间歇性疼痛',
        'thai': 'อาการปวดเป็นพักๆ',
        'filipino': 'Intermittent',
        'category': 'symptom',
        'definition': 'Pain that comes and goes'
    },
    {
        'english': 'Acute',
        'russian': 'Острая боль',
        'spanish': 'Dolor agudo',
        'arabic': 'ألم حاد',
        'french': 'Douleur aiguë',
        'german': 'Akuter Schmerz',
        'chinese': '急性疼痛',
        'thai': 'อาการปวดเฉียบพลัน',
        'filipino': 'Acute',
        'category': 'symptom',
        'definition': 'Sudden, severe pain'
    },
    {
        'english': 'Chronic',
        'russian': 'Хроническая боль',
        'spanish': 'Dolor crónico',
        'arabic': 'ألم مزمن',
        'french': 'Douleur chronique',
        'german': 'Chronischer Schmerz',
        'chinese': '慢性疼痛',
        'thai': 'อาการปวดเรื้อรัง',
        'filipino': 'Chronic',
        'category': 'symptom',
        'definition': 'Long-lasting pain'
    },
    {
        'english': 'Localized',
        'russian': 'Локализованная боль',
        'spanish': 'Dolor localizado',
        'arabic': 'ألم موضعي',
        'french': 'Douleur localisée',
        'german': 'Lokalisierter Schmerz',
        'chinese': '局部疼痛',
        'thai': 'อาการปวดเฉพาะที่',
        'filipino': 'Localized',
        'category': 'symptom',
        'definition': 'Pain in a specific area'
    },
    {
        'english': 'Shooting',
        'russian': 'Стреляющая боль',
        'spanish': 'Dolor lancinante',
        'arabic': 'ألم إطلاق نار',
        'french': 'Douleur fulgurante',
        'german': 'Schießender Schmerz',
        'chinese': '射击性疼痛',
        'thai': 'อาการปวดยิง',
        'filipino': 'Shooting',
        'category': 'symptom',
        'definition': 'Pain that radiates'
    },
    {
        'english': 'Burning',
        'russian': 'Жгучая боль',
        'spanish': 'Dolor ardiente',
        'arabic': 'ألم حارق',
        'french': 'Douleur brûlante',
        'german': 'Brennender Schmerz',
        'chinese': '灼烧性疼痛',
        'thai': 'อาการปวดแสบ',
        'filipino': 'Burning',
        'category': 'symptom',
        'definition': 'Pain that feels like burning'
    },
    {
        'english': 'Catching',
        'russian': 'Защемляющая боль',
        'spanish': 'Dolor por atrapamiento',
        'arabic': 'ألم حاد',
        'french': 'Douleur de piégeage',
        'german': 'Einklemmungsschmerz',
        'chinese': '夹痛',
        'thai': 'อาการปวดเสียด',
        'filipino': 'Catching',
        'category': 'symptom',
        'definition': 'Pain that catches during movement'
    },
    {
        'english': 'Cramping',
        'russian': 'Судорожная боль',
        'spanish': 'Dolor por calambres',
        'arabic': 'ألم تشنجي',
        'french': 'Douleur crampiforme',
        'german': 'Krampfartiger Schmerz',
        'chinese': '痉挛性疼痛',
        'thai': 'อาการปวดเกร็ง',
        'filipino': 'Cramping',
        'category': 'symptom',
        'definition': 'Painful muscle contractions'
    },
    {
        'english': 'Slight',
        'russian': 'Легкая боль',
        'spanish': 'Dolor leve',
        'arabic': 'ألم خفيف',
        'french': 'Douleur légère',
        'german': 'Leichter Schmerz',
        'chinese': '轻度疼痛',
        'thai': 'อาการปวดเล็กน้อย',
        'filipino': 'Slight',
        'category': 'symptom',
        'definition': 'Mild pain'
    },
    {
        'english': 'Mild',
        'russian': 'Умеренная боль',
        'spanish': 'Dolor moderado',
        'arabic': 'ألم معتدل',
        'french': 'Douleur modérée',
        'german': 'Mäßiger Schmerz',
        'chinese': '中度疼痛',
        'thai': 'อาการปวดปานกลาง',
        'filipino': 'Mild',
        'category': 'symptom',
        'definition': 'Moderate pain'
    },
    {
        'english': 'Severe',
        'russian': 'Сильная боль',
        'spanish': 'Dolor severo',
        'arabic': 'ألم شديد',
        'french': 'Douleur sévère',
        'german': 'Starker Schmerz',
        'chinese': '剧烈疼痛',
        'thai': 'อาการปวดรุนแรง',
        'filipino': 'Severe',
        'category': 'symptom',
        'definition': 'Intense pain'
    },
    {
        'english': 'Pericarditis',
        'russian': 'Перикардит',
        'spanish': 'Pericarditis',
        'arabic': 'التهاب التامور',
        'french': 'Péricardite',
        'german': 'Perikarditis',
        'chinese': '心包炎',
        'thai': 'เยื่อหุ้มหัวใจอักเสบ',
        'filipino': 'Pericarditis',
        'category': 'cardiology',
        'definition': 'Inflammation of the pericardium'
    },
    {
        'english': 'Glucose monitor',
        'russian': 'Глюкометр',
        'spanish': 'Monitor de glucosa',
        'arabic': 'جهاز قياس الجلوكوز',
        'french': 'Moniteur de glucose',
        'german': 'Glukosemonitor',
        'chinese': '血糖监测仪',
        'thai': 'เครื่องวัดระดับน้ำตาลในเลือด',
        'filipino': 'Glucose monitor',
        'category': 'equipment',
        'definition': 'Device to measure blood sugar'
    },
    {
        'english': 'Test Strip',
        'russian': 'Тест-полоска',
        'spanish': 'Tira reactiva',
        'arabic': 'شريط اختبار',
        'french': 'Bandelette réactive',
        'german': 'Teststreifen',
        'chinese': '试纸',
        'thai': 'แถบทดสอบ',
        'filipino': 'Test strip',
        'category': 'equipment',
        'definition': 'Strip used with a glucose monitor'
    }
]

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
    definition = db.Column(db.Text)
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
            'definition': self.definition,
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
    print("☑️ Database created! No sample cards added — users will add their own.")

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

# ------------------------------------------------------------
# AUTHENTICATION ROUTES
# ------------------------------------------------------------
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
        basic_terms = [
            {
                'english': 'blood pressure',
                'russian': 'кровяное / артериальное давление',
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
                'russian': 'инфаркт, сердечный приступ',
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
                'english': 'Living Will',
                'russian': 'завещание о жизни. Завещание о жизни позволяет заранее выразить свои предпочтения в области медицинского обслуживания.',
                'spanish': 'testamento vital',
                'arabic': 'الوصية الحية',
                'french': 'testament de vie',
                'german': 'Patientenverfügung',
                'chinese': '生前预嘱',
                'thai': 'พินัยกรรมเพื่อชีวิต',
                'filipino': 'buhay na testamento',
                'category': 'legal',
                'definition': 'A document that indicates the type of care a patient wants in the event they become incompetent to make decision.'
            },
            {
                'english': 'Advanced Directives',
                'russian': 'предварительное распоряжение о медицинском обслуживании',
                'spanish': 'directivas anticipadas',
                'arabic': 'التوجيهات المسبقة',
                'french': 'directives anticipées',
                'german': 'Patientenverfügung',
                'chinese': '预先指示',
                'thai': 'คำสั่งล่วงหน้า',
                'filipino': 'paunang direktiba',
                'category': 'legal',
                'definition': 'Legal documents that convey your decisions about end-of-life care (includes medical power of attorney, living will). Texas law requires that all patients be asked if they have advanced directives prior to admission.'
            },
            {
                'english': 'Benign',
                'russian': 'доброкачественный',
                'spanish': 'benigno',
                'arabic': 'حميد',
                'french': 'bénin',
                'german': 'gutartig',
                'chinese': '良性',
                'thai': 'ไม่ร้ายแรง',
                'filipino': 'benigno',
                'category': 'oncology',
                'definition': 'Mild-natured; not cancerous.'
            },
            {
                'english': 'Catheter',
                'russian': 'катетер',
                'spanish': 'catéter',
                'arabic': 'قسطرة',
                'french': 'cathéter',
                'german': 'Katheter',
                'chinese': '导管',
                'thai': 'สายสวน',
                'filipino': 'kateter',
                'category': 'equipment',
                'definition': 'A small tube allowing infusion or drainage of fluid. May also be called an IV line, port-a-cath, or Foley.'
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
                'english': 'Constipation',
                'russian': 'запор',
                'spanish': 'estreñimiento',
                'arabic': 'إمساك',
                'french': 'constipation',
                'german': 'Verstopfung',
                'chinese': '便秘',
                'thai': 'ท้องผูก',
                'filipino': 'tibi',
                'category': 'symptom',
                'definition': 'Infrequent bowel movements.'
            },
            {
                'english': 'CT (Computed Tomography)',
                'russian': 'компьютерная томография (КТ)',
                'spanish': 'tomografía computarizada (TC)',
                'arabic': 'التصوير المقطعي المحوسب',
                'french': 'tomodensitométrie (TDM)',
                'german': 'Computertomographie (CT)',
                'chinese': '计算机断层扫描（CT）',
                'thai': 'การตรวจซีที (Computed Tomography)',
                'filipino': 'CT (Computed Tomography)',
                'category': 'diagnostics',
                'definition': 'A diagnostic test with cross-sectional images (type of cross-sectional x-ray). Also called a CAT scan.'
            },
            {
                'english': 'Deductible',
                'russian': 'Сумма оплаты до начала страховки. Франшиза.',
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
                'english': 'DNR (Do Not Resuscitate)',
                'russian': 'не реанимировать (DNR)',
                'spanish': 'no reanimar (DNR)',
                'arabic': 'لا للإنعاش (DNR)',
                'french': 'ne pas réanimer (DNR)',
                'german': 'nicht reanimieren (DNR)',
                'chinese': '不复苏（DNR）',
                'thai': 'ไม่ช่วยชีวิต (DNR)',
                'filipino': 'huwag buhayin muli (DNR)',
                'category': 'legal',
                'definition': 'A medical order not to perform CPR if the patient stops breathing or their heart stops.'
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
            }
        ]
        
        for term in basic_terms:
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

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/upgrade-premium')
def upgrade_premium():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Check if user already has premium terms
    existing = Flashcard.query.filter_by(user_id=user.id, folder='premium').first()
    if existing:
        flash('You already have premium terms!', 'info')
        return redirect(url_for('study'))
    
    # Add all premium terms
    for term in premium_terms:
        card = Flashcard(
            user_id=user.id,
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
            folder='premium'
        )
        db.session.add(card)
        print(f"Adding {len(premium_terms)} premium terms for user {user.username}")
    db.session.commit()
    flash('🎉 Premium dictionary added! You now have access to 128 medical terms.', 'success')
    return redirect(url_for('study'))

@app.route('/trial')
def trial():
    return render_template('trial.html')

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
    folders = ['general', 'medical', 'insurance', 'legal', 'oncology', 'cardiology', 'emergency', 'premium']
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
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.reader(stream)
            headers = [h.lower().strip() for h in next(csv_input)]
            rows = list(csv_input)
            
        elif file.filename.endswith('.xlsx'):
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
        definition=request.form.get('definition', ''),
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

# ------------------------------------------------------------
# RUN THE APP
# ------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)