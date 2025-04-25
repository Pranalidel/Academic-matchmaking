from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mvp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100), nullable=False)  
    email = db.Column(db.String(120), unique=True, nullable=False) 
    role = db.Column(db.String(50), nullable=False)  

    def __repr__(self):
        return f"<User {self.name}>"

# Define the Opportunity model
class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    title = db.Column(db.String(150), nullable=False)  
    description = db.Column(db.Text, nullable=False)  
    academic_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 

    academic = db.relationship('User', backref='opportunities')

    def __repr__(self):
        return f"<Opportunity {self.title}>"
    
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

if __name__ == '__main__':
    app.run(debug=True)


# Endpoint to add a new user
@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(name=data['name'], email=data['email'], role=data['role'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

# Endpoint to add a new research opportunity
@app.route('/opportunities', methods=['POST'])
def add_opportunity():
    data = request.get_json()
    # Validate that the academic user exists and has the correct role
    academic = User.query.get(data['academic_id'])
    if not academic or academic.role != 'academic':
        return jsonify({'message': 'Invalid academic user'}), 400
    # Create a new opportunity
    new_opportunity = Opportunity(
        title=data['title'], 
        description=data['description'], 
        academic_id=data['academic_id']
    )
    db.session.add(new_opportunity)
    db.session.commit()
    return jsonify({'message': 'Opportunity created successfully'}), 201

# GET Endpoints
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        })
    return jsonify(user_list), 200

@app.route('/opportunities', methods=['GET'])
def get_opportunities():
    opportunities = Opportunity.query.all()
    opportunity_list = []
    for opp in opportunities:
        opportunity_list.append({
            'id': opp.id,
            'title': opp.title,
            'description': opp.description,
            'academic_id': opp.academic_id
        })
    return jsonify(opportunity_list), 200

# NEW MATCHING ENDPOINT
@app.route('/match/fuzzy', methods=['GET'])
def fuzzy_match():
    students = User.query.filter_by(role='student').all()
    opportunities = Opportunity.query.all()
    matches = []

    for student in students:
        if not student.interests:
            continue
        for opp in opportunities:
            score = fuzz.partial_ratio(student.interests.lower(), opp.description.lower())
            if score > 60:
                matches.append({
                    'student_id': student.id,
                    'student_name': student.name,
                    'interests': student.interests,
                    'opportunity_title': opp.title,
                    'opportunity_description': opp.description,
                    'match_score': score
                })

    return jsonify(matches), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
