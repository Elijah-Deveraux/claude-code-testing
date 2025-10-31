# Virtual Environment Setup Instructions

## Overview
This project uses Python 3.12 virtual environment (venv) for dependency isolation.

## Setup Steps

### 1. Create Virtual Environment
```bash
python3.12 -m venv venv
```

### 2. Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Verify Activation
You should see `(venv)` prefix in your terminal prompt.

Check Python version:
```bash
python --version
# Should output: Python 3.12.x
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Verify Installation
```bash
pip list
```

## Deactivation
To deactivate the virtual environment:
```bash
deactivate
```

## Troubleshooting

### Python 3.12 not found
- Ensure Python 3.12 is installed on your system
- Try `python3.12 --version` to verify installation

### Permission errors
- Use `pip install --user` if needed
- On Linux/macOS, avoid using `sudo` with pip

### Virtual environment not activating
- Delete the `venv` folder and recreate it
- Check for typos in the activation command
