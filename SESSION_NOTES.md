# Infrastructure API - Session Notes

## Project Overview
Built a Self-Service Infrastructure API where:
- **Users** can request infrastructure resources (databases, S3 buckets, K8s namespaces)
- **Admins** manage teams, users, and approve/reject resource requests
- **Celery** handles async provisioning after approval

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI       │────▶│     Redis       │────▶│  Celery Worker  │
│   (API Server)  │     │  (Message Queue)│     │  (Task Runner)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│    SQLite DB    │◀──────────────────────────│  Terraform      │
│  (infra.db)     │                           │  (Provisioning) │
└─────────────────┘                           └─────────────────┘
```

---

## Files Created/Modified

### Core Files
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app entry point, includes all routers |
| `database.py` | SQLAlchemy engine and session configuration |
| `models.py` | User, Team, ResourceRequest models |
| `schemas.py` | Pydantic schemas for request/response validation |

### Auth
| File | Purpose |
|------|---------|
| `auth/auth.py` | JWT authentication, password hashing, dependencies |

### Admin Routes
| File | Purpose |
|------|---------|
| `admin_routes/teamanagement.py` | Team CRUD operations |
| `admin_routes/requests.py` | View/Approve/Reject resource requests |

### User Routes
| File | Purpose |
|------|---------|
| `user_routes/users.py` | Register, Login, Profile endpoints |
| `user_routes/requests.py` | Submit and view resource requests |

### Celery (Async Tasks)
| File | Purpose |
|------|---------|
| `celery_app/__init__.py` | Celery app instance with Redis config |
| `celery_app/celery_config.py` | Additional Celery configuration |
| `celery_app/tasks/terraform_tasks.py` | `provision_resource` task |

---

## Problems Faced & Solutions

### 1. Typos in Code
**Problem:** `bycrpt` instead of `bcrypt`, `deprecrated` instead of `deprecated`
```python
# Wrong
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bycrpt"], deprecrated="auto")

# Correct
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```
**Lesson:** Always double-check library names and parameter spellings.

---

### 2. Missing TokenData Class
**Problem:** `get_current_user` function referenced `TokenData` class that didn't exist.

**Solution:** Added Pydantic model:
```python
class TokenData(BaseModel):
    username: Optional[str] = None
```

---

### 3. Pydantic/FastAPI Version Incompatibility
**Problem:** Newer versions of Pydantic (2.10+) had breaking changes with FastAPI.

**Solution:** Downgraded to compatible versions:
```bash
pip install "pydantic<2.10" "fastapi<0.115"
```
**Lesson:** Check version compatibility when using multiple libraries together.

---

### 4. bcrypt Version Issue
**Problem:** bcrypt 4.1+ had issues with passlib.

**Solution:**
```bash
pip install "bcrypt>=4.0.0,<4.1.0"
```

---

### 5. Missing email-validator
**Problem:** Pydantic's `EmailStr` type requires email-validator package.

**Solution:**
```bash
pip install email-validator
```

---

### 6. User Route Syntax Errors
**Problem:** Multiple issues in `user_routes/requests.py`:

```python
# Problem 1: Broken filter query (missing comma between conditions)
requests = db.query(ResourceRequest).filter(ResourceRequest.user_id == user.id
    ResourceRequest.user_id == user.id ).all()  # SyntaxError!

# Problem 2: Missing path parameter in function
@request_router.get("/requests/{id}")
def view_my_request(db: Session = Depends(get_db)):  # Missing 'id' parameter!

# Problem 3: Wrong response_model (single vs list)
@request_router.get("/requests", response_model=ResourceRequestResponse)  # Should be List[...]
def view_my_requests(...):
    return db.query(...).all()  # Returns a list!
```

**Solution:**
```python
# Fixed version
@request_router.get("/requests/{request_id}", response_model=ResourceRequestResponse)
def get_my_request(request_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    request = db.query(ResourceRequest).filter(
        ResourceRequest.id == request_id,
        ResourceRequest.user_id == user.id  # Comma separates filter conditions
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request

@request_router.get("/requests", response_model=List[ResourceRequestResponse])  # List!
def view_my_requests(db: Session = Depends(get_db), user = Depends(get_current_user)):
    return db.query(ResourceRequest).filter(ResourceRequest.user_id == user.id).all()
```

**Lessons:**
- SQLAlchemy filter conditions are separated by commas
- Path parameters must be in function signature
- Match response_model with what you actually return

---

### 7. Celery Module Import Error
**Problem:** Celery worker couldn't find `database` module.
```
ModuleNotFoundError: No module named 'database'
```

**Solution:** Added parent directory to sys.path in `terraform_tasks.py`:
```python
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SessionLocal
from models import ResourceRequest
```

**Lesson:** Celery workers run in a different context than your main app. Module paths need to be explicit.

---

### 8. Celery Redis Connection Refused (Big Issue!)
**Problem:** FastAPI could approve requests but failed when sending to Celery:
```
kombu.exceptions.OperationalError: [Errno 61] Connection refused
```

**Root Cause:** `@shared_task` decorator wasn't properly binding to our configured Celery app when imported by FastAPI.

**Failed Attempt 1:** Updated `celery_app/__init__.py` with explicit broker URL:
```python
celery_app = Celery(
    "infrautomater",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)
```
Still didn't work because `@shared_task` creates tasks that can be associated with any Celery app.

**Solution:** Changed from `@shared_task` to `@celery_app.task`:
```python
# Before (problematic)
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def provision_resource(self, request_id: int):
    ...

# After (working)
from celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def provision_resource(self, request_id: int):
    ...
```

**Lesson:**
- `@shared_task` is for tasks that can work with any Celery app
- `@celery_app.task` binds the task to your specific configured app
- When importing tasks into another application (like FastAPI), use `@app.task`

---

### 9. Server Cache Issue
**Problem:** After fixing code, FastAPI still used old cached modules.

**Solution:** Restart the server completely (kill and restart uvicorn).

**Lesson:** Even with `--reload`, sometimes you need a full restart for import changes.

---

## API Endpoints Summary

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login, get JWT token |
| GET | `/api/v1/auth/me` | Get current user profile |
| GET | `/api/v1/auth/me/team` | Get user's team info |
| GET | `/api/v1/auth/me/team/members` | Get team members |

### Admin - Teams
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/admin/teams` | Create team |
| GET | `/api/v1/admin/teams` | List all teams |
| GET | `/api/v1/admin/teams/{id}` | Get team details |
| PUT | `/api/v1/admin/teams/{id}` | Update team |
| DELETE | `/api/v1/admin/teams/{id}` | Delete team |
| POST | `/api/v1/admin/teams/{id}/members` | Add member to team |
| DELETE | `/api/v1/admin/teams/{id}/members/{user_id}` | Remove member |

### Admin - Requests
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/requests` | View all requests (with status filter) |
| GET | `/api/v1/admin/requests/{id}` | Get request details |
| PUT | `/api/v1/admin/requests/{id}/approve` | Approve request |
| PUT | `/api/v1/admin/requests/{id}/reject` | Reject request |

### User - Requests
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/requests/submit` | Submit new request |
| GET | `/api/v1/users/requests` | View my requests |
| GET | `/api/v1/users/requests/{id}` | Get specific request |

---

## Request Status Flow

```
pending ──▶ approved ──▶ provisioning ──▶ provisioned
    │                         │
    ▼                         ▼
 rejected                   failed
```

---

## How to Run

### Terminal 1: Start Redis
```bash
brew services start redis
# or
redis-server
```

### Terminal 2: Start FastAPI
```bash
cd /Users/kavikondalajayasurya/infrautomater
source venv/bin/activate
uvicorn main:app --reload
```

### Terminal 3: Start Celery Worker
```bash
cd /Users/kavikondalajayasurya/infrautomater
source venv/bin/activate
celery -A celery_app worker --loglevel=info
```

### Access
- API: http://127.0.0.1:8000
- Swagger Docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Test Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| User | john | john123 |

---

## Key Learnings

1. **Always read files before editing** - Understand the existing code structure
2. **Check import paths** - Different execution contexts (FastAPI vs Celery) may need different import strategies
3. **Version compatibility matters** - Pin versions in requirements.txt
4. **Restart services after changes** - Especially for import-level changes
5. **Use proper decorators** - `@shared_task` vs `@app.task` have different behaviors
6. **SQLAlchemy filter syntax** - Use commas to separate conditions, not `and`
7. **Match response_model to return type** - Single object vs List
8. **Path parameters must be in function signature** - FastAPI uses them for routing

---

## Next Steps (Future Work)

1. **Actual Terraform Integration**
   - Create Terraform modules in `terraform/` directory
   - Update `_provision_*` functions to run actual Terraform commands

2. **Add More Resource Types**
   - EC2 instances
   - RDS databases
   - VPCs

3. **Add Status Webhooks**
   - Notify users when requests are approved/rejected/provisioned

4. **Add Request History/Audit Log**
   - Track who approved what and when

5. **Switch to PostgreSQL**
   - For production, replace SQLite with PostgreSQL

6. **Add Tests**
   - Unit tests for endpoints
   - Integration tests for Celery tasks

---

*Session Date: 2026-01-26*
