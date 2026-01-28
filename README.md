![UQMARKS logo image](./static/images/share_small.png)

A grade calculator specifically designed for UQ.  
Currently hosted at https://www.uqmarks.com/

## Features

- **Weekly Quiz Calculator** - Calculate your grade when only the best _X_ quizzes count
- **Grade Calculator** - Calculate required marks to achieve a certain grade in any course

## Tech Stack

- **Backend:** Flask (Python 3.10+), PostgreSQL, SQLAlchemy
- **Frontend:** Vue 3, Vuetify, TypeScript, Vite
- **Analytics:** Dash (Python)
- **Deployment:** Docker, Gunicorn

Inspired by [uqfinal](https://uqfinal.com/).

## Installation

### Prerequisites

- Python 3.10+
- Node.js
- PostgreSQL (or use Docker)

### Environment Setup

1. (Optional) Create Discord channels for logging (one for errors, one for general logs)
2. Create a `.env` file in the root directory:

```env
# Flask
SECRET_KEY=your_secret_key
DEBUG_MODE=T/F
ENABLE_LOGGING=T/F

# PostgreSQL
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=your_db_name
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Discord Logging (optional)
LOG_LINK=discord_webhook_url
ERROR_LOG_LINK=discord_webhook_url
MANAGER_ID=discord_user_id
```

## Running the App

### Option 1: Docker (Recommended)

```bash
docker compose up
```

### Option 2: Manual Start

This allows you to run the app in debug mode, with hot reload.

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install frontend dependencies:

   ```bash
   cd react-app
   npm install
   ```

3. Start the Flask backend:

   ```bash
   python app.py
   ```

4. In a new terminal, start the frontend dev server:
   ```bash
   cd react-app
   npm run dev
   ``
   ```

## License

MIT
