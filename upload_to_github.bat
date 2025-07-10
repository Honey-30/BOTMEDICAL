@echo off
echo ====================================================
echo      GitHub Upload Script for AI Healthcare Chatbot
echo ====================================================
echo.

cd /d "c:\Users\Honey\Downloads\chatbot"
echo Current directory: %CD%
echo.

echo Step 1: Initialize Git Repository...
git init
echo.

echo Step 2: Configure Git (if not already configured)...
echo Please enter your name when prompted:
git config user.name "Honey-30"
echo Please enter your email when prompted:
git config user.email "your-email@example.com"
echo.

echo Step 3: Add all files to Git...
git add .
echo.

echo Step 4: Create initial commit...
git commit -m "Initial commit: Advanced AI Healthcare Chatbot System with Modern UI/UX"
echo.

echo Step 5: Set main branch...
git branch -M main
echo.

echo Step 6: Add remote repository...
git remote add origin https://github.com/Honey-30/medibot.git
echo.

echo Step 7: Push to GitHub...
echo Note: You may need to authenticate with GitHub
echo If you have 2FA enabled, use a Personal Access Token instead of password
git push -u origin main
echo.

echo ====================================================
echo Upload complete! Your project is now on GitHub at:
echo https://github.com/Honey-30/medibot
echo ====================================================
pause
