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

*Detailed setup instructions are provided in the original `README.md`. They cover cloning the repository with Git LFS, setting up the MySQL database, configuring the `.env` file, and running the application both locally and with Docker Compose.*
