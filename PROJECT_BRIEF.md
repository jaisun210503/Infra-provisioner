# Self-Service Infrastructure API - Development Brief

## Project Overview
Building a Self-Service Infrastructure API where:
- Admin creates teams and manages users
- Users request infrastructure resources (DB, S3, K8s namespaces, etc.)
- Admin reviews and approves/rejects requests
- Approved requests trigger Terraform to provision resources
- Credentials are securely sent back to users

## Current Phase: Phase 1 - Core API (Days 1-3)

### Phase 1 Goals
- [x] Project setup and structure
- [ ] Database models (User, Team)
- [ ] JWT authentication system
- [ ] User registration and login
- [ ] Admin team management endpoints
- [ ] Role-based access control

### Tech Stack
- **Backend**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **Migrations**: Alembic
- **Auth**: JWT (python-jose)
- **Password**: bcrypt/passlib
- **Validation**: Pydantic v2
- **Container**: Docker + Docker Compose
- **Task Queue** (Phase 3): Celery + Redis
- **IaC** (Phase 3): Terraform

## Database Schema (Phase 1)

### User
- id: UUID (primary key)
- email: String (unique, indexed)
- password_hash: String
- is_admin: Boolean (default: False)
- team_id: UUID (foreign key, nullable)
- created_at: DateTime
- updated_at: DateTime

### Team
- id: UUID (primary key)
- name: String (unique)
- description: Text (nullable)
- created_by: UUID (foreign key to User)
- created_at: DateTime
- updated_at: DateTime

## API Endpoints (Phase 1)

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info (protected)

### Teams (Admin Only)
- `POST /api/v1/teams` - Create team
- `GET /api/v1/teams` - List all teams
- `GET /api/v1/teams/{id}` - Get team details
- `PUT /api/v1/teams/{id}` - Update team
- `DELETE /api/v1/teams/{id}` - Delete team
- `POST /api/v1/teams/{id}/members` - Add user to team
- `DELETE /api/v1/teams/{id}/members/{user_id}` - Remove user from team

### Users
- `GET /api/v1/users/me/team` - Get my team info
- `GET /api/v1/users/me/team/members` - Get my team members

## Project Structure
```
infrastructure-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py         # Auth endpoints
│   │       ├── teams.py        # Team endpoints
│   │       └── users.py        # User endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings & environment variables
│   │   ├── security.py         # JWT & password utilities
│   │   └── dependencies.py     # Common dependencies (get_db, get_current_user)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User SQLAlchemy model
│   │   └── team.py             # Team SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── team.py             # Team Pydantic schemas
│   │   └── token.py            # Token schemas
│   └── db/
│       ├── __init__.py
│       └── session.py          # Database session management
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/                      # Unit tests (Phase 2)
├── .env                        # Environment variables (not in git)
├── .env.example                # Example env file
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── PROJECT_BRIEF.md           # This file
```

## Development Environment
- **OS**: MAC
- **Python Version**:  3.9+
- **Docker**: Yes
- **Editor**: VS Code

## Development Approach: INTERACTIVE CODING

### Your Role (Developer - Me)
- Write all code
- Ask questions when unclear
- Share code for review
- Implement feedback
- Test locally

### Claude's Role (Code Reviewer & Guide)
- Break tasks into small steps
- Guide what to build and why
- Review code and provide feedback
- Suggest improvements
- Help debug issues
- Answer questions about best practices
- **DO NOT write complete code files**
- **DO provide guidance, explanations, and code reviews**

## Success Criteria for Phase 1
- [ ] Docker Compose runs PostgreSQL successfully
- [ ] FastAPI app connects to database
- [ ] User can register via API
- [ ] User can login and receive JWT token
- [ ] Admin can create teams
- [ ] Admin can add users to teams
- [ ] Protected endpoints require valid JWT
- [ ] Role-based access control works (admin vs user)
- [ ] API documentation visible at `/docs`

## Future Phases (Not Now)

### Phase 2: Resource Request System
- ResourceRequest model
- User can submit resource requests
- Admin can view pending requests
- Admin can approve/reject requests

### Phase 3: Terraform Integration
- Celery for async tasks
- Terraform modules for each resource type
- Credential encryption and storage
- Provisioning workflow

### Phase 4: Additional Features
- Resource deletion
- Audit logs
- Cost tracking
- Email notifications

## Current Status
**Starting Phase 1** - Setting up project structure

## Notes & Questions
[Add notes here as you develop]

---

**Last Updated**: [DATE]
**Current Step**: Project initialization
```

## Step 3: Use it with Claude

Now in VS Code, you can simply say to Claude:
```
Read PROJECT_BRIEF.md and guide me through Phase 1 step by step. 
Start by telling me what to create first.