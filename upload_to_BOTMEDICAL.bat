@echo off
echo ====================================================
echo   AI Healthcare Chatbot - Upload to BOTMEDICAL
echo ====================================================
echo.

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

REM Remove existing git repository if it exists
if exist .git (
    echo 🔄 Removing existing git repository...
    rmdir /s /q .git
    echo ✅ Cleaned up existing git repository
    echo.
)

REM Initialize fresh git repository
echo 🔄 Step 1: Initializing fresh Git repository...
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
git commit -m "Initial commit: Advanced AI Healthcare Chatbot System

🏥 BOTMEDICAL - AI Healthcare Assistant
=======================================

Features:
✅ Modern glassmorphism UI/UX design
✅ AI-powered symptom analysis & diagnosis
✅ Advanced conversational interface
✅ User authentication & security
✅ Admin dashboard with analytics
✅ Docker containerization
✅ CI/CD pipeline configuration
✅ Comprehensive test suite
✅ Production-ready deployment
✅ API documentation & monitoring

Built with Flask, Bootstrap, AI/ML models, and modern web technologies.
Ready for production deployment with Docker and comprehensive monitoring."

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

REM Add remote repository (new URL)
echo 🔗 Step 6: Adding GitHub remote (BOTMEDICAL)...
git remote add origin https://github.com/Honey-30/BOTMEDICAL.git
if %errorlevel% neq 0 (
    echo ⚠️  Remote might already exist, trying to set URL...
    git remote set-url origin https://github.com/Honey-30/BOTMEDICAL.git
)
echo ✅ GitHub remote added for BOTMEDICAL
echo.

REM Push to GitHub
echo 🚀 Step 7: Pushing to GitHub (BOTMEDICAL)...
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
    echo ❌ Push failed. Trying alternative methods...
    echo.
    
    REM Try to pull first in case repo has content
    echo 🔄 Attempting to pull remote changes first...
    git pull origin main --allow-unrelated-histories
    if %errorlevel% neq 0 (
        echo ⚠️  Pull failed, trying force push...
        echo.
        echo ⚠️  WARNING: Force push will overwrite remote content
        echo    Type 'yes' to continue with force push, or 'no' to cancel:
        set /p confirm=
        if /i "%confirm%"=="yes" (
            git push -f origin main
            if %errorlevel% neq 0 (
                echo ❌ Force push failed
                echo.
                echo 💡 Try GitHub Desktop instead: https://desktop.github.com/
                pause
                exit /b 1
            )
        ) else (
            echo Operation cancelled
            pause
            exit /b 1
        )
    ) else (
        echo ✅ Successfully pulled remote changes
        echo 🚀 Now pushing to GitHub...
        git push origin main
        if %errorlevel% neq 0 (
            echo ❌ Push still failed
            pause
            exit /b 1
        )
    )
)

echo.
echo ====================================================
echo 🎉 SUCCESS! Your project is now on GitHub!
echo ====================================================
echo.
echo 🔗 Repository URL: https://github.com/Honey-30/BOTMEDICAL
echo 📊 Features uploaded:
echo    ✅ Modern glassmorphism UI design
echo    ✅ AI-powered healthcare chatbot
echo    ✅ Advanced symptom analysis
echo    ✅ User authentication system
echo    ✅ Admin dashboard with analytics
echo    ✅ Docker containerization
echo    ✅ CI/CD pipeline configuration
echo    ✅ Comprehensive test suite
echo    ✅ Production-ready setup
echo    ✅ API documentation
echo.
echo 🌟 Next steps:
echo 1. Visit: https://github.com/Honey-30/BOTMEDICAL
echo 2. Add repository description: "Advanced AI Healthcare Chatbot"
echo 3. Add topics: ai, healthcare, chatbot, flask, docker, machine-learning
echo 4. Enable GitHub Pages (optional)
echo 5. Star your repository! ⭐
echo.
echo 🚀 Your BOTMEDICAL AI Healthcare Chatbot is now live!
echo ====================================================
pause
