from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
from flask_cors import CORS
import os
import hashlib

# --- กำหนดค่า Flask App ---
app = Flask(__name__) 
CORS(app) 

# กำหนดค่าฐานข้อมูล SQLite
base_dir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(base_dir, 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)
    
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_dir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- ลำดับสถานะงานซ่อมที่ละเอียดขึ้น (Hardcoded ใน Python เพื่อใช้ในการตรวจสอบ) ---
# ต้องมั่นใจว่ารายการนี้ตรงกับ STATUS_ORDER_DETAIL ใน index.html
STATUS_ORDER_DETAIL_PYTHON = [
    'ยืนยันจอง', 
    'รอรับรถ', 
    'รถเข้าอู่', 
    'ตรวจเช็ค/ประเมิน', 
    'รออะไหล่/รออนุมัติ', 
    'กำลังดำเนินการ', 
    'ควบคุมคุณภาพ', 
    'ซ่อมเสร็จสิ้น'
]
# --- สิ้นสุดสถานะงานซ่อม ---

# --- สร้าง Models (ตารางในฐานข้อมูล) ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False) # ใช้เป็น Email
    password = db.Column(db.String(256), nullable=False) # รหัสผ่านที่เข้ารหัส
    fullname = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False) # ใช้เป็นเบอร์โทรสำหรับ Login/Tracking
    email = db.Column(db.String(120), unique=True, nullable=False) 
    user_type = db.Column(db.String(10), default='customer') # 'customer' หรือ 'admin'

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    service_type = db.Column(db.String(100), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    booking_time = db.Column(db.Time, nullable=False)
    license_plate = db.Column(db.String(20), nullable=False) 
    # **** แก้ไข: ขยายขนาด Column และตั้งค่า Default Status ใหม่ ****
    status = db.Column(db.String(50), default='ยืนยันจอง') # ขยายขนาดเป็น 50
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # เพิ่มความสัมพันธ์กับ User
    customer = db.relationship('User', backref='booking_details')

    def to_dict(self):
        # ฟังก์ชันแปลง Object เป็น Dictionary สำหรับส่งกลับไปที่ Frontend
        return {
            'id': self.id,
            'user_id': self.user_id,
            'fullname': self.customer.fullname if self.customer else 'N/A',
            'phone_number': self.customer.phone_number if self.customer else 'N/A',
            'email': self.customer.email if self.customer else 'N/A',
            'service_type': self.service_type,
            'booking_date': self.booking_date.isoformat(),
            'booking_time': self.booking_time.isoformat(),
            'license_plate': self.license_plate,
            'status': self.status
        }

# --- ฟังก์ชันช่วยเหลือ ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password_hash, provided_password):
    return stored_password_hash == hash_password(provided_password)

# --- Routes หลัก (Rendering Templates) ---

@app.route('/')
def index():
    """แสดงหน้าหลัก (Customer View)"""
    return render_template('index.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    """แสดงหน้า Admin Dashboard"""
    return render_template('admin_dashboard.html')

# --- API Endpoints: การจัดการฐานข้อมูลและการยืนยันตัวตน ---

@app.route('/api/initdb', methods=['GET'])
def init_db():
    """สร้างตารางในฐานข้อมูลและสร้าง Admin เริ่มต้น"""
    # *** ข้อควรระวัง: หากคุณเปลี่ยน Model (User/Booking) คุณต้องลบไฟล์ site.db ทิ้ง
    # เพื่อให้ db.create_all() ทำงานและสร้างตารางใหม่ด้วยขนาด/สถานะใหม่
    with app.app_context():
        db.create_all()
        admin_exists = User.query.filter_by(user_type='admin').first()
        if not admin_exists:
            admin_user = User(
                username='admin@garage.com', 
                password=hash_password('0811234567'), 
                fullname='Admin Auto Shop',
                phone_number='0811234567',
                email='admin@garage.com',
                user_type='admin'
            )
            test_customer = User(
                username='patid_test',
                password=hash_password('1234'),
                fullname='พาทิศ ลดาพงษ์พัฒนา',
                phone_number='0816507142',
                email='patidzazaza@gmail.com',
                user_type='customer'
            )
            db.session.add_all([admin_user, test_customer])
            db.session.commit()
            return jsonify({'message': 'Database initialized and default Admin/Test Customer created.'}), 201
        return jsonify({'message': 'Database already initialized.'}), 200


@app.route('/api/login', methods=['POST'])
def login():
    """API สำหรับ Login ของ Admin/พนักงาน"""
    data = request.json
    username = data.get('username') 
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()

    if user and verify_password(user.password, password) and user.user_type == 'admin':
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'fullname': user.fullname,
            'user_type': user.user_type,
            'redirect': url_for('admin_dashboard')
        }), 200
    return jsonify({'error': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง หรือคุณไม่ใช่ Admin'}), 401

# --- API Endpoints: ส่วนของลูกค้า (Booking & Tracking) ---

@app.route('/api/book', methods=['POST'])
def book_queue():
    """API สำหรับจองคิวซ่อม (TC-002, TC-006)"""
    data = request.json
    
    customer_email = data['email']
    customer_phone = data['phone']
    
    user = User.query.filter_by(email=customer_email).first()
    if not user:
        user = User(
            username=customer_email,
            password=hash_password(customer_phone),
            fullname=f"{data['firstName']} {data['lastName']}",
            phone_number=customer_phone,
            email=customer_email,
            user_type='customer'
        )
        db.session.add(user)
        db.session.flush() 
    
    try:
        booking_date = datetime.strptime(data['bookingDate'], '%Y-%m-%d').date()
        booking_time = datetime.strptime(data['bookingTime'], '%H:%M').time()
    except:
        return jsonify({'error': 'รูปแบบวันที่หรือเวลาไม่ถูกต้อง'}), 400

    # TC-006: ป้องกันคิวซ้ำซ้อน
    # **** แก้ไข: ใช้สถานะที่ละเอียดขึ้นในการตรวจสอบคิวที่ยัง Active ****
    active_statuses = [s for s in STATUS_ORDER_DETAIL_PYTHON if s != 'ซ่อมเสร็จสิ้น']
    
    existing_booking = Booking.query.filter(
        Booking.booking_date == booking_date,
        Booking.booking_time == booking_time,
        Booking.status.in_(active_statuses)
    ).first()

    if existing_booking:
        return jsonify({'error': '❌ เวลาจองนี้มีคิวอื่นจองอยู่แล้ว กรุณาเลือกเวลาอื่น'}), 409 # Conflict

    # สร้างการจองใหม่
    new_booking = Booking(
        user_id=user.id,
        service_type=data['selectedService'],
        booking_date=booking_date,
        booking_time=booking_time,
        license_plate=data['licensePlate'],
        status='ยืนยันจอง' # สถานะเริ่มต้น
    )

    try:
        db.session.add(new_booking)
        db.session.commit()
        
        print(f"\n[NOTIFICATION MOCK] Sending confirmation to {user.email} for booking ID: {new_booking.id}")
        
        return jsonify({'message': '✅ ข้อมูลการจองถูกบันทึกสำเร็จ!', 'booking_id': new_booking.id, 'tracking_key': customer_phone}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error booking: {e}")
        return jsonify({'error': 'ไม่สามารถบันทึกการจองได้ เนื่องจากมีข้อผิดพลาดในฐานข้อมูล'}), 500

@app.route('/api/track', methods=['GET'])
def track_status():
    """API สำหรับตรวจสอบสถานะงานซ่อม"""
    tracking_key = request.args.get('key')
    
    if not tracking_key:
        return jsonify({'error': 'Missing tracking key'}), 400

    user = User.query.filter((User.phone_number == tracking_key) | (User.email == tracking_key)).first()

    if not user:
        return jsonify({'error': f'ไม่พบข้อมูลการจองสำหรับ {tracking_key}'}), 404

    latest_booking = Booking.query.filter_by(user_id=user.id).order_by(Booking.booking_date.desc(), Booking.booking_time.desc()).first()

    if not latest_booking:
         return jsonify({'error': f'ไม่พบการจองล่าสุดสำหรับ {tracking_key}'}), 404

    return jsonify({
        'message': 'Status found',
        'data': latest_booking.to_dict()
    }), 200

# --- API Endpoints: ส่วนของ Admin (Dashboard) ---

@app.route('/api/admin/bookings', methods=['GET'])
def get_all_bookings():
    """API สำหรับ Admin: ดูรายการจองทั้งหมด พร้อมข้อมูลลูกค้า"""
    bookings = Booking.query.order_by(Booking.booking_date.asc(), Booking.booking_time.asc()).all()
    
    return jsonify([b.to_dict() for b in bookings]), 200

@app.route('/api/admin/update_status/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id):
    """API สำหรับ Admin: อัปเดตสถานะการจอง (TC-005)"""
    data = request.json
    new_status = data.get('status')
    
    booking = Booking.query.get(booking_id)
    
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
        
    # **** แก้ไข: ใช้สถานะ 8 ขั้นตอนในการตรวจสอบความถูกต้อง ****
    if new_status not in STATUS_ORDER_DETAIL_PYTHON:
        return jsonify({'error': 'สถานะไม่ถูกต้อง: ' + new_status}), 400

    try:
        booking.status = new_status
        db.session.commit()
        
        print(f"\n[NOTIFICATION MOCK] Status updated for Booking ID {booking_id} to {new_status}. Notifying customer: {booking.customer.email}")
        
        return jsonify({'message': f'Status updated to {new_status} successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update status', 'details': str(e)}), 500

# --- การรัน Flask App ---
if __name__ == '__main__':
    # *** ขั้นตอนสำคัญ: ลบไฟล์ฐานข้อมูลเดิม (site.db) ทิ้งก่อนรัน
    # เพื่อให้ Model ถูกสร้างใหม่ด้วยขนาดคอลัมน์ status ที่ถูกต้อง
    with app.app_context():
        db.create_all() 
    app.run(debug=True, port=5000)