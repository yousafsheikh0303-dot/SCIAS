# 🌾 SCIAS - Smart Crop Irrigation Advisory System

> An AI-powered agricultural advisory platform that empowers farmers with intelligent recommendations for crop health, irrigation, weather, market prices, and yield prediction through voice and text interactions.

---

## 📖 Overview

SCIAS (Smart Crop Irrigation Advisory System) is an intelligent multi-agent platform designed to support farmers in making data-driven agricultural decisions.

The system provides personalized recommendations using Artificial Intelligence, Retrieval-Augmented Generation (RAG), speech processing, and multilingual support, making agricultural knowledge more accessible.

---

## ✨ Features

- 🌦 Real-time Weather Advisory
- 🌱 Crop Disease Detection & Recommendations
- 💧 Smart Irrigation Guidance
- 📈 Market Price Information
- 🌾 Crop Yield Prediction
- 📚 AI Knowledge Base using RAG
- 🎤 Speech-to-Text (Voice Input)
- 🔊 Text-to-Speech (Voice Response)
- 🌍 Multilingual Support
  - English
  - Urdu
  - Punjabi
- 💬 Natural Language Interaction
- 🖥 Modern Streamlit Interface

---

# 🏗 System Architecture

```
                User
                  │
        Voice / Text Query
                  │
        Speech-to-Text (Optional)
                  │
          Translation Agent
                  │
         Query Orchestrator
                  │
     ┌────────────┼─────────────┐
     │            │             │
 Weather     Disease      Irrigation
     │            │             │
 Market     Yield Prediction   RAG
     │            │             │
     └────────────┼─────────────┘
                  │
      Text-to-Speech (Optional)
                  │
             Final Response
```

---

# 🧠 AI Modules

- Weather Agent
- Disease Detection Agent
- Irrigation Agent
- Yield Prediction Agent
- Market Price Agent
- Translation Agent
- Speech-to-Text Agent
- Text-to-Speech Agent
- RAG Knowledge Base

---

# 🛠 Tech Stack

## Programming

- Python

## AI & Machine Learning

- LangGraph
- Groq LLaMA
- Hugging Face Embeddings
- ChromaDB

## Frontend

- Streamlit

## Database

- SQLite

## Speech Processing

- Vosk
- gTTS

## Data Processing

- Pandas
- NumPy

---

# 📂 Project Structure

```
SCIAS/
│
├── agents/
│
├── frontend/
│   ├── pages/
│   ├── streamlit_app.py
│   └── ui_theme.py
│
├── data/
│
├── db/
│
├── models/
│
├── orchestrator.py
├── serve_disease_model.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/yousafsheikh0303-dot/SCIAS.git
```

Move into the project folder

```bash
cd SCIAS
```

Create virtual environment

```bash
python -m venv .venv
```

Activate environment

### Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
streamlit run frontend/streamlit_app.py
```

---

# 🎯 Use Cases

- Farmers
- Agriculture Students
- Researchers
- Agricultural Consultants
- Smart Farming Projects
- AI in Agriculture Demonstrations

---

# 🌍 Future Improvements

- Mobile Application
- Satellite Image Analysis
- IoT Sensor Integration
- Fertilizer Recommendation System
- Pest Detection using Computer Vision
- Crop Calendar Planning
- Offline Voice Assistant
- Farmer Dashboard & Analytics

---

# 📸 Screenshots

## 🔐 Login Page

![Login Page](screenshots/login.png)

---

## 🏠 Home Page

![Home Page](screenshots/home.png)

---

## 🌦 Weather Advisory

![Weather Advisory](screenshots/weather.png)

---

## 🌱 Disease Detection

![Disease Detection](screenshots/disease.png)

---

## 💧 Irrigation Recommendation

![Irrigation Recommendation](screenshots/irrigation.png)

---

## 📈 Market Prices

![Market Prices](screenshots/market.png)

---

## 📚 Knowledge Base

![Knowledge Base](screenshots/knowledge.png)

---

## 🌾 Yield Prediction

![Yield Prediction](screenshots/yield.png)

# 👨‍💻 Author

## Muhammad Yousaf

Computer Science Student

AI | Generative AI | Machine Learning | Python | Streamlit | LangGraph | RAG

GitHub:
https://github.com/yousafsheikh0303-dot

LinkedIn:
www.linkedin.com/in/muhammad-yousaf-819a362a0

---

## ⭐ Support

If you found this project helpful, please consider giving it a ⭐ on GitHub.
