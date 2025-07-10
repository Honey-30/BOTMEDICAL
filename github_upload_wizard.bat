@echo off
setlocal enabledelayedexpansion

echo ====================================================
echo   AI Healthcare Chatbot - GitHub Upload Wizard
echo ====================================================
echo.

REM Change to the project directory
cd /d "c:\Users\Honey\Downloads\chatbot"

echo Current directory: %CD%
echo.

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed or not in PATH
    echo.
    echo Please install Git first:
    echo 1. Download from: https://git-scm.com/download/win
    echo 2. Install with default settings
    echo 3. Restart Command Prompt
    echo 4. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Git is installed and working
echo.

REM Initialize git repository
echo 🔄 Step 1: Initializing Git repository...
git init
if %errorlevel% neq 0 (
    echo ❌ Failed to initialize Git repository
    pause
    exit /b 1
)
echo ✅ Git repository initialized
echo.

REM Configure git user
echo 🔧 Step 2: Configuring Git user...
set /p git_name="Enter your GitHub username (or press Enter for 'Honey-30'): "
if "%git_name%"=="" set git_name=Honey-30

set /p git_email="Enter your GitHub email: "
if "%git_email%"=="" (
    echo ❌ Email is required
    pause
    exit /b 1
)

git config user.name "%git_name%"
git config user.email "%git_email%"
echo ✅ Git user configured
echo.

REM Add all files
echo 📁 Step 3: Adding all files to Git...
git add .
if %errorlevel% neq 0 (
    echo ❌ Failed to add files
    pause
    exit /b 1
)
echo ✅ All files added to Git
echo.

REM Create initial commit
echo 💾 Step 4: Creating initial commit...
git commit -m "Initial commit: Advanced AI Healthcare Chatbot System with Modern UI/UX - Production ready with Docker, CI/CD, and comprehensive features"
if %errorlevel% neq 0 (
    echo ❌ Failed to create commit
    pause
    exit /b 1
)
echo ✅ Initial commit created
echo.

REM Set main branch
echo 🌟 Step 5: Setting main branch...
git branch -M main
echo ✅ Main branch set
echo.

REM Add remote repository
echo 🔗 Step 6: Adding GitHub remote...
git remote add origin https://github.com/Honey-30/medibot.git
if %errorlevel% neq 0 (
    echo ⚠️  Remote might already exist, trying to set URL...
    git remote set-url origin https://github.com/Honey-30/medibot.git
)
echo ✅ GitHub remote added
echo.

REM Push to GitHub
echo 🚀 Step 7: Pushing to GitHub...
echo.
echo ⚠️  IMPORTANT: GitHub Authentication Required
echo.
echo If you have 2FA enabled, you MUST use a Personal Access Token:
echo 1. Go to: https://github.com/settings/tokens
echo 2. Click "Generate new token (classic)"
echo 3. Select "repo" permissions
echo 4. Copy the token
echo 5. Use the token as your password when prompted
echo.
echo Otherwise, use your regular GitHub password.
echo.
pause

git push -u origin main
if %errorlevel% neq 0 (
    echo ❌ Push failed. Common issues:
    echo 1. Wrong credentials
    echo 2. Repository doesn't exist
    echo 3. Need Personal Access Token for 2FA
    echo 4. Network issues
    echo.
    echo Solutions:
    echo 1. Create repository at: https://github.com/new
    echo 2. Use Personal Access Token if 2FA is enabled
    echo 3. Check your internet connection
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo 🎉 SUCCESS! Your project is now on GitHub!
echo ====================================================
echo.
echo 🔗 Repository URL: https://github.com/Honey-30/medibot
echo 📊 Features uploaded:
echo    ✅ Modern glassmorphism UI design
echo    ✅ AI-powered healthcare chatbot
echo    ✅ Docker containerization
echo    ✅ CI/CD pipeline configuration
echo    ✅ Comprehensive test suite
echo    ✅ Admin dashboard
echo    ✅ Security features
echo    ✅ API documentation
echo    ✅ Production-ready setup
echo.
echo 🌟 Next steps:
echo 1. Visit: https://github.com/Honey-30/medibot
echo 2. Add repository description
echo 3. Enable GitHub Pages (optional)
echo 4. Star your repository! ⭐
echo.
echo ====================================================
echo                Thank you for using our wizard!
echo ====================================================
pause
