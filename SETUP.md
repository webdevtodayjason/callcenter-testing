# First-Time Setup Instructions

Follow these steps to set up the repository for the first time:

## 1. Verify the Repository

Visit https://github.com/webdevtodayjason/callcenter-testing to verify that your code has been pushed successfully.

## 2. Set Up Environment

1. Create a `.env` file based on the `.env.example` template:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your actual Twilio credentials and other configuration.

## 3. Create Conda Environment

```bash
conda create -n callcenter-testing python=3.11
conda activate callcenter-testing
pip install -r requirements.txt
```

## 4. Run the Application

```bash
python app.py
```

The application will be available at http://localhost:5005. 