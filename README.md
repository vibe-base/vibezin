# Vibezin

A savage digital carnival of code and chaos. Myspace on acid, wired to the soul. Build your altar. Broadcast your vibe. God help us all.

## Setup Instructions

### Prerequisites
- Python 3.x
- pip (Python package manager)
- PostgreSQL (optional, can use SQLite for development)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd vibezin
   ```

2. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add the following variables:
     ```
     DB_NAME=vibezin_db
     DB_USER=vibezin_user
     DB_PASSWORD=your_secure_password
     DB_HOST=localhost
     DB_PORT=5432
     DEBUG=True
     SECRET_KEY=your_django_secret_key_here
     ALLOWED_HOSTS=localhost,127.0.0.1
     ```

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

8. Access the application at http://127.0.0.1:8000/

## Features

- Create and share your vibes
- Browse vibes from other users
- Admin interface for managing content

## Database Configuration

By default, the application uses SQLite for development. To use PostgreSQL:

1. Create a PostgreSQL database and user:
   ```sql
   CREATE DATABASE vibezin_db;
   CREATE USER vibezin_user WITH PASSWORD 'your_secure_password';
   ALTER ROLE vibezin_user SET client_encoding TO 'utf8';
   ALTER ROLE vibezin_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE vibezin_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE vibezin_db TO vibezin_user;
   ```

2. Uncomment the PostgreSQL configuration in `vibezin_project/settings.py`
