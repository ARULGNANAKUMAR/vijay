# FloatChat ARGO Installation Guide

This guide provides detailed instructions for setting up the FloatChat ARGO system in development and production environments.

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows 10+
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for package installation

### Software Dependencies
- MySQL 5.7+ or MariaDB 10.3+
- MongoDB 4.4+
- Python 3.8+
- Git

## Step-by-Step Installation

### 1. System Preparation

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
sudo apt install mysql-server mongodb
```

#### CentOS/RHEL
```bash
sudo yum install python3 python3-pip git
sudo yum install mysql-server mongodb-server
```

#### macOS (with Homebrew)
```bash
brew install python3 git mysql mongodb
```

#### Windows
- Install Python 3.8+ from python.org
- Install Git from git-scm.com
- Install MySQL Community Server
- Install MongoDB Community Edition

### 2. Database Setup

#### MySQL Configuration
```bash
# Start MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure installation
sudo mysql_secure_installation

# Create database and user
mysql -u root -p < database/mysql_setup.sql
```

#### MongoDB Configuration
```bash
# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod

# Setup collections and indexes
mongo floatchat < database/mongodb_setup.js
```

### 3. Python Environment Setup

```bash
# Create virtual environment
python3 -m venv floatchat-env
source floatchat-env/bin/activate  # On Windows: floatchat-env\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (use your favorite editor)
nano .env
```

Update the following variables in `.env`:
```env
SECRET_KEY=your-unique-secret-key-here
DATABASE_URL=mysql://floatchat_user:your-password@localhost/floatchat
MONGODB_URI=mongodb://localhost:27017/floatchat
```

### 5. Database Initialization

```bash
# Initialize MySQL tables and sample data
cd backend
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database initialized successfully!')
"
```

### 6. Application Startup

#### Backend Server
```bash
cd backend
python app.py
```
The API will be available at http://localhost:5000

#### Frontend Server (Development)
```bash
cd frontend
python -m http.server 8000
```
The web interface will be available at http://localhost:8000

## Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run with multiple workers
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker (Alternative)

```bash
# Build Docker image
docker build -t floatchat-argo .

# Run with Docker Compose
docker-compose up -d
```

### Nginx Configuration (Frontend)

Create `/etc/nginx/sites-available/floatchat`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/floatchat/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/floatchat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Verification

### Test API Endpoints
```bash
# Health check
curl http://localhost:5000/api/health

# Login test
curl -X POST http://localhost:5000/api/login   -H "Content-Type: application/json"   -d '{"username": "user", "password": "user123"}'
```

### Test Frontend
1. Open http://localhost:8000 in your browser
2. Click "Login" and use demo credentials:
   - User: `user` / `user123`
   - Admin: `admin` / `admin123`
3. Test the chatbot with queries like "show temperature profiles"

### Test Database Connections
```bash
# MySQL test
mysql -u floatchat_user -p -e "SELECT COUNT(*) FROM floatchat.argo_floats;"

# MongoDB test
mongo floatchat --eval "db.chat_logs.count()"
```

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check MySQL service
sudo systemctl status mysql

# Check MongoDB service  
sudo systemctl status mongod

# Test connections
mysql -u floatchat_user -p floatchat
mongo floatchat
```

#### Python Package Issues
```bash
# Update pip and reinstall
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### Port Conflicts
```bash
# Check what's using ports
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :8000

# Kill processes if needed
sudo kill -9 <PID>
```

### Log Files
- Backend: Check Flask console output
- MySQL: `/var/log/mysql/error.log`
- MongoDB: `/var/log/mongodb/mongod.log`
- Nginx: `/var/log/nginx/error.log`

## Performance Optimization

### Database Indexes
```sql
-- Add indexes for better query performance
CREATE INDEX idx_profiles_float_date ON ocean_profiles(float_id, profile_date);
CREATE INDEX idx_floats_location ON argo_floats(latitude, longitude);
```

### Python Optimization
```bash
# Use production WSGI server
pip install gunicorn gevent

# Run with optimized settings
gunicorn -w 4 --worker-class gevent --worker-connections 1000 app:app
```

### Frontend Optimization
- Enable gzip compression in Nginx
- Minify CSS and JavaScript files
- Use browser caching headers

## Backup and Maintenance

### Database Backup
```bash
# MySQL backup
mysqldump -u floatchat_user -p floatchat > backup_$(date +%Y%m%d).sql

# MongoDB backup
mongodump --db floatchat --out backup_$(date +%Y%m%d)
```

### Update Process
```bash
# Pull latest changes
git pull origin main

# Update Python packages
pip install -r requirements.txt --upgrade

# Apply database migrations
python migrate.py

# Restart services
sudo systemctl restart floatchat
```

## Security Checklist

- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable firewall (UFW/iptables)
- [ ] Set up SSL/TLS certificates
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Regular security updates

For additional help, consult the [troubleshooting guide](TROUBLESHOOTING.md) or create an issue on GitHub.
