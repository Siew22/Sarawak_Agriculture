# 🌿 Sarawak Agri-Advisor: An End-to-End AI Plant Doctor

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

An AI-powered, 100% self-developed plant disease diagnosis system designed for farmers in Sarawak, with a specialized focus on Black Pepper cultivation. This is a complete end-to-end web application that provides instant, AI-driven diagnosis, environmental risk assessment, and actionable management advice in multiple languages.

The entire system, from data collection and model training to a multi-user backend API and deployment, is built from the ground up, demonstrating a full-stack AI development lifecycle.

---

## ✨ Core Features

-   **📸 100% Self-Developed AI Model:** Upload a leaf photo for instant diagnosis. The core is a custom `EfficientNet` model, **trained from scratch** on a curated dataset of local pepper diseases.
-   **👥 Multi-User System with 2FA:** Secure registration and login for `Public` and `Business` users, featuring email verification (2FA) for account activation.
-   **🌦️ Fuzzy Logic Risk Assessment:** Automatically fetches local weather (via GPS) and uses a `Scikit-fuzzy` based inference system to calculate a real-time environmental risk score.
-   **🌐 Dynamic & Multilingual Reporting:** Generates comprehensive diagnostic reports in **English, Bahasa Malaysia, and Chinese**, sourced from a structured YAML knowledge base.
-   **🧠 AI-Enhanced Web Search:** For unrecognized diseases, the system uses a custom-trained **Siamese Network (LSTM-based)** to perform semantic web searches and find relevant information.
-   **🔍 XAI Model Explainability:** Provides **Grad-CAM** heatmaps to visualize which parts of the image the AI model focused on, making the diagnosis transparent.
-   **🌱 Self-Learning Architecture:** The system can automatically add new discoveries to the dataset and knowledge base, triggering a background retraining process via **Celery & Redis**.
-   **🐳 Dockerized Deployment:** The entire application stack (FastAPI, Celery Worker, Redis, MySQL) is containerized using **Docker Compose** for easy, reproducible deployment.

---

## 🛠️ Technology Stack

-   **Backend:** FastAPI, Uvicorn
-   **Database:** MySQL with SQLAlchemy (ORM)
-   **AI & Machine Learning:** PyTorch, Scikit-fuzzy, Grad-CAM, Sentence-Transformers, Passlib (for password hashing)
-   **Async Task Queue:** Celery, Redis
-   **Deployment:** Docker, Docker Compose
-   **Frontend:** Vanilla HTML5, CSS3, JavaScript (Fetch API, Geolocation API)
-   **Email Service (Dev):** Python's built-in `smtpd` for local debugging.

---

## 🚀 Getting Started Instructions

Follow these instructions to get the full project running on your local machine for development and testing.

### Prerequisites

1.  **Git & Git LFS:** [Download Git](https://git-scm.com/downloads), [Install Git LFS](https://git-lfs.github.com/).
2.  **Python 3.10:** [Download Python](https://www.python.org/downloads/).
3.  **MySQL Server & Workbench:** [Download MySQL Community Server](https://dev.mysql.com/downloads/mysql/) and [MySQL Workbench](https://dev.mysql.com/downloads/workbench/). During installation, remember your `root` user password.
4.  **(Optional for AI Training)** An NVIDIA GPU with CUDA drivers.

### Step-by-Step Setup

**1. Clone the Repository**
   - First, ensure Git LFS is installed on your system. Open your terminal (Git Bash, PowerShell, etc.) and run:
     ```bash
     git lfs install
     ```
   - Clone the project. This will automatically download the large dataset and model files tracked by LFS.
     ```bash
     git clone https://github.com/Siew22/Sarawak_Agriculture.git
     cd Sarawak_Agriculture
     ```

**2. Set Up the Database**
   - Start your MySQL Server.
   - Open **MySQL Workbench** and connect to your local server.
   - Create a new database (schema) for the project. Run this SQL command:
     ```sql
     CREATE DATABASE sarawak_agri_prod;
     ```

**3. Configure Environment Variables**
   - In the project's root directory, find the `.env.example` file (if it exists) and rename it to `.env`. If it doesn't exist, create a new file named `.env`.
   - Open the `.env` file and fill in your details:
     ```ini
     # --- Database Configuration ---
     DB_HOST=127.0.0.1
     DB_PORT=3306
     DB_USER=root
     DB_PASSWORD="YOUR_MYSQL_ROOT_PASSWORD"  # <-- IMPORTANT: Replace with your actual password
     DB_NAME="sarawak_agri_prod"

     # --- Other Settings (Keep as is for now) ---
     PROJECT_NAME="Sarawak Agri-Advisor"
     CONFIDENCE_THRESHOLD=0.75
     SERPAPI_KEY="" 
     ALLOWED_ORIGINS="http://localhost,http://localhost:8080,http://127.0.0.1:5500,null"
     ```

**4. Set Up Python Virtual Environment**
   - From the project root directory in your terminal:
     ```bash
     # Create a virtual environment
     python -m venv env

     # Activate it
     # On Windows (PowerShell):
     .\env\Scripts\Activate.ps1
     # On macOS/Linux:
     # source env/bin/activate
     
     # Install all required packages
     pip install -r requirements.txt
     ```

**5. You are ready to run the application!**

---

## ▶️ Running the Application (Development Mode)

The application requires **two separate terminal windows** to run in development mode.

**Terminal 1: Start the Local Email Debug Server**
   - Open a new terminal, navigate to the project directory, and activate the virtual environment.
   - Run the following command. This terminal will "listen" for emails and print them. **Do not close it.**
     ```bash
     python -m smtpd -c DebuggingServer -n localhost:8025
     ```

**Terminal 2: Start the FastAPI Backend Server**
   - Open another new terminal, navigate to the project directory, and activate the virtual environment.
   - Run the Uvicorn server. It will automatically connect to the database and email server.
     ```bash
     uvicorn app.main:app --reload
     ```
   - The backend is now live at `http://127.0.0.1:8000`. The first time you run this, it will automatically create all necessary tables in your `sarawak_agri_prod` database.

**Access the Frontend**
   - Navigate to the `frontend/` directory in your file explorer.
   - Double-click the `login.html` file to open it in your browser.
   - You can now test the full registration -> email verification -> login -> dashboard -> AI diagnosis workflow.

---

## 🐳 Running with Docker (Production/Easy Mode)

Once Docker Desktop is installed, you can run the entire stack with a single command.

1.  Make sure your `.env` file is correctly configured as described in the setup steps.
2.  From the project root directory, run:
    ```bash
    docker-compose up --build
    ```
    This will start the FastAPI backend, Redis, and a Celery worker. *Note: The provided `docker-compose.yml` does not include MySQL; it assumes a separate database instance.*

---

## 🔬 Training Your Own Models (Optional)

If you wish to retrain the models:

1.  **Image Classifier:**
    - Place your datasets in the appropriate folders.
    - Run the training script:
      ```bash
      python app/train/train_model_2.py
      ```
2.  **NLG Sentence Encoder:**
    - Update the training data in `knowledge_base/nlg_training_data.json`.
    - Run the training script:
      ```bash
      python app/train/train_nlg_model.py
      ```

---

## 📂 Project Structure

```
.
├── app/                  # Main FastAPI backend application
│   ├── auth/             # Authentication logic and schemas
│   ├── models/           # AI models (classifier, fuzzy logic, etc.)
│   ├── routers/          # API endpoints (users, token)
│   ├── services/         # Business logic (email, weather, etc.)
│   ├── train/            # Scripts for training models
│   ├── utils/            # Utility functions (image processing, XAI)
│   ├── database.py       # SQLAlchemy setup and ORM models
│   └── main.py           # FastAPI entrypoint
├── frontend/             # All frontend files (HTML, CSS, JS)
├── knowledge_base/       # YAML files for multilingual disease info
├── models_store/         # Stores trained model weights (.pth)
├── static/               # For serving static files like uploaded images
├── .env                  # Environment variables (!!! DO NOT COMMIT !!!)
├── docker-compose.yml    # Docker configuration
├── Dockerfile            # Instructions to build the backend image
└── requirements.txt      # Python dependencies
```