# FloatChat ARGO - AI Ocean Data Intelligence

FloatChat ARGO is a comprehensive full-stack web application that provides AI-powered conversational interfaces for exploring and analyzing oceanographic data from the global ARGO float network.

## 🌊 Features

### Frontend
- **Responsive Web Interface**: Modern, ocean-themed design
- **Role-Based Access**: Separate user and admin dashboards
- **Interactive Maps**: Real-time ARGO float locations with Leaflet.js
- **AI Chatbot**: Natural language queries about ocean data
- **Data Visualization**: Temperature and salinity profile charts

### Backend
- **Flask REST API**: Complete RESTful web services
- **JWT Authentication**: Secure token-based user authentication
- **Multi-Database Architecture**: MySQL + MongoDB + FAISS Vector DB
- **File Processing**: NetCDF to CSV converter with progress tracking
- **Vector Search**: Semantic search for intelligent chat responses

### Database
- **MySQL**: Structured data (users, floats, profiles)
- **MongoDB**: Unstructured data (chat logs, system logs)
- **Vector Database**: AI embeddings for chatbot functionality

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js (for development)
- MySQL/MariaDB
- MongoDB
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/floatchat-argo.git
   cd floatchat-argo
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   # MySQL
   mysql -u root -p < database/mysql_setup.sql

   # MongoDB
   mongo floatchat < database/mongodb_setup.js
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Run the Application**
   ```bash
   # Backend
   cd backend
   python app.py

   # Frontend (serve static files)
   cd frontend
   python -m http.server 8000
   ```

6. **Access the Application**
   - Frontend: http://localhost:8000
   - Backend API: http://localhost:5000

## 👥 User Roles

### User Account
- **Username**: `user`
- **Password**: `user123`
- **Features**: Chat with AI, view ARGO locations, explore ocean maps

### Admin Account  
- **Username**: `admin`
- **Password**: `admin123`
- **Features**: All user features plus system management, file conversion, user management

## 📁 Project Structure

```
FloatChat-ARGO-FullStack/
├── frontend/                 # Frontend web application
│   ├── index.html           # Main HTML file
│   ├── style.css            # Styling and responsive design
│   └── app.js               # JavaScript application logic
├── backend/                 # Python Flask backend
│   ├── app.py               # Main Flask application
│   ├── config.py            # Configuration settings
│   ├── vector_db.py         # Vector database management
│   ├── nc_converter.py      # NetCDF file converter
│   └── requirements.txt     # Python dependencies
├── database/                # Database setup scripts
│   ├── mysql_setup.sql      # MySQL schema and sample data
│   └── mongodb_setup.js     # MongoDB collections and indexes
├── docs/                    # Documentation
└── README.md                # This file
```

## 🔧 API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/register` - User registration

### ARGO Data
- `GET /api/floats` - Get all ARGO floats
- `POST /api/floats` - Add new float (admin only)
- `GET /api/profiles/<float_id>` - Get profiles for specific float

### Chat System
- `POST /api/chat` - Send chat message to AI
- `GET /api/admin/system-status` - Get system health metrics (admin only)

### File Management
- `POST /api/admin/convert-nc` - Convert NetCDF files to CSV (admin only)
- `POST /api/admin/chatbot-training` - Update chatbot training data (admin only)

## 🛠️ Technology Stack

### Frontend
- HTML5, CSS3, JavaScript ES6+
- Leaflet.js for interactive maps
- Chart.js for data visualization
- Responsive design with CSS Grid/Flexbox

### Backend
- Flask (Python web framework)
- SQLAlchemy (MySQL ORM)
- PyMongo (MongoDB client)
- FAISS (Vector similarity search)
- Sentence Transformers (Text embeddings)
- xarray & pandas (NetCDF processing)

### Databases
- **MySQL/MariaDB**: User data, ARGO floats, ocean profiles
- **MongoDB**: Chat logs, system logs, conversion history
- **FAISS Vector DB**: Semantic search for AI responses

## 📊 Sample Data

The application includes sample ARGO float data from the Indian Ocean:
- 5 sample floats with realistic coordinates
- Temperature and salinity profiles
- Battery levels and maintenance schedules
- Quality control flags

## 🔒 Security Features

- JWT token-based authentication
- Role-based access control (RBAC)
- SQL injection prevention with SQLAlchemy
- Password hashing with Werkzeug
- File upload validation and sanitization

## 🌐 Deployment

### Development
```bash
# Backend
cd backend && python app.py

# Frontend  
cd frontend && python -m http.server 8000
```

### Production
```bash
# Backend with Gunicorn
cd backend && gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Frontend with Nginx (recommended)
# Configure Nginx to serve frontend static files
```

## 📝 Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://user:password@localhost/floatchat
MONGODB_URI=mongodb://localhost:27017/floatchat
UPLOAD_FOLDER=uploads
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For support and questions:
- Create an issue on GitHub
- Email: support@floatchat.org
- Documentation: [Wiki](https://github.com/your-repo/floatchat-argo/wiki)

## 🎯 Roadmap

- [ ] Real-time data streaming
- [ ] Advanced ML models for ocean prediction
- [ ] Integration with satellite data
- [ ] Multi-language support
- [ ] Mobile app development
- [ ] Docker containerization

---

**FloatChat ARGO** - Democratizing access to ocean data through AI-powered conversations.
