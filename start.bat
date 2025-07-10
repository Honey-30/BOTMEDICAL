@echo off
echo Setting up AI Healthcare Chatbot...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH!
    echo Please install Python 3.11 or later from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Download spaCy models
echo Downloading spaCy models...
python -m spacy download en_core_web_sm

REM Initialize database
echo Initializing database...
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized successfully!')"

REM Start the application
echo Starting AI Healthcare Chatbot...
echo.
echo ================================================
echo AI Healthcare Chatbot is starting...
echo Open your browser and go to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo ================================================
echo.

python run.py

pause
