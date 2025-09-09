from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import xarray as xr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import jwt
import os
from functools import wraps
import json
from sentence_transformers import SentenceTransformer
import faiss

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/floatchat'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# MongoDB connection
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['floatchat']
chat_collection = mongo_db['chat_logs']
system_logs = mongo_db['system_logs']
conversion_logs = mongo_db['conversion_logs']

# Vector database setup
model = SentenceTransformer('all-MiniLM-L6-v2')
dimension = 384
vector_index = faiss.IndexFlatL2(dimension)

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

class ArgoFloat(db.Model):
    __tablename__ = 'argo_floats'
    id = db.Column(db.Integer, primary_key=True)
    float_id = db.Column(db.String(20), unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    deployment_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')
    last_profile = db.Column(db.Date)
    profiles_count = db.Column(db.Integer, default=0)
    region = db.Column(db.String(50))
    battery_level = db.Column(db.Integer, default=100)
    next_maintenance = db.Column(db.Date)
    data_quality = db.Column(db.String(20), default='good')

class OceanProfile(db.Model):
    __tablename__ = 'ocean_profiles'
    id = db.Column(db.Integer, primary_key=True)
    float_id = db.Column(db.String(20), db.ForeignKey('argo_floats.float_id'))
    profile_date = db.Column(db.DateTime, default=datetime.utcnow)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    depth = db.Column(db.Float)
    temperature = db.Column(db.Float)
    salinity = db.Column(db.Float)
    pressure = db.Column(db.Float)
    oxygen = db.Column(db.Float)
    quality_flag = db.Column(db.String(5))

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

# Vector database functions
def add_to_vector_db(text, metadata):
    """Add text embedding to FAISS index"""
    embedding = model.encode([text])
    vector_index.add(embedding)

    # Store metadata in MongoDB
    mongo_db.vector_metadata.insert_one({
        'index': vector_index.ntotal - 1,
        'text': text,
        'metadata': metadata,
        'created_at': datetime.utcnow()
    })

def search_vector_db(query, top_k=5):
    """Search vector database for similar content"""
    if vector_index.ntotal == 0:
        return []

    query_embedding = model.encode([query])
    distances, indices = vector_index.search(query_embedding, min(top_k, vector_index.ntotal))

    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1:
            metadata_doc = mongo_db.vector_metadata.find_one({'index': int(idx)})
            if metadata_doc:
                results.append({
                    'text': metadata_doc['text'],
                    'metadata': metadata_doc['metadata'],
                    'distance': float(distances[0][i])
                })
    return results

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        # Validate input
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password required'}), 400

        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 409

        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role=data.get('role', 'user'),
            full_name=data.get('full_name', data['username'])
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()

        if user and check_password_hash(user.password_hash, data['password']):
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Create JWT token
            token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'full_name': user.full_name
                }
            })

        return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/floats', methods=['GET'])
@token_required
def get_floats(current_user):
    try:
        floats = ArgoFloat.query.all()
        return jsonify([{
            'id': f.id,
            'float_id': f.float_id,
            'latitude': f.latitude,
            'longitude': f.longitude,
            'status': f.status,
            'deployment_date': f.deployment_date.isoformat() if f.deployment_date else None,
            'last_profile': f.last_profile.isoformat() if f.last_profile else None,
            'region': f.region,
            'battery_level': f.battery_level,
            'data_quality': f.data_quality
        } for f in floats])

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/floats', methods=['POST'])
@token_required
@admin_required
def add_float(current_user):
    try:
        data = request.get_json()

        float_obj = ArgoFloat(
            float_id=data['float_id'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            status=data.get('status', 'active'),
            region=data.get('region', ''),
            battery_level=data.get('battery_level', 100),
            data_quality=data.get('data_quality', 'good')
        )

        db.session.add(float_obj)
        db.session.commit()

        # Add to vector database
        text = f"ARGO float {data['float_id']} located at {data['latitude']}, {data['longitude']}"
        add_to_vector_db(text, {'type': 'float', 'float_id': data['float_id']})

        return jsonify({'message': 'Float added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@token_required
def chat_query(current_user):
    try:
        data = request.get_json()
        query = data.get('message', '')

        # Search vector database for relevant context
        relevant_docs = search_vector_db(query, top_k=5)

        # Generate response based on query
        response = generate_argo_response(query, relevant_docs)

        # Log chat interaction
        chat_log = {
            'user_id': current_user.id,
            'query': query,
            'response': response,
            'relevant_docs': relevant_docs,
            'timestamp': datetime.utcnow()
        }
        chat_collection.insert_one(chat_log)

        return jsonify({
            'response': response,
            'sources': relevant_docs[:3]  # Return top 3 sources
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_argo_response(query, context_docs):
    """Generate AI-style response for ARGO queries"""
    query_lower = query.lower()

    # Get some statistics from database
    total_floats = ArgoFloat.query.count()
    active_floats = ArgoFloat.query.filter_by(status='active').count()

    # Response templates based on query type
    if 'temperature' in query_lower:
        return f"Based on data from {active_floats} active ARGO floats, I found temperature profiles showing surface temperatures ranging from 25°C to 29°C. The thermocline typically occurs between 80-120m depth, with deeper waters cooling to 2-4°C at 2000m depth."

    elif 'salinity' in query_lower:
        return f"Salinity measurements from {active_floats} floats show typical values between 34.9-35.3 PSU (Practical Salinity Units). Higher salinity values are often observed in regions with high evaporation and limited freshwater input."

    elif 'location' in query_lower or 'float' in query_lower:
        return f"Currently tracking {total_floats} ARGO floats with {active_floats} actively reporting. These autonomous instruments are distributed across ocean basins, providing continuous temperature and salinity profiles every 10 days."

    elif 'profile' in query_lower:
        return "Ocean profiles from ARGO floats reveal typical oceanic stratification: warm surface mixed layer, sharp thermocline/halocline, and stable deep waters. Each profile extends from surface to 2000m depth."

    else:
        return f"I can help you explore ARGO float data including temperature, salinity, float locations, and ocean profiles. Currently monitoring {active_floats} active floats. What specific aspect of ocean data interests you?"

@app.route('/api/profiles/<float_id>', methods=['GET'])
@token_required
def get_profiles(current_user, float_id):
    try:
        profiles = OceanProfile.query.filter_by(float_id=float_id).order_by(
            OceanProfile.profile_date.desc()
        ).limit(50).all()

        return jsonify([{
            'id': p.id,
            'profile_date': p.profile_date.isoformat() if p.profile_date else None,
            'latitude': p.latitude,
            'longitude': p.longitude,
            'depth': p.depth,
            'temperature': p.temperature,
            'salinity': p.salinity,
            'pressure': p.pressure,
            'oxygen': p.oxygen
        } for p in profiles])

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/convert-nc', methods=['POST'])
@token_required
@admin_required
def convert_netcdf(current_user):
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.nc'):
            return jsonify({'error': 'File must be NetCDF format (.nc)'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        try:
            # Convert NetCDF to CSV
            ds = xr.open_dataset(filepath)
            df = ds.to_dataframe().reset_index()

            # Generate CSV filename
            csv_filename = filename.replace('.nc', '.csv')
            csv_filepath = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
            df.to_csv(csv_filepath, index=False)

            # Log conversion
            conversion_log = {
                'user_id': current_user.id,
                'original_file': filename,
                'csv_file': csv_filename,
                'rows': len(df),
                'columns': len(df.columns),
                'status': 'success',
                'timestamp': datetime.utcnow()
            }
            conversion_logs.insert_one(conversion_log)

            return jsonify({
                'message': 'File converted successfully',
                'csv_file': csv_filename,
                'rows': len(df),
                'columns': len(df.columns)
            })

        except Exception as e:
            # Log failed conversion
            conversion_logs.insert_one({
                'user_id': current_user.id,
                'original_file': filename,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })
            return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/chatbot-training', methods=['POST'])
@token_required
@admin_required
def update_chatbot_training(current_user):
    try:
        data = request.get_json()
        training_data = data.get('training_data', [])

        # Add training data to vector database
        for item in training_data:
            if 'question' in item and 'answer' in item:
                text = f"Q: {item['question']} A: {item['answer']}"
                metadata = {
                    'type': 'training',
                    'category': item.get('category', 'general'),
                    'updated_by': current_user.id
                }
                add_to_vector_db(text, metadata)

        # Log training update
        system_logs.insert_one({
            'action': 'chatbot_training_update',
            'user_id': current_user.id,
            'training_items': len(training_data),
            'timestamp': datetime.utcnow()
        })

        return jsonify({
            'message': f'Added {len(training_data)} training items to chatbot database'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/system-status', methods=['GET'])
@token_required
@admin_required
def system_status(current_user):
    try:
        # Database statistics
        total_floats = ArgoFloat.query.count()
        active_floats = ArgoFloat.query.filter_by(status='active').count()
        total_users = User.query.count()
        total_profiles = OceanProfile.query.count()

        # MongoDB statistics
        chat_count = chat_collection.count_documents({})
        conversion_count = conversion_logs.count_documents({})

        return jsonify({
            'database': {
                'total_floats': total_floats,
                'active_floats': active_floats,
                'total_users': total_users,
                'total_profiles': total_profiles
            },
            'mongodb': {
                'chat_logs': chat_count,
                'conversions': conversion_count,
                'vector_db_size': vector_index.ntotal
            },
            'system': {
                'uptime': '99.9%',
                'last_update': datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    try:
        users = User.query.all()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'full_name': u.full_name,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'last_login': u.last_login.isoformat() if u.last_login else None
        } for u in users])

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize database and add sample data
@app.before_first_request
def create_tables():
    db.create_all()

    # Create default users if they don't exist
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@floatchat.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            full_name='System Administrator'
        )
        db.session.add(admin_user)

    if not User.query.filter_by(username='user').first():
        regular_user = User(
            username='user',
            email='user@floatchat.com',
            password_hash=generate_password_hash('user123'),
            role='user',
            full_name='Marine Researcher'
        )
        db.session.add(regular_user)

    # Add sample ARGO floats
    sample_floats = [
        {'float_id': '2901623', 'lat': -10.5, 'lng': 67.8, 'region': 'Indian Ocean'},
        {'float_id': '2901624', 'lat': -15.2, 'lng': 72.1, 'region': 'Indian Ocean'},
        {'float_id': '2901625', 'lat': -8.7, 'lng': 65.3, 'region': 'Indian Ocean'},
        {'float_id': '2901626', 'lat': -12.8, 'lng': 70.5, 'region': 'Indian Ocean'},
        {'float_id': '2901627', 'lat': -6.2, 'lng': 68.9, 'region': 'Indian Ocean'}
    ]

    for float_data in sample_floats:
        if not ArgoFloat.query.filter_by(float_id=float_data['float_id']).first():
            argo_float = ArgoFloat(
                float_id=float_data['float_id'],
                latitude=float_data['lat'],
                longitude=float_data['lng'],
                region=float_data['region'],
                status='active',
                battery_level=np.random.randint(70, 100),
                data_quality='good'
            )
            db.session.add(argo_float)

    db.session.commit()

    # Initialize vector database with ARGO knowledge
    initialize_vector_db()

def initialize_vector_db():
    """Initialize vector database with ARGO domain knowledge"""
    if vector_index.ntotal == 0:
        knowledge_base = [
            {
                'text': 'ARGO floats are autonomous instruments that collect temperature and salinity profiles from the ocean surface to 2000m depth',
                'metadata': {'type': 'definition', 'topic': 'argo'}
            },
            {
                'text': 'Temperature profiles show oceanic thermal structure with warm surface waters and cooler deep waters',
                'metadata': {'type': 'explanation', 'topic': 'temperature'}
            },
            {
                'text': 'Salinity measurements indicate the salt content of seawater measured in Practical Salinity Units (PSU)',
                'metadata': {'type': 'explanation', 'topic': 'salinity'}
            },
            {
                'text': 'ARGO floats cycle every 10 days, profiling from 2000m depth to surface while measuring T and S',
                'metadata': {'type': 'process', 'topic': 'cycle'}
            },
            {
                'text': 'The Indian Ocean contains numerous ARGO floats monitoring monsoon effects and ocean circulation',
                'metadata': {'type': 'regional', 'topic': 'indian_ocean'}
            }
        ]

        for item in knowledge_base:
            add_to_vector_db(item['text'], item['metadata'])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
