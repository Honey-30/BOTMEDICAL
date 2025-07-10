@echo off
echo ====================================================
echo   BOTMEDICAL - Fix Push Rejection Error
echo ====================================================
echo.

cd /d "c:\Users\Honey\Downloads\chatbot"

echo Current directory: %CD%
echo.

echo 🔍 Issue: The BOTMEDICAL repository has content that conflicts with your local files
echo 💡 Solution: We'll merge the remote changes and then push your project
echo.

echo Method 1: Pull and merge remote changes...
git pull origin main --allow-unrelated-histories
if %errorlevel% neq 0 (
    echo ❌ Method 1 failed, trying Method 2...
    echo.
    
    echo Method 2: Fetch and merge separately...
    git fetch origin main
    if %errorlevel% neq 0 (
        echo ❌ Fetch failed, trying Method 3...
        goto :method3
    )
    
    git merge origin/main --allow-unrelated-histories --no-edit
    if %errorlevel% neq 0 (
        echo ❌ Merge failed, trying Method 3...
        goto :method3
    )
    
    echo ✅ Successfully merged remote changes
    echo.
    
    echo 📤 Now pushing your BOTMEDICAL project...
    git push origin main
    if %errorlevel% neq 0 (
        echo ❌ Push still failed, trying Method 3...
        goto :method3
    )
    
    echo ✅ Successfully pushed to BOTMEDICAL repository!
    goto :success
)

echo ✅ Successfully pulled and merged remote changes
echo.

echo 📤 Now pushing your BOTMEDICAL project...
git push origin main
if %errorlevel% neq 0 (
    echo ❌ Push failed, trying Method 3...
    goto :method3
)

echo ✅ Successfully pushed to BOTMEDICAL repository!
goto :success

:method3
echo.
echo Method 3: Force push (overwrites remote content)
echo.
echo ⚠️  WARNING: This will overwrite any existing content in the repository
echo    Your AI Healthcare Chatbot will replace whatever is currently there.
echo.
echo Type 'yes' to continue with force push, or 'no' to cancel:
set /p confirm=
if /i "%confirm%"=="yes" (
    echo.
    echo 🚀 Force pushing to BOTMEDICAL repository...
    git push -f origin main
    if %errorlevel% neq 0 (
        echo ❌ Force push failed. Please try GitHub Desktop instead.
        echo    Download: https://desktop.github.com/
        pause
        exit /b 1
    )
    echo ✅ Force push successful!
    goto :success
) else (
    echo.
    echo Operation cancelled. Alternative solutions:
    echo 1. Use GitHub Desktop: https://desktop.github.com/
    echo 2. Delete and recreate the repository on GitHub
    echo 3. Try uploading via web interface
    pause
    exit /b 1
)

:success
echo.
echo ====================================================
echo 🎉 SUCCESS! BOTMEDICAL is now live on GitHub!
echo ====================================================
echo.
echo 🔗 Repository URL: https://github.com/Honey-30/BOTMEDICAL
echo.
echo 🏥 Your AI Healthcare Chatbot features now available:
echo    ✅ Modern glassmorphism UI design
echo    ✅ AI-powered symptom analysis
echo    ✅ Advanced conversational interface
echo    ✅ User authentication & security
echo    ✅ Admin dashboard with analytics
echo    ✅ Docker containerization
echo    ✅ CI/CD pipeline configuration
echo    ✅ Comprehensive test suite
echo    ✅ Production-ready deployment
echo    ✅ API documentation
echo.
echo 🌟 Next steps:
echo 1. Visit: https://github.com/Honey-30/BOTMEDICAL
echo 2. Add repository description: "Advanced AI Healthcare Chatbot"
echo 3. Add topics: ai, healthcare, chatbot, flask, docker, python
echo 4. Enable GitHub Pages for live demo (optional)
echo 5. Share your project with the world! 🌍
echo.
echo 🎯 Your BOTMEDICAL AI Healthcare Chatbot is now showcased on GitHub!
echo ====================================================
pause
