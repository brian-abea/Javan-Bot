**Customer Support Chatbot

**Javan is an AI-powered chatbot designed to enhance customer service for a Watu Africa  by improving asset security, tracking efficiency, and responding to customer inquiries. 
The chatbot can be deployed on WhatsApp and a dedicated webpage, Watu App, and the company’s website providing 24/7 availability.

Tech Stack
NLP & Logic: Rasa
Frontend: React (custom UI with chat bubbles, auto-scroll, formatting)
Backend DB: PostgreSQL (asset info, phone verification)
Cloud Deployment: Google Cloud Run
CI/CD: GitHub Actions
Analytics: BigQuery + Looker Studio
Auth: OAuth 2.0 (for web users)
Messaging: Twilio (WhatsApp integration)

📌 Features
✅ Verifies users (customers & employees) via phone number
🔍 Allows asset lookup via plate number after verification
📲 Supports WhatsApp and web chat interface
🔒 Role-based access to sensitive data
📊 Logs conversations and sentiment to BigQuery
🔁 Supports rollback & A/B testing of model versions
📈 Dashboards with anomaly detection and predictive insights
🚨 Alerts for failed deployments and model underperformance


Chatbot Capabilities
Check asset status (online/offline, type, client)
Help with smartphone financing
Payment support
Locked phone issue resolution
Staff-specific queries and tools

Setup Guide
1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/your-org/chatbot-project.git
cd chatbot-project

3. Rasa Backend
bash
Copy
Edit
cd rasa-backend
pip install -r requirements.txt
rasa train
rasa run actions & rasa run

5. PostgreSQL Setup
Create tables:

sql
Copy
Edit
-- Users Table
CREATE TABLE users (
  phone VARCHAR PRIMARY KEY,
  name TEXT
);

-- Employees Table
CREATE TABLE employees (
  phone VARCHAR PRIMARY KEY,
  name TEXT
);

-- GPS Installations Table
CREATE TABLE gps_installations (
  plate_number VARCHAR PRIMARY KEY,
  asset_type TEXT,
  client_name TEXT,
  status TEXT
);

4. React Frontend
bash
Copy
Edit
cd react-frontend
npm install
npm start


Deployment
Cloud Run hosts the Rasa server and action server.
Frontend deployed via Firebase or Cloud Run.
CI/CD handles automated training, rollback, and alerts.


