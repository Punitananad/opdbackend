import os
from flask import Flask, render_template, redirect, url_for, flash, request,abort,jsonify,session
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from math import ceil



app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
csrf = CSRFProtect(app)
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()


# Models        
class User(db.Model,UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    mobile = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __init__(self, name, email, mobile, password):
        self.name = name
        self.email = email
        self.mobile = mobile
        self.password = password
        
class MedicineInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    total_quantity = db.Column(db.Integer, nullable=False, default=0)
    used_quantity = db.Column(db.Integer, nullable=False, default=0)
    
    def available_quantity(self):
        return self.total_quantity - self.used_quantity



class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    remarks = db.Column(db.String(200))
    qty = db.Column(db.Integer)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_profile.id'), nullable=False)
    added_on = db.Column(db.DateTime, default=datetime.utcnow)  

    def __init__(self, name, dosage, frequency, duration, remarks, qty, patient_id):
        self.name = name
        self.dosage = dosage
        self.frequency = frequency
        self.duration = duration
        self.remarks = remarks
        self.qty = qty
        self.patient_id = patient_id
    

class Patient_profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    gender = db.Column(db.Text)
    state = db.Column(db.Text)
    phn_no = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    age = db.Column(db.Integer)
    blood_group = db.Column(db.Text)
    fathers_name = db.Column(db.Text)
    section = db.Column(db.Text)
    can_view_records = db.Column(db.Boolean, default=True, nullable=False, server_default='1')  # Add this column
    patient = db.relationship('Beddb', backref='patient_profile', lazy=True)
    medicines = db.relationship('Medicine', backref='patient_profile', lazy=True)  

    def __init__(self, name, gender, state, phn_no, weight, age, blood_group, fathers_name, section, can_view_records=True):
        self.name = name
        self.gender = gender
        self.state = state
        self.phn_no = phn_no
        self.weight = weight
        self.age = age
        self.blood_group = blood_group
        self.fathers_name = fathers_name
        self.section = section
        self.can_view_records = can_view_records

        
class Patient_details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    gender = db.Column(db.Text)
    state = db.Column(db.Text)
    phn_no = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    age = db.Column(db.Integer)
    blood_group = db.Column(db.Text)
    fathers_name = db.Column(db.Text)
    section = db.Column(db.Text)
    can_view_records = db.Column(db.Boolean, default=True, nullable=False, server_default='1')

    def __init__(self, name, gender, state, phn_no, weight, age, blood_group, fathers_name,section):
        self.name = name
        self.gender = gender
        self.state = state
        self.phn_no = phn_no
        self.weight = weight
        self.age = age
        self.blood_group = blood_group
        self.fathers_name = fathers_name
        self.section = section


class Floordb(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor_count = db.Column(db.Integer, unique=True)
    beds = db.relationship('Beddb', backref='floordb')

    def __init__(self, floor_count):
        self.floor_count = floor_count
# Convert UTC to IST
from datetime import datetime
import pytz

# Function to convert a string date to a datetime object and convert to IST
def convert_to_ist(date_str):
    # Convert the string to a datetime object (assuming it's in UTC)
    utc_datetime = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    
    # Convert to IST timezone
    ist_timezone = pytz.timezone('Asia/Kolkata')
    ist_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(ist_timezone)
    return ist_datetime





class Beddb(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bed_number = db.Column(db.Integer, nullable=False)
    is_allotted = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    floor_id = db.Column(db.Integer, db.ForeignKey('floordb.id'))  # Ensure foreign key relationship is correct
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_profile.id'))
    allotted_by = db.Column(db.String(100))

    def __init__(self, bed_number, floor_id, patient_id=None, allotted_by=None):
        self.bed_number = bed_number
        self.floor_id = floor_id
        self.patient_id = patient_id
        self.allotted_by = allotted_by
        
 

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/addpatient', methods=['GET', 'POST'])
@login_required
def addpatient():
    if request.method == "POST":
        name = request.form.get('name')
        gender = request.form.get('gender')
        state = request.form.get('state')
        phn_no = request.form.get('phn_no')
        weight = request.form.get('weight')
        age = request.form.get('age')
        blood = request.form.get('blood')
        f_name = request.form.get('f_name')
        section = request.form.get('section')
        
        new_patient = Patient_details(name=name, gender=gender, state=state, phn_no=phn_no, weight=weight, age=age, blood_group=blood, fathers_name=f_name, section=section)
        db.session.add(new_patient)
        db.session.commit()
        
        patient_profile = Patient_profile(name=name, gender=gender, state=state, phn_no=phn_no, weight=weight, age=age, blood_group=blood, fathers_name=f_name, section=section)
        db.session.add(patient_profile)
        db.session.commit()

        print_option = request.form.get('print')
        if print_option == 'yes':
            return render_template('print_template.html', name=name, gender=gender, state=state, phn_no=phn_no, weight=weight, age=age, blood=blood, section=section, f_name=f_name)
        
        flash(f"{name} added successfully!")
        return redirect(url_for('addpatient'))
    
    return render_template('addpatient.html')



@app.route('/queue', methods=['GET'])
@login_required
def queue_by_section():
    section = request.args.get('section', 'All Sections')  # Default to 'All Sections' if not provided

    # Only allow specific sections to prevent unexpected values
    allowed_sections = ['General Medicine', 'Pediatrics', 'Orthopedics', 'Cardiology', 'All Sections']
    if section not in allowed_sections:
        section = 'All Sections'  # Fallback to default

    # Continue with fetching patients and rendering the template
    if section == 'All Sections':
        all_patients = Patient_details.query.filter_by(can_view_records=True).all()
    else:
        all_patients = Patient_details.query.filter_by(section=section, can_view_records=True).all()

    total_patients = len(all_patients)
    return render_template('queue.html', all_patients=all_patients, total_patients=total_patients, section=section)





@app.route('/queue/all')
@login_required
def queue_all_sections():
    # Get all patients who can view records
    all_patients = Patient_details.query.filter_by(can_view_records=True).order_by(Patient_details.id.desc()).all()
    total_patients = len(all_patients)
    return render_template('queue.html', all_patients=all_patients, total_patients=total_patients, section="All Sections")


@app.route('/delete_patient/<int:id>', methods=['POST'])
@login_required
def delete_patient(id):
    patient = Patient_details.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    flash(f"Patient {patient.name} has been deleted.")
    
    section = request.args.get('section', 'All Sections')  # Get section from query parameters
    return redirect(url_for('queue_by_section', section=section))
@app.route('/reschedule/<int:id>', methods=['POST'])
@login_required
def reschedule_patient(id):
    # Fetch the patient details to be rescheduled
    patient = Patient_details.query.get_or_404(id)
    
    # Delete the old patient record
    db.session.delete(patient)
    db.session.commit()
    
    # Create a new record with the same details but without the ID
    new_patient = Patient_details(
        name=patient.name,
        gender=patient.gender,
        state=patient.state,
        phn_no=patient.phn_no,
        weight=patient.weight,
        age=patient.age,
        blood_group=patient.blood_group,
        fathers_name=patient.fathers_name,
        # Make sure the section field exists if you're including it
        section=patient.section
    )
    
    # Add and commit the new patient record
    db.session.add(new_patient)
    db.session.commit()
    
    flash('Patient rescheduled successfully.', 'success')
    
    # Ensure that 'home' is the correct endpoint name
    try:
        section = request.args.get('section', 'All Sections')  # Get section from query parameters
        return redirect(url_for('queue_by_section', section=section))
    except Exception as e:
        # Print error for debugging
        print(f"Error during redirect: {e}")
        flash('An error occurred during redirection.', 'error')
        return redirect(url_for('home'))  # or any other fallback route




@app.route('/mark_done/<int:id>', methods=['POST'])
@login_required
def mark_done(id):
    # Fetch the patient from Patient_profile
    patient = Patient_details.query.get_or_404(id)
    
    # Assuming 'Patient_details' is a related model or you can create a new entry if necessary
    patient_details = Patient_details.query.filter_by(id=id).first()
    
    if patient_details:
        # Update the status in Patient_details
        patient_details.status = 'Done'
        db.session.commit()
    
    # Hide patient from the queue by setting can_view_records to False
    patient.can_view_records = False
    db.session.commit()
    
    flash(f"Patient {patient.name} has been marked as DONE.")
    
    section = request.args.get('section', 'All Sections')  # Get section from query parameters
    return redirect(url_for('queue_by_section', section=section))



@app.route('/bedinfo')
@login_required
def bedinfo():
    # Get all floors
    floors = Floordb.query.all()
    # Fetch the floor_count parameter from the request, default to None if not provided
    floor_count_param = request.args.get('floor_count', type=int)  # To avoid confusion, renamed it to floor_count_param
    
    # Create a list to store information about each floor
    floor_data = []

    for floor in floors:
        # Get the total number of beds for each floor
        total_beds = Beddb.query.filter_by(floor_id=floor.id).count()
        # Get the number of allotted beds for each floor
        allotted_beds = Beddb.query.filter_by(floor_id=floor.id, is_allotted=True).count()
        # Get the number of non-allotted beds for each floor
        non_allotted_beds = total_beds - allotted_beds
        
        # Append data to floor_data list
        floor_data.append({
            'floor_count': floor.floor_count,  # Using floor_count attribute correctly
            'total_beds': total_beds,
            'allotted_beds': allotted_beds,
            'non_allotted_beds': non_allotted_beds
        })
    
    # Fetch non-allotted beds across all floors if needed for further processing
    non_allotted_beds_all_floors = Beddb.query.filter_by(is_allotted=False).all()

    # Render the template with the collected data
    return render_template(
        'beds.html', 
        floor_count=floor_count_param, 
        floors=floor_data, 
        floor_data=floor_data,  # Pass the calculated data for each floor
        non_allotted_beds=non_allotted_beds_all_floors
    )
    

@app.route('/floorinfo', methods=['GET', 'POST'])
@login_required
def floorinfo():
    existing_floors = Floordb.query.count()

    if existing_floors > 0:
        return redirect(url_for('bedinfo', floor_count=existing_floors))

    if request.method == "POST":
        floor_input = request.form.get('floor')
        if floor_input and floor_input.isnumeric():
            floor_input = int(floor_input)
            for data in range(1, floor_input + 1):
                if not Floordb.query.filter_by(floor_count=data).first():
                    floor_data = Floordb(floor_count=data)
                    db.session.add(floor_data)
            db.session.commit()
            return redirect(url_for('bedinfo', floor_count=floor_input))
        else:
            flash("Please enter a valid number of floors.", 'error')

    return render_template('floorinfo.html')


@app.route('/floor/<int:floor_number>', methods=['GET', 'POST'])
@login_required
def floordata(floor_number):
    floor = Floordb.query.get_or_404(floor_number)
    bedcount = None
    if request.method == 'POST':
        bedcount = request.form.get('bedcount')
        if bedcount.isdigit():
            bedcount = int(bedcount)
            for i in range(1, bedcount + 1):
                bed_instance = Beddb(bed_number=i, floor_id=floor.id)
                db.session.add(bed_instance)
            db.session.commit()
            flash(f"{bedcount} beds added to floor {floor_number}.")
        else:
            flash("Invalid bed count. Please enter a number.")

    beds = Beddb.query.filter_by(floor_id=floor.id).all()
    return render_template('floordata.html', floor_number=floor_number, bedcount=bedcount, beds=beds)

@app.route('/manage_floors', methods=['GET', 'POST'])
@login_required
def manage_floors():
    floors = Floordb.query.all()

    # Check if floors exist and render the 'add_first_floor' template if none exist
    if request.method == 'GET' and not floors:
        return render_template('add_first_floor.html')

    if request.method == 'POST':
        # Adding a new floor
        if 'add_floor' in request.form:
            floor_input = request.form.get('floor')
            if floor_input and floor_input.isdigit():
                floor_data = Floordb(floor_count=int(floor_input))
                db.session.add(floor_data)
                db.session.commit()
                flash(f"Floor {floor_input} added successfully!")
                return redirect(url_for('manage_floors'))
            else:
                flash("Please enter a valid floor number.")


    # Render the 'manage_floors' template with existing floors
    return render_template('manage_floors.html', floors=floors)

@app.route('/delete_floor/<int:floor_id>', methods=['POST'])
@login_required
def delete_floor(floor_id):
    # Fetch the floor object from the database using the floor_id from the URL
    floor_to_delete = Floordb.query.get(floor_id)
    
    if floor_to_delete:
        # Find all beds associated with the floor to be deleted
        beds_to_unassign = Beddb.query.filter_by(floor_id=floor_id).all()
        for bed in beds_to_unassign:
            # Clear the necessary fields while keeping the floor_id
            bed.floor_id = None  # or you can set it to a default floor ID if applicable
            bed.is_allotted = False
            bed.patient_id = None
            bed.allotted_by = None

        # Delete the floor
        db.session.delete(floor_to_delete)
        db.session.commit()
        flash(f"Floor {floor_to_delete.floor_count} deleted successfully!")
    else:
        flash('Floor not found.')

    return redirect(url_for('manage_floors'))




@app.route('/view_all', methods=['GET', 'POST'])
@login_required
def view_all():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of patients to display per page
    
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        search_by = request.form.get('search_by')

        if search_by == 'id':
            query = Patient_profile.query.filter(Patient_profile.id == search_query)
        elif search_by == 'name':
            query = Patient_profile.query.filter(Patient_profile.name.ilike(f'%{search_query}%'))
        elif search_by == 'phn_no':
            try:
                phn_no_query = int(search_query)  # Convert search query to integer
                query = Patient_profile.query.filter(Patient_profile.phn_no == phn_no_query)
            except ValueError:
                # Handle the case where the search query is not a valid integer
    
                query = Patient_profile.query.filter(False)  # This will return an empty query set

        else:
            query = Patient_profile.query.order_by(Patient_profile.id.desc())
    else:
        query = Patient_profile.query.order_by(Patient_profile.id.desc())
    
    # Apply pagination to the query
    total = query.count()
    all_db = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('all_users.html', all_db=all_db.items, page=page, total_pages=ceil(total / per_page))



@app.route('/profilepage/<int:id>', methods=['GET', 'POST'])
@login_required
def profilepage(id):
    # Validate patient ID
    if id <= 0:
        abort(400, description="Invalid Patient ID")
    
    # Fetch the patient by ID
    patient = Patient_profile.query.get(id)
    
    # Handle case where patient is not found
    if patient is None:
        abort(404, description="No patient found with the given ID")
    
    # Fetch all medicines
    medicines = MedicineInventory.query.all()  # Replace with your actual query method
    
    # Render profile page with patient and medicines details
    return render_template('profilepage.html', patient=patient, medicines=medicines)


@app.route('/delete_patient_permanently/<int:id>', methods=['POST'])
@login_required
def delete_patient_permanently(id):
    # Retrieve the patient profile or return a 404 if not found
    patient = Patient_profile.query.get_or_404(id)
    
    # Delete associated medicines
    Medicine.query.filter_by(patient_id=id).delete()
    
    # Free up the bed associated with the patient, if any
    bed = Beddb.query.filter_by(allotted_by=id).first()
    if bed:
        # Update the bed's status
        bed.is_allotted = False
        bed.patient_id = None
        bed.allotted_by = None
        db.session.add(bed)  # Ensure the bed update is added to the session

    # Delete the patient
    db.session.delete(patient)
    
    # Commit all changes to the database
    db.session.commit()
    
    flash(f"Patient {patient.name} and related records deleted successfully.", 'success')
    return redirect(url_for('view_all'))


@app.route('/make_appointment/<int:id>', methods=['POST'])
@login_required
def make_appointment(id):
    patient_profile = Patient_profile.query.get_or_404(id)
    new_appointment = Patient_details(
        name=patient_profile.name,
        gender=patient_profile.gender,
        state=patient_profile.state,
        phn_no=patient_profile.phn_no,
        weight=patient_profile.weight,
        age=patient_profile.age,
        blood_group=patient_profile.blood_group,
        fathers_name=patient_profile.fathers_name,
        section=patient_profile.section  # Added missing field
    )
    db.session.add(new_appointment)
    db.session.commit()
    flash(f"Appointment created for {patient_profile.name}.")
    return redirect(url_for('view_all'))


@app.route('/non_allotted_beds')
@login_required
def non_allotted_beds():
    non_allotted_beds = Beddb.query.filter_by(is_allotted=False).all()
    return render_template('non_allotted_beds.html', beds=non_allotted_beds)

@app.route('/allot_bed/<int:bed_id>', methods=['POST'])
@login_required
def allot_bed(bed_id):
    allotted_by_id = request.form.get('allotted_by')
    
    bed = Beddb.query.get_or_404(bed_id)
    
    if allotted_by_id:
        if allotted_by_id.isdigit():
            allotted_by_id = int(allotted_by_id)
            patient = Patient_profile.query.get(allotted_by_id)
            if patient:
                existing_allotment = Beddb.query.filter_by(patient_id=allotted_by_id, is_allotted=True).first()
                if existing_allotment:
                    flash('Patient ID is already allotted to another bed.', 'danger')
                else:
                    bed.is_allotted = True
                    bed.patient_id = allotted_by_id
                    bed.allotted_by = patient.name
                    db.session.commit()
                    flash('Bed successfully allotted.', 'success')
            else:
                flash('Patient ID does not exist.', 'danger')
        else:
            flash('Invalid patient ID. It must be an integer.', 'danger')
    else:
        flash('No patient ID provided.', 'danger')
    
    return redirect(url_for('floordata', floor_number=bed.floor_id))



@app.route('/unallot_bed/<int:bed_id>', methods=['POST'])
@login_required
def unallot_bed(bed_id):
    bed = Beddb.query.get_or_404(bed_id)
    
    if bed.is_allotted:
        bed.is_allotted = False
        bed.patient_id = None
        bed.allotted_by = None
        db.session.commit()
        flash('Bed successfully unallotted.', 'success')
    else:
        flash('Bed is not currently allotted.', 'warning')
    
    return redirect(url_for('floordata', floor_number=bed.floor_id))
from datetime import datetime

from datetime import datetime
import pytz


# Set your desired timezone
timezone = pytz.timezone('Asia/Kolkata')

# Get the current time in UTC
now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

# Convert to the desired timezone
now_local = now_utc.astimezone(timezone)
from datetime import datetime
import pytz

@app.route('/admin_dashboard')
def admin_dashboard():
    all_patients = Patient_profile.query.all()
    
    # Get the total number of patients
    patient_count = len(all_patients)
    
    # Print the count (useful for debugging; remove in production)
        # Get all floors
    floors = Floordb.query.all()

    # Create a list to store information about each floor
    floor_data = []
    total_non_allotted_beds = 0  # Initialize total non-allotted beds count

    for floor in floors:
        # Get the total number of beds for each floor
        total_beds = Beddb.query.filter_by(floor_id=floor.id).count()
        # Get the number of allotted beds for each floor
        allotted_beds = Beddb.query.filter_by(floor_id=floor.id, is_allotted=True).count()
        # Get the number of non-allotted beds for each floor
        non_allotted_beds = total_beds - allotted_beds

        # Update the total non-allotted beds
        total_non_allotted_beds += non_allotted_beds

        # Append data to floor_data list
        floor_data.append({
            'floor_count': floor.floor_count,
            'total_beds': total_beds,
            'allotted_beds': allotted_beds,
            'non_allotted_beds': non_allotted_beds
        })
        
    return render_template(
        'admin_dashboard.html',  # The template for the admin dashboard
        floors=floor_data,
        total_non_allotted_beds=total_non_allotted_beds ,
        total = patient_count
    )

@app.route('/medicine_history/<int:id>', methods=['GET', 'POST'])
@login_required
def medicine_history(id):
    patient = Patient_profile.query.get_or_404(id)
    medicines = Medicine.query.filter_by(patient_id=id).order_by(Medicine.added_on.desc()).all()

    # Define your timezone
    local_tz = pytz.timezone('Asia/Kolkata')

    # Initialize medicine_by_date as an empty dictionary
    medicine_by_date = {}

    for med in medicines:
        # Ensure added_on is not None
        if med.added_on:
            # Ensure med.added_on is timezone-aware
            if med.added_on.tzinfo is None:
                med.added_on = pytz.utc.localize(med.added_on)  # Convert naive datetime to UTC-aware datetime
            # Convert to the desired timezone
            added_on_local = med.added_on.astimezone(local_tz)
            # Format the date for grouping
            date_str = added_on_local.strftime('%d/%m/%Y, %I:%M %p')
        else:
            date_str = 'Unknown Date'

        if date_str not in medicine_by_date:
            medicine_by_date[date_str] = []
        medicine_by_date[date_str].append(med)

    return render_template('medicine_history.html', patient_id=id, medicine_by_date=medicine_by_date, patient=patient)




@app.route('/add_medicine_to_patient/<int:id>', methods=['POST'])
@login_required
def add_medicine_to_patient(id):
    # Retrieve form data
    med_name = request.form.get('med_name')
    dosage = request.form.get('dosage')
    freq = request.form.get('freq')
    duration = request.form.get('duration')
    qty = request.form.get('qty')
    remarks = request.form.get('remarks')
    
    # Find the patient
    patient = Patient_profile.query.get(id)
    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('view_all'))

    # Create a new medicine record
    medicine = Medicine(
        patient_id=id,
        name=med_name,
        dosage=dosage,
        frequency=freq,
        duration=duration,
        qty=qty,
        remarks=remarks
    )
    
    try:
        # Add and commit the new record to the database
        db.session.add(medicine)
        db.session.commit()
        flash('Medicine added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    
    # Redirect back to the patient's profile page
    return redirect(url_for('profilepage', id=id))

@app.route('/patient_management')
def patient_management():
    return render_template("patient_management.html")

@app.route('/save_all_medicines/<int:id>', methods=['POST'])
@login_required
def save_all_medicines(id):
    medicines = request.json

    # Find the patient
    patient = Patient_profile.query.get(id)
    if not patient:
        return jsonify({'success': False, 'message': 'Patient not found'}), 404

    try:
        for med in medicines:
            # Fetch medicine inventory
            medicine_inventory = MedicineInventory.query.filter_by(name=med['med_name']).first()
            if not medicine_inventory:
                return jsonify({'success': False, 'message': f"Medicine '{med['med_name']}' not found in inventory"}), 404

            if medicine_inventory.total_quantity < med['qty']:
                return jsonify({'success': False, 'message': f"Insufficient quantity for '{med['med_name']}'"}), 400

            # Ensure qty is an integer
            qty = int(med['qty'])
            if medicine_inventory.total_quantity < qty:
                return jsonify({'success': False, 'message': f"Insufficient quantity for '{med['med_name']}'"}), 400

# Similarly, ensure other numeric fields are converted to int where necessary

            # Create new medicine record
            patient_medicine = Medicine(
                patient_id=id,
                name=med['med_name'],
                dosage=med['dosage'],
                frequency=med['freq'],
                duration=med['duration'],
                qty=med['qty'],
                remarks=med['remarks']
            )
            db.session.add(patient_medicine)

            # Update inventory
            medicine_inventory.total_quantity -= med['qty']
        
        # Commit changes
        db.session.commit()
        return jsonify({'success': True}), 200

    except Exception as e:
        db.session.rollback()
        # Print error for debugging
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500





@app.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    return render_template('add_medicine.html')  

from flask import request, redirect, url_for, render_template, flash

# Route to add new medicine to the inventory
@app.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_inventory_medicine():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        total_quantity = request.form.get('total_quantity')

        # Validate the form inputs
        if name and total_quantity and total_quantity.isdigit() and int(total_quantity) > 0:
            total_quantity = int(total_quantity)  # Convert to an integer
            # Check if the medicine already exists in the inventory
            medicine = MedicineInventory.query.filter_by(name=name).first()

            if medicine:
                # Update existing medicine quantity
                medicine.total_quantity += total_quantity
                flash(f"Medicine '{name}' updated successfully.", "success")
            else:
                # Add new medicine
                new_medicine = MedicineInventory(name=name, total_quantity=total_quantity)
                db.session.add(new_medicine)
                flash(f"Medicine '{name}' added successfully.", "success")

            # Commit changes to the database
            db.session.commit()
        else:
            flash("Invalid input. Please enter a valid name and quantity.", "danger")

        # Redirect to the inventory view after processing
        return redirect(url_for('view_inventory'))
    
    # Render the add medicine page
    return render_template('add_inventory_medicine.html')

# Route to view inventory
@app.route('/inventory/view')
@login_required
def view_inventory():
    medicines = MedicineInventory.query.all()
    return render_template('view_inventory.html', medicines=medicines)

# Route to update inventory when assigning medicine to a user
@app.route('/inventory/assign/<int:patient_id>', methods=['POST'])
@login_required
def assign_inventory_medicine(patient_id):
    medicine_id = request.form.get('medicine_id')
    quantity = int(request.form.get('quantity'))

    # Fetch the medicine from the inventory
    medicine = MedicineInventory.query.get_or_404(medicine_id)

    if medicine.available_quantity() >= quantity:
        medicine.used_quantity += quantity
        db.session.commit()
        flash(f"{quantity} units of '{medicine.name}' assigned to patient ID {patient_id}.", "success")
    else:
        flash(f"Not enough stock available for '{medicine.name}'.", "danger")

    return redirect(url_for('profilepage', id=patient_id))


# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Ensure passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        # Create a new user instance
        new_user = User(name=name, email=email, mobile=mobile, password=password)

        # Add the new user to the session and commit it to the database
        db.session.add(new_user)
        db.session.commit()

        flash('You have successfully registered!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:  # Consider using hashed passwords in production
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your email and/or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)