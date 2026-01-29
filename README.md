# InfraUtomater

A full-stack infrastructure automation platform that enables teams to request and provision AWS resources through an approval-based workflow system.

## Features

- **User Authentication & Authorization**: JWT-based authentication with role-based access control (Admin/User)
- **Team Management**: Organize users into teams with team-specific resource access
- **Resource Request System**: Submit infrastructure requests that require admin approval
- **AWS Credentials Management**: Secure storage of team-specific AWS credentials with encryption
- **Terraform Integration**: Automated infrastructure provisioning via Celery task queue
- **Admin Dashboard**: Comprehensive admin panel for managing teams, users, and approving requests
- **User Dashboard**: Request tracking and team resource visibility

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Default database (can be switched to PostgreSQL)
- **Celery**: Distributed task queue for async operations
- **Redis**: Message broker for Celery
- **Boto3**: AWS SDK for Python
- **Cryptography**: Secure credential encryption

### Frontend
- **React**: UI library
- **React Router**: Client-side routing
- **Axios**: HTTP client
- **Context API**: State management

## Project Structure

```
infrautomater/
├── admin_routes/          # Admin-only API endpoints
│   ├── aws_credentials.py # AWS credential management
│   ├── requests.py        # Request approval system
│   └── teamanagement.py   # Team & user management
├── user_routes/           # User API endpoints
│   ├── users.py           # Authentication & user profile
│   └── requests.py        # User request submission
├── celery_app/            # Background task processing
│   └── tasks/
│       └── terraform_tasks.py  # Infrastructure provisioning
├── auth/                  # Authentication logic
│   └── auth.py            # JWT & password hashing
├── utils/                 # Utility functions
│   └── encryption.py      # Credential encryption
├── frontend/              # React frontend
│   └── src/
│       ├── components/    # Reusable components
│       ├── pages/         # Page components
│       ├── context/       # React Context
│       └── services/      # API service layer
├── models.py              # Database models
├── schemas.py             # Pydantic schemas
├── database.py            # Database configuration
├── main.py                # FastAPI application entry
├── create_test_user.py    # User management utility
└── check_system.py        # System health check utility
```

## Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- Redis (for Celery)
- Terraform (for infrastructure provisioning)

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd infrautomater
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

5. **Generate secret keys**:
   ```bash
   # Generate JWT secret
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

   # Generate encryption key
   python -c "from cryptography.fernet import Fernet; print('CREDENTIALS_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
   ```

   Add these to your `.env` file.

6. **Initialize the database**:
   ```bash
   # Database tables are created automatically on first run
   python main.py
   ```

7. **Create test users** (optional):
   ```bash
   python create_test_user.py
   ```
   This creates:
   - Admin user: `admin` / `admin123`
   - Test user: `testuser` / `test123`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm start
   ```
   Frontend will run on `http://localhost:3000`

### Running the Application

#### Option 1: Manual Start (Development)

**Terminal 1 - Backend**:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm start
```

**Terminal 3 - Celery Worker** (optional, for async tasks):
```bash
source venv/bin/activate
celery -A celery_app.celery_worker worker --loglevel=info
```

**Terminal 4 - Redis** (required for Celery):
```bash
redis-server
```

#### Option 2: Check System Health

Before starting, verify everything is configured:
```bash
python check_system.py
```

This checks:
- Environment variables
- Database connectivity
- User accounts
- Port availability

## Usage

### First-Time Setup

1. **Access the application**: Navigate to `http://localhost:3000`

2. **Login with admin credentials**:
   - Username: `admin`
   - Password: `admin123`

3. **Configure AWS Credentials** (Admin only):
   - Go to Admin Dashboard → AWS Credentials
   - Add team-specific or global AWS credentials
   - Credentials are encrypted before storage

4. **Create Teams** (Admin only):
   - Go to Admin Dashboard → Teams
   - Create teams and assign users

### Submitting Infrastructure Requests (Users)

1. Login with user credentials
2. Navigate to Dashboard → New Request
3. Fill in the resource request form
4. Submit for admin approval
5. Track request status in your dashboard

### Approving Requests (Admins)

1. Login with admin credentials
2. Navigate to Admin Dashboard → Requests
3. Review pending requests
4. Approve or reject with comments
5. Approved requests trigger Terraform provisioning

## API Documentation

Once the backend is running, access interactive API docs at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user profile

#### User Routes
- `GET /api/v1/user/requests` - List user's requests
- `POST /api/v1/user/requests` - Create new request
- `GET /api/v1/auth/me/team` - Get user's team info

#### Admin Routes
- `GET /api/v1/admin/teams` - List all teams
- `POST /api/v1/admin/teams` - Create team
- `GET /api/v1/admin/requests` - List all requests
- `PUT /api/v1/admin/requests/{id}` - Approve/reject request
- `POST /api/v1/admin/aws-credentials` - Configure AWS credentials

## Monitoring & Logging

Application logs are written to:
- **app.log**: Main application logs (includes login attempts, errors)
- **backend.log**: Uvicorn server logs
- **celery.log**: Task queue logs

View live logs:
```bash
tail -f app.log
```

## Security Features

- **Password Hashing**: Bcrypt with salt
- **JWT Authentication**: Secure token-based auth with expiration
- **Credential Encryption**: AWS credentials encrypted with Fernet (AES-128)
- **CORS Protection**: Configured for localhost development
- **Role-Based Access**: Admin-only routes protected
- **SQL Injection Protection**: SQLAlchemy ORM parameterized queries

## Development Tools

### Create Test Users
```bash
python create_test_user.py
```

### Check System Health
```bash
python check_system.py
```

### Monitor Application Logs
```bash
tail -f app.log
```

### Database Inspection
```bash
sqlite3 infra.db
.tables
SELECT * FROM users;
```

## Troubleshooting

### Backend won't start

**Error**: `JWT_SECRET_KEY environment variable must be set`
- **Solution**: Make sure `.env` file exists and contains `JWT_SECRET_KEY`

**Error**: `CREDENTIALS_ENCRYPTION_KEY environment variable must be set`
- **Solution**: Generate encryption key and add to `.env`

### Login fails

**Error**: `401 Unauthorized`
- **Solution**: Run `python create_test_user.py` to reset passwords
- Check `app.log` for login attempt details

### CORS errors in browser

**Error**: `Access-Control-Allow-Origin`
- **Solution**: Ensure frontend is running on `http://localhost:3000`
- Check CORS configuration in `main.py`

### Port already in use

**Error**: `Address already in use`
- **Solution**:
  ```bash
  # Kill process on port 8000
  lsof -ti :8000 | xargs kill -9

  # Kill process on port 3000
  lsof -ti :3000 | xargs kill -9
  ```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

## License

[MIT License](LICENSE) - feel free to use this project for your own purposes.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Note**: This is a development setup. For production deployment:
- Use PostgreSQL instead of SQLite
- Set up proper SSL/TLS certificates
- Use environment-specific configuration
- Set up proper logging and monitoring
- Use a production-grade WSGI server (e.g., Gunicorn)
- Implement rate limiting and additional security measures
