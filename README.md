# 🌿 Sarawak Agri-Advisor: End-to-End AI Plant Doctor for Sarawak Agriculture

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

---

## 📜 Project Overview

**Sarawak Agri-Advisor** is a sophisticated, full-stack AI-powered web application designed to serve as a "digital agronomist" for farmers in Sarawak. With a specialized initial focus on **Black Pepper**, the state's iconic crop, this platform provides instant plant disease diagnosis, real-time environmental risk assessment, and actionable management advice in multiple languages.

This project is not just a standalone AI model; it is a complete, scalable, and commercially-viable ecosystem built from the ground up. It demonstrates the entire AI product lifecycle: from automated data collection and custom model training to a feature-rich, multi-user backend API, a responsive frontend, and a containerized deployment architecture. It bridges the gap between advanced AI technology and practical, on-the-ground agricultural needs.

---

## 🎯 Mission, Vision, and Objectives

### **Our Vision**
To empower every farmer in Sarawak with accessible, data-driven agricultural intelligence, transforming traditional farming practices through technology to ensure food security and economic prosperity for the region.

### **Our Mission**
To deliver an intuitive, reliable, and localized AI-powered platform that provides immediate and actionable insights for crop management, starting with Sarawak's black pepper industry, thereby reducing crop loss, optimizing resource usage, and increasing profitability for local farmers.

### **Core Objectives**
1.  **Democratize Agronomy:** Provide small to medium-scale farmers with affordable access to expert-level crop disease diagnosis, traditionally available only through human experts.
2.  **Reduce Crop Loss:** Enable early detection and provide immediate, localized treatment recommendations to mitigate the impact of devastating diseases like Foot Rot and Pollu Disease.
3.  **Promote Sustainable Farming:** Offer environmental risk assessments to help farmers make informed decisions about resource application (e.g., fungicides), reducing chemical usage and operational costs.
4.  **Build a Community:** Foster a digital ecosystem where farmers and businesses can connect, share knowledge, and trade goods, creating a self-sustaining agricultural network.
5.  **Create a Scalable Platform:** Develop a robust, microservices-based architecture that can be easily expanded to include other crops (e.g., oil palm, paddy) and advanced features (e.g., yield prediction, automated drone integration).

---

## 💡 Core Features & The User Journey

The platform offers a seamless flow for users, from diagnosis to community interaction and e-commerce.

### **User Flow**
1.  **Registration & Login**: A user (either `Public` or `Business`) registers and verifies their account via email.
2.  **AI Diagnosis**: The user uploads a photo of a pepper leaf. The system uses their device's GPS to fetch local weather data.
3.  **Instant Report**: Within seconds, the user receives a comprehensive, multilingual report detailing:
    *   **The diagnosed disease** (from a custom-trained PyTorch model).
    *   **Environmental risk level** (from a Scikit-fuzzy logic system).
    *   **AI's reasoning** (via Grad-CAM heatmaps showing where the AI "looked").
    *   **Actionable management advice** from a localized knowledge base.
4.  **Community Interaction**: Users can share their findings, ask questions, and comment on posts within the community platform.
5.  **Marketplace & E-commerce**: Business users can list products (e.g., fertilizers, disease-free seedlings), and public users can browse and purchase them, completing the cycle from diagnosis to solution.
6.  **History Tracking**: All diagnosis reports and purchase orders are saved to the user's profile for future reference.

### **Key Technical Features**
-   **🚀 100% Self-Developed AI Model:** A custom `EfficientNet-B2` model, trained from scratch on a curated dataset of local black pepper diseases.
-   **👥 Multi-User System with Subscriptions:** Secure registration for `Public` and `Business` users with tiered feature access controlled by a subscription model.
-   **🌦️ Fuzzy Logic Risk Assessment:** Uses real-time weather data to calculate environmental risk scores.
-   **🌐 Dynamic & Multilingual Reporting:** Generates reports in English, Bahasa Malaysia, and Chinese.
-   **🔍 XAI Model Explainability:** Integrates **Grad-CAM** to provide visual transparency for AI diagnoses.
-   **🛒 Integrated E-commerce & Community Platform:** A full-featured marketplace and social posting system.
-   **💬 Real-Time Chat:** WebSocket-based chat for user-to-user communication.
-   **🐳 Fully Dockerized:** The entire stack is containerized with Docker Compose for one-command deployment.

---

## 🛠️ Technology Architecture & Code Modules

The project is built on a modern, decoupled microservices architecture. The structure is as follows:

-   `.` (Project Root)
    -   `app/`: Main FastAPI backend application
        -   `auth/`: Authentication (JWT, Passwords) & Schemas
        -   `models/`: AI models (Classifier, Fuzzy Logic, NLG)
        -   `routers/`: API endpoints (users, products, posts, etc.)
        -   `services/`: Business logic (Weather, Email, Permissions)
        -   `train/`: Scripts for training all AI models
        -   `database.py`: SQLAlchemy ORM models
        -   `main.py`: FastAPI application entrypoint
    -   `frontend/`: Vanilla JS, HTML5, CSS3 single-page application
    -   `knowledge_base/`: YAML files for multilingual disease info
    -   `models_store/`: Stores trained model weights (.pth, .json)
    -   `static/`: Serves user-uploaded images and generated content
    -   `.env`: Environment variables (**DO NOT COMMIT**)
    -   `docker-compose.yml`: Docker Compose orchestration file
    -   `Dockerfile`: Docker build instructions for the backend

-   **Backend (`FastAPI`)**: Serves as the central nervous system, handling API requests, orchestrating AI model inferences, and managing database interactions.
-   **Frontend (`Vanilla JS`)**: A lightweight, responsive user interface deployed on Vercel, communicating with the backend via a secure Ngrok tunnel during development.
-   **Database (`MySQL`)**: A relational database for storing user data, profiles, diagnosis history, posts, products, and orders.
-   **AI Core (`PyTorch`, `Scikit-fuzzy`)**: A collection of specialized Python modules responsible for image classification, risk assessment, and report generation.
-   **Asynchronous Tasks (`Celery`, `Redis`)**: Redis serves as a message broker for Celery, which can handle long-running background tasks like model retraining without blocking the API.
-   **Deployment (`Docker`)**: All services (backend, frontend, database, etc.) are containerized, ensuring consistency and simplifying deployment across any environment.

---

## 📈 Business Plan & Market Analysis

### **Target Market**
1.  **Primary**: Over 67,000 smallholder pepper farmers in Sarawak who lack immediate access to agricultural experts and rely on traditional methods for disease identification.
2.  **Secondary**: Larger plantation enterprises, agricultural cooperatives, and government agencies (e.g., Department of Agriculture Sarawak) seeking digital tools for monitoring and data collection.
3.  **Tertiary**: Local agricultural suppliers (fertilizers, pesticides, equipment) who can use the platform's Business accounts to market their products directly to farmers in need.

### **Financial Projections (Simplified Estimation)**

#### **Estimated Costs (Monthly)**
-   **Server Hosting (Cloud VM for Docker)**: RM 150 - RM 300 (e.g., DigitalOcean, AWS Lightsail)
-   **Database Hosting (Managed Service)**: RM 50 - RM 100
-   **Domain & SSL**: RM 10
-   **Third-Party APIs (e.g., Ngrok Pro, Email Service)**: RM 50
-   **Marketing & Outreach**: RM 200
-   **Total Estimated Monthly Cost**: **~RM 460 - RM 660**

#### **Revenue Model & Projections**
The platform utilizes a freemium subscription model to generate revenue.

| Tier              | Price (RM/month) | Target User | Key Features                                       |
| ----------------- | ---------------- | ----------- | -------------------------------------------------- |
| **Free**          | 0                | Public      | Limited AI diagnoses, access to community          |
| **Pro (Tier 10)**     | 10               | Public      | More diagnoses, shopping, chat, posting            |
| **Pro+ (Tier 15)**    | 15               | Public      | High-volume diagnoses, advanced analytics (future) |
| **Business (Tier 20)**| 20               | Business    | List products, view sales analytics, post          |

**Projected Monthly Revenue (Based on User Adoption):**

-   **Phase 1 (First 6 Months - 500 users):**
    -   400 Free Users
    -   80 Pro Users @ RM 10 = RM 800
    -   20 Business Users @ RM 20 = RM 400
    -   **Total Monthly Revenue**: **RM 1,200**
    -   **Estimated Monthly Profit**: **~RM 540 - RM 740**

-   **Phase 2 (First Year - 2,500 users):**
    -   1,800 Free Users
    -   500 Pro Users @ RM 10 = RM 5,000
    -   150 Pro+ Users @ RM 15 = RM 2,250
    -   50 Business Users @ RM 20 = RM 1,000
    -   **Total Monthly Revenue**: **RM 8,250**
    -   **Estimated Monthly Profit**: **~RM 7,590**

This model shows strong potential for profitability and scalability, especially as more farmers and businesses join the ecosystem.

---

## 🚀 Getting Started (Technical Instructions)

Follow these instructions to get the full project running on your local machine. The recommended method for both development and production is using **Docker Compose**.

### **Prerequisites**

1.  **Docker Desktop**: Install it from the [official Docker website](https://www.docker.com/products/docker-desktop/). This is the only requirement for the easiest setup.
2.  **Git & Git LFS**: Ensure Git is installed. Then, install Git LFS to handle large model files. Run `git lfs install` in your terminal once after installation.
3.  **(Optional - for Native Python mode)**: Python 3.10, MySQL Server.

### **1. Clone the Repository**

First, ensure Git LFS is activated. Then, clone the repository. This will automatically download the large dataset and model files tracked by LFS.

    git lfs install
    git clone https://github.com/Siew22/Sarawak-Agriculture-main.git
    cd Sarawak-Agriculture-main

### **2. Configure Environment Variables**

In the project's root directory, create a file named `.env`. Copy the content from `.env.example` (if it exists) or use the template below. **This is a critical step.**

    # .env file

    # --- Database Configuration ---
    # These are for the MySQL container inside Docker
    DB_HOST=db
    DB_PORT=3306
    DB_USER=root
    DB_PASSWORD="your_strong_secret_password"  # <-- IMPORTANT: Replace with your password
    DB_NAME="sarawak_agri_prod"

    # --- Backend Application Settings ---
    PROJECT_NAME="Sarawak Agri-Advisor"
    CONFIDENCE_THRESHOLD=0.75

    # --- External API Keys ---
    SERPAPI_KEY="" 
    NGROK_AUTHTOKEN="YOUR_NGROK_AUTHTOKEN" # <-- IMPORTANT: Get from https://dashboard.ngrok.com/get-started/your-authtoken

    # --- Email Configuration (for local debug server) ---
    SMTP_SERVER=mail
    SMTP_PORT=8025
    SENDER_EMAIL="noreply@sarawak-agri.dev"

    # --- CORS Settings (for development) ---
    ALLOWED_ORIGINS="https://sarawak-agriculture.vercel.app,https://*.vercel.app,http://localhost:8080,http://127.0.0.1:8080"

**Important:**
- Replace `your_strong_secret_password` with a secure password of your choice.
- Replace `YOUR_NGROK_AUTHTOKEN` with your actual token from your Ngrok dashboard.

### **3. Running the Application with Docker Compose (Recommended)**

This is the simplest and most reliable way to run the entire application stack.

1.  Make sure Docker Desktop is running.
2.  From the project root directory, run the following command:

        docker-compose up --build

3.  **Wait patiently.** The first time you run this, Docker will download all the necessary base images (Python, MySQL, Nginx, Redis) and build your application containers. This can take several minutes. The `db` service in particular may take a minute or two to initialize.
4.  Once all services are up and running (you will see logs from `backend`, `frontend`, `ngrok`, etc.), your application is live!

**Accessing the Services:**
-   **Frontend UI**: `http://localhost:8080`
-   **Backend API (via Ngrok)**: Look for the URL in the `ngrok` service logs (e.g., `https://juliette-unattempted-tammara.ngrok-free.dev`). This is the URL you should use for your Vercel frontend's API endpoint.
-   **Ngrok Inspector**: `http://localhost:4040` (to monitor API traffic)
-   **Database (via MySQL Workbench)**: Connect to `127.0.0.1` on port `3307` (not the standard 3306) with the user `root` and the password you set in the `.env` file.

### **4. (Optional) Training Your Own Models**

If you wish to retrain the AI models:
1.  **Image Classifier:**
    -   Organize your datasets in the appropriate folders.
    -   Run the training script inside a running Docker container to ensure the environment is correct:

            docker-compose exec backend python app/train/train_model_2.py

2.  **NLG Sentence Encoder:**
    -   Update the training data in `knowledge_base/nlg_training_data.json`.
    -   Run the training script:
    
            docker-compose exec backend python app/train/train_nlg_model.py
