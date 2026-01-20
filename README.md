# 🚀 WhatsApp Clone - Complete Setup Guide

## Step-by-Step Installation

### 1️⃣ Prerequisites Installation

#### Install Python 3.9+
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# macOS
brew install python@3.11

# Verify
python3 --version
```

#### Install Redis
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# macOS
brew install redis
brew services start redis

# Verify
redis-cli ping  # Should return PONG
```

#### Install PostgreSQL (Optional, recommended for production)
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS
brew install postgresql
brew services start postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE whatsapp_db;
CREATE USER whatsapp_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE whatsapp_db TO whatsapp_user;
\q
```

---

### 2️⃣ Project Setup

#### Clone/Create Project Directory
```bash
# Create project directory
mkdir whatsapp_project
cd whatsapp_project

# Initialize git (optional)
git init
```

#### Create Virtual Environment
```bash
# Create venv
python3 -m venv venv

# Activate venv
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Your prompt should now show (venv)
```

#### Install Dependencies
```bash
# Create requirements.txt with this content:
cat > requirements.txt << EOF
Django==4.2.7
channels==4.0.0
channels-redis==4.1.0
Pillow==10.1.0
qrcode==7.4.2
redis==5.0.1
daphne==4.0.0
anthropic==0.18.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
gunicorn==21.2.0
whitenoise==6.6.0
django-cors-headers==4.3.1
EOF

# Install all dependencies
pip install -r requirements.txt
```

---

### 3️⃣ Create Django Project

```bash
# Create Django project
django-admin startproject whatsapp_project .

# Create whatsapp app
python manage.py startapp whatsapp
```

---

### 4️⃣ Setup Environment Variables

```bash
# Create .env file
cat > .env << EOF
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (choose one)
# SQLite (default):
DATABASE_URL=sqlite:///db.sqlite3

# PostgreSQL (recommended for production):
# DATABASE_URL=postgresql://whatsapp_user:your_password@localhost:5432/whatsapp_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Anthropic AI - Get your key from https://console.anthropic.com/
ANTHROPIC_API_KEY=your-api-key-here

# Media/Static
MEDIA_URL=/media/
STATIC_URL=/static/
EOF
```

---

### 5️⃣ Copy All Project Files

Now copy all the files from the artifacts into their respective locations:

```bash
# Create directory structure
mkdir -p whatsapp/templates/partials
mkdir -p whatsapp/static/{css,js,images/wallpapers}
mkdir -p whatsapp/management/commands
mkdir -p whatsapp/tests
mkdir -p media/{profiles,group_icons,media,status,wallpapers,chat_wallpapers,channel_icons,community_icons,channel_posts,ai_avatars,ai_audio}
mkdir -p logs
mkdir -p staticfiles
```

**Copy files from the artifacts:**
1. `models.py` → `whatsapp/models.py`
2. `views.py` → `whatsapp/views.py`
3. `consumers.py` → `whatsapp/consumers.py`
4. `routing.py` → `whatsapp/routing.py`
5. `urls.py` → `whatsapp/urls.py`
6. `ai_service.py` → `whatsapp/ai_service.py`
7. `admin.py` → `whatsapp/admin.py`
8. `forms.py` → `whatsapp/forms.py`
9. `signals.py` → `whatsapp/signals.py`
10. `utils.py` → `whatsapp/utils.py`
11. `apps.py` → `whatsapp/apps.py`
12. HTML templates → `whatsapp/templates/`
13. Settings, URLs, ASGI files → `whatsapp_project/`
14. Test files → `whatsapp/tests/`

---

### 6️⃣ Database Setup

```bash
# Make sure Redis is running
redis-cli ping  # Should return PONG

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
# Enter username, phone number (+254XXXXXXXXX), and password

# Create AI assistant
python manage.py create_ai_assistant
```

---

### 7️⃣ Collect Static Files

```bash
# For development
python manage.py collectstatic --noinput
```

---

### 8️⃣ Run the Application

You need **3 terminal windows**:

#### Terminal 1: Redis Server
```bash
redis-server

# You should see:
# Ready to accept connections
```

#### Terminal 2: Django HTTP Server
```bash
# Activate venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run server
python manage.py runserver

# You should see:
# Starting development server at http://127.0.0.1:8000/
```

#### Terminal 3: Daphne WebSocket Server
```bash
# Activate venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run Daphne
daphne -b 0.0.0.0 -p 8001 whatsapp_project.asgi:application

# You should see:
# Listening on TCP address 0.0.0.0:8001
```

---

### 9️⃣ Access the Application

Open your browser and visit:
- **Main App**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/

Login with the superuser credentials you created!

---

## 🐳 Alternative: Docker Setup

If you prefer Docker:

```bash
# Build and run with Docker Compose
docker-compose up --build

# The app will be available at:
# http://localhost:80
```

---

## ✅ Verify Installation

### Check if everything is working:

```bash
# Test Redis connection
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'working')
>>> cache.get('test')
'working'
>>> exit()

# Test WebSocket connection
# Open browser console on http://localhost:8000/chat/
# You should see: "WebSocket connected"

# Test AI integration (if you have API key)
python manage.py shell
>>> from whatsapp.ai_service import ClaudeAIService
>>> ai = ClaudeAIService()
>>> response = ai.generate_text_response("Hello")
>>> print(response)
```

---

## 🎯 Quick Test Workflow

1. **Register a new account:**
   - Go to http://localhost:8000/register/
   - Phone: +254712345678
   - Username: TestUser
   - Password: test123456

2. **Login:**
   - Go to http://localhost:8000/
   - Enter credentials

3. **Create a test user (in another browser/incognito):**
   - Phone: +254787654321
   - Username: TestUser2

4. **Start chatting:**
   - From first account, click "New Chat"
   - Enter: +254787654321
   - Send messages!

5. **Test features:**
   - ✅ Send messages
   - ✅ See typing indicator
   - ✅ Check read receipts
   - ✅ Create a group
   - ✅ Post a status
   - ✅ Chat with AI assistant

---

## 🔧 Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping

# If not running:
redis-server

# Or restart:
sudo systemctl restart redis
```

### WebSocket Not Connecting
```bash
# Make sure Daphne is running on port 8001
lsof -i :8001  # Linux/macOS
netstat -ano | findstr :8001  # Windows

# Restart Daphne
daphne -b 0.0.0.0 -p 8001 whatsapp_project.asgi:application
```

### Database Errors
```bash
# Delete db and recreate
rm db.sqlite3
rm -rf whatsapp/migrations/
python manage.py makemigrations whatsapp
python manage.py migrate
python manage.py createsuperuser
```

### Port Already in Use
```bash
# Kill process on port 8000
# Linux/macOS:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Static Files Not Loading
```bash
# Recollect static files
python manage.py collectstatic --clear --noinput
```

---

## 📊 Performance Tips

### For Development:
```bash
# Use SQLite (already default)
# Enable Django Debug Toolbar:
pip install django-debug-toolbar
```

### For Production:
```bash
# Use PostgreSQL
# Set DEBUG=False in .env
# Use Gunicorn instead of runserver
# Enable caching
# Use CDN for media files
```

---

## 🔒 Security Checklist (Production)

- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Set proper `ALLOWED_HOSTS`
- [ ] Use environment variables for secrets
- [ ] Enable CSRF protection
- [ ] Set secure cookie flags
- [ ] Use PostgreSQL instead of SQLite
- [ ] Regular backups
- [ ] Rate limiting
- [ ] Monitor logs

---

## 📱 Mobile Testing

To test on mobile devices on same network:

```bash
# Find your local IP
# Linux/macOS:
ifconfig | grep "inet "
# Windows:
ipconfig

# Run server with your IP
python manage.py runserver 0.0.0.0:8000

# Access from mobile:
http://YOUR_LOCAL_IP:8000
```

---

## 🎓 Next Steps

1. **Customize branding** - Change colors, logos
2. **Add more features** - Voice messages, file sharing
3. **Deploy to production** - Heroku, AWS, DigitalOcean
4. **Add analytics** - Google Analytics, Mixpanel
5. **Mobile apps** - React Native, Flutter
6. **Monetization** - Premium features, ads

---

## 📚 Additional Resources

- **Django Docs**: https://docs.djangoproject.com/
- **Channels Docs**: https://channels.readthedocs.io/
- **Anthropic API**: https://docs.anthropic.com/
- **Redis Docs**: https://redis.io/docs/

---

## 🆘 Getting Help

If you encounter issues:

1. Check the logs: `tail -f logs/django.log`
2. Enable Django debug mode temporarily
3. Search error messages on Stack Overflow
4. Check Django/Channels documentation
5. Verify all services are running (Redis, Django, Daphne)

---

## 🎉 You're Done!

Your WhatsApp clone is now running! Start chatting, testing features, and customizing to your needs.

**Happy coding! 🚀**