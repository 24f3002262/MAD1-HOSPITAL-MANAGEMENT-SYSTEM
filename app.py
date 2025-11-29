from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random, string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------------------ Models ------------------------------

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    doctors = db.relationship('Doctor', backref='department', lazy=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    specialization = db.Column(db.String(100))
    education = db.Column(db.Text)
    experience = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)  # 08:00-12:00
    is_available = db.Column(db.Boolean, default=True)

    doctor = db.relationship('Doctor', backref='availability')


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    age = db.Column(db.Integer)
    sex = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    city = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(20), nullable=False)
    appointment_type = db.Column(db.String(50))
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='Booked')

    treatment = db.relationship(
        'Treatment',
        backref='appointment',
        uselist=False,
        cascade="all, delete-orphan"
    )

class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    visit_type = db.Column(db.String(50))
    tests_done = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    medicines = db.Column(db.Text)
    notes = db.Column(db.Text)
    followup_date = db.Column(db.Date)

# ------------------------------ Helpers ------------------------------

def generate_patient_id():
    year = datetime.now().year
    return f"HMS{year}{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def generate_appointment_id():
    return f"APT{Appointment.query.count() + 1:05d}"

# ------------------------------ Routes ------------------------------

@app.route('/')
def index():
    return render_template('index.html')

# ----------- Login System -----------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Patient.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_type'] = 'patient'
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('patient_dashboard'))
        flash('Invalid Patient Credentials', 'error')
        return redirect(url_for('login'))
    return render_template('login_form.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = Admin.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_type'] = 'admin'
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('admin_dashboard'))
        flash('Invalid Admin Credentials', 'error')
    return render_template('admin_login.html')

@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        user = Doctor.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_type'] = 'doctor'
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('doctor_dashboard'))
        flash('Invalid Doctor Credentials', 'error')
    return render_template('doctor_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        patient = Patient(
            username=request.form['username'],
            password=generate_password_hash(request.form['password']),
            patient_id=generate_patient_id(),
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            contact=request.form['mobile']
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient Registered Successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register_form.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ----------- Dashboards -----------

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    # fetch live data from database
    doctors = Doctor.query.filter_by(is_active=True).all()
    patients = Patient.query.filter_by(is_active=True).all()
    appointments = Appointment.query.order_by(
        Appointment.appointment_date, Appointment.appointment_time
    ).all()

    total_doctors = len(doctors)
    total_patients = len(patients)
    total_appointments = len(appointments)

    # small debug print – check terminal if needed
    print("ADMIN DASHBOARD →", total_doctors, "doctors,", total_patients,
          "patients,", total_appointments, "appointments")

    return render_template(
        'admin_dashboard.html',
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        doctors=doctors,
        patients=patients,
        appointments=appointments
    )


@app.route('/doctor/dashboard')
def doctor_dashboard():
    if session.get('user_type') != 'doctor':
        return redirect(url_for('login'))

    doctor_id = session['user_id']
    doctor = Doctor.query.get_or_404(doctor_id)

    appointments = Appointment.query.filter_by(
        doctor_id=doctor_id, status='Booked'
    ).all()

    patients = (
        db.session.query(Patient)
        .join(Appointment)
        .filter(Appointment.doctor_id == doctor_id)
        .distinct()
        .all()
    )

    return render_template(
        'doct_dash.html',
        doctor=doctor,
        appointments=appointments,
        patients=patients
    )


@app.route('/patient/dashboard')
def patient_dashboard():
    if session.get('user_type') != 'patient':
        return redirect(url_for('login'))
    patient = Patient.query.get(session['user_id'])
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    return render_template('patient_dash.html', patient=patient, appointments=appointments)

# ----------- Doctor Profile & Availability -----------

@app.route('/doctor/<int:doctor_id>')
def doct_profile(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('doct_profile.html', doctor=doctor)


@app.route('/doctor/availability', methods=['GET', 'POST'])
def doctor_availability():
    if session.get('user_type') != 'doctor':
        return redirect(url_for('login'))

    doctor_id = session['user_id']
    doctor = Doctor.query.get_or_404(doctor_id)

    if request.method == 'POST':
        date_str = request.form.get('date')
        time_slot = request.form.get('time_slot')  
        availability_status = request.form.get('is_available', '').strip().lower()
        is_available = (availability_status == 'true')

        if not date_str or not time_slot:
            flash("Please fill all fields.", "error")
            return redirect(url_for('doctor_availability'))

        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        new_slot = DoctorAvailability(
            doctor_id=doctor_id,
            date=date,
            time_slot=time_slot, 
            is_available=is_available,
        )

        db.session.add(new_slot)
        db.session.commit()

        return redirect(url_for('doctor_availability'))

    # Get all slots
    availability = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id
    ).order_by(DoctorAvailability.date).all()

    return render_template(
        'doct_availability.html',
        doctor=doctor,
        availability=availability
    )


@app.route('/admin/patient-history/<int:patient_id>')
def admin_patient_history(patient_id):
    if session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()

    return render_template('patient_history.html',
                           patient=patient,
                           appointments=appointments)



@app.route('/check-availability/<int:doctor_id>')
def doct_avail_patient(doctor_id):
    if session.get('user_type') != 'patient':
        return redirect(url_for('login'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    patient = Patient.query.get(session['user_id'])

    # Fetch availability slots
    availability = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id
    ).order_by(DoctorAvailability.date).all()

    return render_template(
        'doct_avail_patient.html',
        doctor=doctor,
        patient=patient,
        availability=availability 
    )



# ----------- Department & Doctors -----------

@app.route('/doctors')
def doctor_list():
    doctors = Doctor.query.filter_by(is_active=True).all()
    return render_template('doctor_list.html', doctors=doctors)

@app.route('/department/<int:dept_id>')
def deptt_details(dept_id):
    department = Department.query.get_or_404(dept_id)
    doctors = Doctor.query.filter_by(department_id=dept_id).all()
    return render_template('deptt_details.html', department=department, doctors=doctors)

# ----------- Appointment System -----------

@app.route('/book-appointment/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    # Only patients can book
    if session.get('user_type') != 'patient':
        return redirect(url_for('login'))

    patient = Patient.query.get(session['user_id'])
    doctor = Doctor.query.get_or_404(doctor_id)

    # If form submitted → save appointment
    if request.method == 'POST':
        new_appointment = Appointment(
            appointment_id=generate_appointment_id(),
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=datetime.strptime(request.form['appointment_date'], '%Y-%m-%d').date(),
            appointment_time=request.form['time_slot'],
            appointment_type=request.form['appointment_type'],
            reason=request.form['reason']
        )
        db.session.add(new_appointment)
        db.session.commit()

        flash('Appointment Booked Successfully!', 'success')
        return redirect(url_for('patient_dashboard'))

    # Data for dropdowns
    departments = Department.query.all()
    doctors = Doctor.query.filter_by(is_active=True).all()

    return render_template('book_appoinment.html',
                           patient=patient,
                           doctor=doctor,
                           departments=departments,
                           doctors=doctors)


@app.route('/cancel_appointment/<int:appt_id>', methods=['POST'])
def cancel_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'Cancelled'
    db.session.commit()
    flash('Appointment Cancelled', 'success')
    return redirect(url_for('doctor_dashboard') if session.get('user_type') == 'doctor' else url_for('patient_dashboard'))

# ----------- Treatment History -----------

@app.route('/doctor/update-treatment/<int:appointment_id>', methods=['GET', 'POST'])
def update_treatment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if session.get('user_type') != 'doctor':
        return redirect(url_for('login'))

    if request.method == 'POST':
        medicines = ', '.join(filter(None, [
            request.form.get(f"medicine_{i}") for i in range(1, 6)
        ]))
        treatment = Treatment(
            appointment_id=appointment_id,
            visit_type=request.form['visit_type'],
            diagnosis=request.form['diagnosis'],
            prescription=request.form['prescription'],
            medicines=medicines,
            tests_done=request.form.get('tests'),
            notes=request.form.get('notes'),
            followup_date=datetime.strptime(request.form['followup_date'], '%Y-%m-%d') if request.form.get('followup_date') else None
        )
        appointment.status = 'Completed'
        db.session.add(treatment)
        db.session.commit()
        flash('Treatment Updated!', 'success')
        return redirect(url_for('doctor_dashboard'))

    return render_template('update_treatment.html', appointment=appointment)

@app.route('/admin/add-doctor', methods=['GET', 'POST'])
def add_doctor():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        first = request.form['first_name']
        last = request.form['last_name']
        email = request.form['email']
        contact = request.form['contact']
        specialization = request.form['specialization']
        experience = request.form['experience']
        education = request.form['education']

        department = Department.query.filter_by(name=specialization).first()
        department_id = department.id if department else 1

        new_doctor = Doctor(
            username=username,
            password=password,
            first_name=first,
            last_name=last,
            email=email,
            contact=contact,
            specialization=specialization,
            experience=experience,
            education=education,
            department_id=department_id
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash('Doctor Added Successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_doct.html')


# doctor -> patient -> history -> appoinments
@app.route('/doctor/patient-history/<int:patient_id>')
def doctor_patient_history(patient_id):
    if session.get('user_type') != 'doctor':
        return redirect(url_for('login'))

    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()

    return render_template('patient_history.html',
                           appointments=appointments,
                           patient=patient)


# patient -> history
@app.route('/patient/history')
def patient_history():
    if session.get('user_type') != 'patient':
        return redirect(url_for('login'))

    patient_id = session.get('user_id')

    # Properly load treatment using join
    appointments = (
        Appointment.query
        .filter_by(patient_id=patient_id)
        .order_by(Appointment.appointment_date.desc())
        .all()
    )

    return render_template('patient_history.html', patient=Patient.query.get(patient_id), appointments=appointments)



# ------------------------------ Database Init ------------------------------

def init_database():
    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            admin = Admin(username='admin', password=generate_password_hash('admin123'), email='admin@hms.com')
            db.session.add(admin)
            db.session.commit()

        if Department.query.count() == 0:
            departments = [
                Department(name='Cardiology', description='Deals with heart diseases'),
                Department(name='Neurology', description='Deals with nervous system disorders'),
                Department(name='Orthopedics', description='Bones, joints, muscles, and spine care'),
                Department(name='Pediatrics', description='Medical care for children'),
                Department(name='Emergency & Critical Care', description='Emergency treatments 24/7')
            ]
            db.session.add_all(departments)
            db.session.commit()

# ------------------------------ Run App ------------------------------

if __name__ == '__main__':
    init_database()
    app.run(debug=True)
