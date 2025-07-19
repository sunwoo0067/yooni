# Project Structure

```
yoonni/
├── frontend/               # Next.js application
├── backend/
│   ├── ai/                # AI/ML modules
│   │   ├── advanced/      # Advanced AI implementations
│   │   └── models/        # Model definitions
│   ├── market/            # Marketplace integrations
│   ├── supplier/          # Supplier APIs
│   ├── main.py           # Unified AI API server
│   ├── simple_api.py     # Minimal API for testing
│   ├── scheduler.py      # Scheduled tasks
│   └── requirements.txt   # Python dependencies
├── scripts/              # Deployment and operations
├── docker-compose.yml    # Development setup
├── docker-compose.dev.yml # AI services development
└── docker-compose.prod.yml # Production deployment
```