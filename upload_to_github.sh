#!/bin/bash

# GitHub Upload Script for AI Healthcare Chatbot
# This script will prepare and upload your project to GitHub

echo "======================================================"
echo "      AI Healthcare Chatbot - GitHub Upload         "
echo "======================================================"
echo

# Navigate to project directory
cd "$(dirname "$0")"

echo "Current directory: $(pwd)"
echo

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    echo "   Download from: https://git-scm.com/"
    exit 1
fi

echo "✅ Git is installed"

# Initialize git repository
echo "🔄 Initializing Git repository..."
git init

# Configure git user (you may need to update these)
echo "🔧 Configuring Git user..."
git config user.name "Honey-30"
git config user.email "your-email@example.com"

# Add all files
echo "📁 Adding all files to Git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Advanced AI Healthcare Chatbot System

Features:
- Modern glassmorphism UI/UX design
- AI-powered symptom checker
- Advanced chat interface
- User authentication & authorization
- Admin dashboard with analytics
- Docker containerization
- CI/CD pipeline ready
- Comprehensive test suite
- Production-ready configuration
- Security best practices
- API documentation
- Multi-language support"

# Set main branch
echo "🌟 Setting main branch..."
git branch -M main

# Add remote repository
echo "🔗 Adding GitHub remote..."
git remote add origin https://github.com/Honey-30/medibot.git

# Push to GitHub
echo "🚀 Pushing to GitHub..."
echo "Note: You may need to authenticate with GitHub"
echo "If you have 2FA enabled, use a Personal Access Token instead of password"

git push -u origin main

if [ $? -eq 0 ]; then
    echo
    echo "======================================================"
    echo "🎉 SUCCESS! Your project is now on GitHub!"
    echo "======================================================"
    echo
    echo "🔗 Repository URL: https://github.com/Honey-30/medibot"
    echo "📱 GitHub Pages (if enabled): https://honey-30.github.io/medibot"
    echo
    echo "Next steps:"
    echo "1. Visit your repository to see the uploaded code"
    echo "2. Enable GitHub Pages for live demo (optional)"
    echo "3. Set up secrets for CI/CD pipeline"
    echo "4. Configure environment variables for deployment"
    echo "5. Star your repository! ⭐"
    echo
else
    echo
    echo "❌ Upload failed. Please check your credentials and try again."
    echo "💡 Common solutions:"
    echo "   - Use Personal Access Token if 2FA is enabled"
    echo "   - Check your internet connection"
    echo "   - Verify repository URL is correct"
    echo
fi

echo "======================================================"
echo "                    Thank you!                       "
echo "======================================================"
