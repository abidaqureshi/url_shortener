# 🔗 URL Shortener

A high-performance, feature-rich URL shortener built with FastAPI, SQLAlchemy, and Redis. This project demonstrates modern Python async programming with proper architecture patterns.

## 🚀 Features

- **🔗 URL Shortening**: Create short URLs with custom aliases
- **📊 Analytics**: Track clicks with comprehensive analytics
- **⚡ Performance**: Redis caching for fast redirects
- **🛡️ Rate Limiting**: Protect against abuse with Redis-based rate limiting
- **⏰ Expiration**: Set expiration dates for URLs
- **🎯 Async Architecture**: Built with async/await for high concurrency
- **📈 Monitoring**: Health checks and performance metrics

## 🛠 Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: SQLAlchemy 2.0+ with async support (SQLite/PostgreSQL)
- **Cache**: Redis with async client
- **API Documentation**: Auto-generated Swagger/OpenAPI
- **Architecture**: MVC pattern with Services, Controllers, and Models

## 📁 Project Structure

```
URLShortner/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database configuration & async session management
│   ├── redis_cache.py          # Redis cache client and operations
│   ├── schemas/                # Pydantic models for request/response
│   │   ├── url_schemas.py      # URL creation/response schemas
│   │   └── analytics_schemas.py # Analytics data schemas
│   ├── models/                 # SQLAlchemy ORM models
│   │   └── url_models.py       # URL and Click models
│   ├── services/               # Business logic layer
│   │   ├── url_service.py      # URL shortening and management
│   │   ├── analytics_service.py # Analytics and reporting
│   │   ├── cache_service.py    # Redis cache operations
│   │   └── rate_limiter.py     # Rate limiting implementation
│   ├── controllers/            # API route handlers
│   │   ├── url_controller.py   # URL management endpoints
│   │   └── analytics_controller.py # Analytics endpoints
│   └── utils/                  # Utility functions
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Redis server
- SQLite (default) or PostgreSQL

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd URLShortner
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit example.env with your configuration
   ```

5. **Start Redis**
   ```bash
   # On macOS (with Homebrew)
   brew services start redis
   
   # On Ubuntu/Debian
   sudo systemctl start redis-server
   
   # On Windows, download and run Redis
   ```

6. **Run the application**
   ```bash
   python app/main.py
   # Or with uvicorn directly:
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./url_shortener.db
# For PostgreSQL: postgresql+asyncpg://user:password@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Application
SECRET_KEY=your-secret-key-here
DEBUG=True
```

## 📚 API Documentation

### Create Short URL
```http
POST /urls
Content-Type: application/json

{
  "original_url": "https://example.com/very/long/url/path",
  "custom_alias": "myalias",  # optional
  "expiration_days": 30       # optional, default 30
}
```

### Redirect to Original URL
```http
GET /r/{short_code}
# Or
GET /urls/{short_code}
```

### Get URL Analytics
```http
GET /urls/{short_code}/analytics
```

### Update URL
```http
PUT /urls/{short_code}
Content-Type: application/json

{
  "custom_alias": "newalias",
  "expiration_days": 60
}
```

### Delete URL
```http
DELETE /urls/{short_code}
```

### Get All Analytics
```http
GET /analytics
```

## 🗄️ Database Models

### URL Model
```python
class URL(Base):
    id: int (Primary Key)
    short_code: str (Unique, Indexed)
    original_url: str
    custom_alias: str (Optional, Unique)
    created_at: DateTime
    expires_at: DateTime (Optional)
    is_active: bool
    clicks: int
```

### Click Model
```python
class Click(Base):
    id: int (Primary Key)
    url_id: int (Foreign Key)
    timestamp: DateTime
    ip_address: str
    user_agent: str (Optional)
    country: str (Optional)
    referrer: str (Optional)
```

## 🔧 Development

### Running Tests
```bash
# Add pytest to requirements and run:
pytest tests/
```

### Code Formatting
```bash
black app/
isort app/
```

### Database Migrations
```bash
# Using Alembic (Not configured yet)
alembic upgrade head
```

## 🏗️ Architecture Patterns

### Dependency Injection
```python
# Services are injected into controllers
async def create_short_url(
    url_data: URLCreate,
    db: AsyncSession = Depends(dependency_db),
    url_service: URLService = Depends(get_url_service)
):
    return await url_service.create_short_url(db, url_data)
```

### Context Managers
```python
# Database sessions managed with context managers
@asynccontextmanager
async def get_db():
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

### Service Layer
- **URLService**: Handles URL creation, retrieval, updates, deletion
- **AnalyticsService**: Manages click tracking and reporting
- **CacheService**: Redis operations for caching
- **RateLimiter**: Request rate limiting

## 📊 Performance Features

### Redis Caching
- URL data cached with TTL
- Click counts cached for fast increments
- Rate limiting using Redis sorted sets

### Async Operations
- All database operations are async
- Redis operations are async
- Non-blocking I/O for high concurrency

### Rate Limiting
- Redis-based rate limiting
- Configurable requests per hour
- Protects against API abuse

## 🚀 Deployment

### Using Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations
- Use PostgreSQL instead of SQLite
- Configure Redis persistence
- Set up proper logging and monitoring
- Use environment variables for secrets
- Configure CORS for web frontend
- Set up reverse proxy (Nginx)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Redis Connection Error**
   - Ensure Redis server is running
   - Check Redis URL in environment variables

2. **Database Connection Error**
   - Verify database URL format
   - Check database permissions

3. **Import Errors**
   - Ensure virtual environment is activated
   - Run `pip3 install -r requirements.txt`

4. **Async Context Manager Errors**
   - Make sure all context managers are properly async
   - Check SQLAlchemy version compatibility

### Getting Help

- Check the API documentation at `/docs`
- Review the application logs
- Verify all services are running (Redis, Database)

---

**Built with ❤️ using FastAPI and modern Python patterns**