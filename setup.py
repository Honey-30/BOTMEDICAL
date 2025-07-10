"""
Setup configuration for the AI Healthcare Chatbot.
"""

from setuptools import setup, find_packages

setup(
    name="ai-healthcare-chatbot",
    version="1.0.0",
    description="Advanced AI Healthcare Chatbot for Symptom Checking",
    author="Healthcare AI Team",
    author_email="team@healthcareai.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "Flask>=2.3.0",
        "Flask-SQLAlchemy>=3.0.0",
        "Flask-Login>=0.6.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
