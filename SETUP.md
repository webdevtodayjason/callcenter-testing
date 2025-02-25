# First-Time Setup Instructions

Follow these steps to set up the repository for the first time:

## 1. Initialize Git Repository

If you haven't already initialized a Git repository, run:

```bash
git init
```

## 2. Add Files to Git

Add all the files to the Git repository:

```bash
git add .
```

## 3. Make the First Commit

Commit the files with an initial commit message:

```bash
git commit -m "Initial commit: Call Center Testing Script"
```

## 4. Set Up Remote Repository

Connect to your GitHub repository:

```bash
git remote add origin https://github.com/webdevtodayjason/callcenter-testing.git
```

## 5. Push to GitHub

Push the code to GitHub:

```bash
git push -u origin main
```

Note: If your default branch is named `master` instead of `main`, use:

```bash
git push -u origin master
```

## 6. Verify the Repository

Visit https://github.com/webdevtodayjason/callcenter-testing to verify that your code has been pushed successfully.

## 7. Set Up Environment

1. Create a `.env` file based on the `.env.example` template:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your actual Twilio credentials and other configuration.

## 8. Create Conda Environment

```bash
conda create -n callcenter-testing python=3.11
conda activate callcenter-testing
pip install -r requirements.txt
```

## 9. Run the Application

```bash
python app.py
```

The application will be available at http://localhost:5005. 