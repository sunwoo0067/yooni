# Architecture

## Frontend (Next.js 15 + TypeScript)
- **Framework**: Next.js 15 with App Router, React 19
- **State Management**: Zustand for global state
- **Data Fetching**: TanStack Query v5 for server state
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **Testing**: Jest with React Testing Library
- **Database**: Direct PostgreSQL connection via pg library

## Backend (Python 3.11)
- **AI/ML API**: FastAPI with uvicorn (main.py, port 8000/8003)
- **Structure**: Module-based without standard Python packaging
- **Database**: PostgreSQL on port 5434 (non-standard)
- **Cache**: Redis for session and model caching
- **ML Platform**: MLflow for experiment tracking and model registry

## AI/ML Stack
- **Time Series**: Prophet, LSTM (PyTorch), ARIMA/SARIMA
- **Machine Learning**: XGBoost, scikit-learn, LightGBM
- **Deep Learning**: PyTorch, Transformers, Sentence Transformers
- **NLP**: KoNLPy for Korean text, custom chatbot with intent classification
- **Optimization**: PuLP, CVXPY, DQN for reinforcement learning
- **MLOps**: MLflow, Optuna for hyperparameter tuning