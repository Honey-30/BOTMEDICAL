# PowerShell Script to Upload to BOTMEDICAL Repository

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   AI Healthcare Chatbot - Upload to BOTMEDICAL" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Set location
Set-Location "c:\Users\Honey\Downloads\chatbot"
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "✅ Git is installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Remove existing git repository if it exists
if (Test-Path ".git") {
    Write-Host "🔄 Removing existing git repository..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".git"
    Write-Host "✅ Cleaned up existing git repository" -ForegroundColor Green
    Write-Host ""
}

# Initialize fresh git repository
Write-Host "🔄 Initializing fresh Git repository..." -ForegroundColor Yellow
try {
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to initialize Git repository" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Configure git user
Write-Host "🔧 Configuring Git user..." -ForegroundColor Yellow
$gitName = Read-Host "Enter your GitHub username (or press Enter for 'Honey-30')"
if (-not $gitName) { $gitName = "Honey-30" }

$gitEmail = Read-Host "Enter your GitHub email"
if (-not $gitEmail) {
    Write-Host "❌ Email is required!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

git config user.name "$gitName"
git config user.email "$gitEmail"
Write-Host "✅ Git user configured" -ForegroundColor Green

Write-Host ""

# Add all files
Write-Host "📁 Adding all files to Git..." -ForegroundColor Yellow
try {
    git add .
    Write-Host "✅ All files added to Git" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to add files" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Create initial commit
Write-Host "💾 Creating initial commit..." -ForegroundColor Yellow
try {
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

    Write-Host "✅ Initial commit created" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create commit" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Set main branch
Write-Host "🌟 Setting main branch..." -ForegroundColor Yellow
git branch -M main
Write-Host "✅ Main branch set" -ForegroundColor Green

Write-Host ""

# Add remote repository (new URL)
Write-Host "🔗 Adding GitHub remote (BOTMEDICAL)..." -ForegroundColor Yellow
try {
    git remote add origin https://github.com/Honey-30/BOTMEDICAL.git
    Write-Host "✅ GitHub remote added for BOTMEDICAL" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Remote might already exist, trying to set URL..." -ForegroundColor Yellow
    git remote set-url origin https://github.com/Honey-30/BOTMEDICAL.git
    Write-Host "✅ GitHub remote URL set for BOTMEDICAL" -ForegroundColor Green
}

Write-Host ""

# Push to GitHub
Write-Host "🚀 Pushing to GitHub (BOTMEDICAL)..." -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  IMPORTANT: GitHub Authentication Required" -ForegroundColor Red
Write-Host ""
Write-Host "If you have 2FA enabled, you MUST use a Personal Access Token:" -ForegroundColor Yellow
Write-Host "1. Go to: https://github.com/settings/tokens" -ForegroundColor Cyan
Write-Host "2. Click 'Generate new token (classic)'" -ForegroundColor Cyan
Write-Host "3. Select 'repo' permissions" -ForegroundColor Cyan
Write-Host "4. Copy the token" -ForegroundColor Cyan
Write-Host "5. Use the token as your password when prompted" -ForegroundColor Cyan
Write-Host ""
Write-Host "Otherwise, use your regular GitHub password." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue"

try {
    git push -u origin main
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host "🎉 SUCCESS! Your project is now on GitHub!" -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Repository URL: https://github.com/Honey-30/BOTMEDICAL" -ForegroundColor Cyan
    Write-Host "📊 Features uploaded:" -ForegroundColor Yellow
    Write-Host "   ✅ Modern glassmorphism UI design" -ForegroundColor Green
    Write-Host "   ✅ AI-powered healthcare chatbot" -ForegroundColor Green
    Write-Host "   ✅ Advanced symptom analysis" -ForegroundColor Green
    Write-Host "   ✅ User authentication system" -ForegroundColor Green
    Write-Host "   ✅ Admin dashboard with analytics" -ForegroundColor Green
    Write-Host "   ✅ Docker containerization" -ForegroundColor Green
    Write-Host "   ✅ CI/CD pipeline configuration" -ForegroundColor Green
    Write-Host "   ✅ Comprehensive test suite" -ForegroundColor Green
    Write-Host "   ✅ Production-ready setup" -ForegroundColor Green
    Write-Host "   ✅ API documentation" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌟 Next steps:" -ForegroundColor Yellow
    Write-Host "1. Visit: https://github.com/Honey-30/BOTMEDICAL" -ForegroundColor Cyan
    Write-Host "2. Add repository description: 'Advanced AI Healthcare Chatbot'" -ForegroundColor Cyan
    Write-Host "3. Add topics: ai, healthcare, chatbot, flask, docker, machine-learning" -ForegroundColor Cyan
    Write-Host "4. Enable GitHub Pages (optional)" -ForegroundColor Cyan
    Write-Host "5. Star your repository! ⭐" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🚀 Your BOTMEDICAL AI Healthcare Chatbot is now live!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Push failed. Trying alternative methods..." -ForegroundColor Red
    Write-Host ""
    
    # Try to pull first in case repo has content
    Write-Host "🔄 Attempting to pull remote changes first..." -ForegroundColor Yellow
    try {
        git pull origin main --allow-unrelated-histories
        Write-Host "✅ Successfully pulled remote changes" -ForegroundColor Green
        Write-Host "🚀 Now pushing to GitHub..." -ForegroundColor Yellow
        git push origin main
        Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "=====================================================" -ForegroundColor Green
        Write-Host "🎉 SUCCESS! Your project is now on GitHub!" -ForegroundColor Green
        Write-Host "=====================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "🔗 Repository URL: https://github.com/Honey-30/BOTMEDICAL" -ForegroundColor Cyan
        
    } catch {
        Write-Host "⚠️  Pull failed, trying force push..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "⚠️  WARNING: Force push will overwrite remote content" -ForegroundColor Red
        $confirm = Read-Host "Type 'yes' to continue with force push, or 'no' to cancel"
        
        if ($confirm -eq 'yes') {
            try {
                git push -f origin main
                Write-Host "✅ Force push successful!" -ForegroundColor Green
                
                Write-Host ""
                Write-Host "=====================================================" -ForegroundColor Green
                Write-Host "🎉 SUCCESS! Your project is now on GitHub!" -ForegroundColor Green
                Write-Host "=====================================================" -ForegroundColor Green
                Write-Host ""
                Write-Host "🔗 Repository URL: https://github.com/Honey-30/BOTMEDICAL" -ForegroundColor Cyan
                
            } catch {
                Write-Host "❌ Force push failed. Please try GitHub Desktop instead." -ForegroundColor Red
                Write-Host "Download: https://desktop.github.com/" -ForegroundColor Cyan
            }
        } else {
            Write-Host "Operation cancelled. Try GitHub Desktop instead." -ForegroundColor Yellow
            Write-Host "Download: https://desktop.github.com/" -ForegroundColor Cyan
        }
    }
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "           Thank you for using our script!" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
