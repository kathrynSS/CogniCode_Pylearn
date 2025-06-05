# 🐍 CogniCode: AI-Powered Python Learning Platform

[![Live Demo](https://img.shields.io/badge/Try%20it%20Now-Online-brightgreen?style=for-the-badge&logo=vercel)](https://capstone-six-alpha.vercel.app/)
[![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-000000?style=for-the-badge&logo=vercel)](https://capstone-six-alpha.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.2-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

> **A next-generation AI-powered platform for learning Python interactively — featuring a visual knowledge graph, an intelligent chatbot tutor, and a built-in online IDE. Level up your programming skills with a personalized and immersive experience.**

---

## 🚀 [Live Demo](https://capstone-six-alpha.vercel.app/)

Try out CogniCode instantly in your browser — no installation required.

## 📺 Demo Videos

### 🔹 Interactive Knowledge Graph

[![Watch the Knowledge Graph Demo](https://img.shields.io/badge/Watch%20Video-Interactive%20Graph-blue?style=for-the-badge&logo=google-drive)](https://drive.google.com/file/d/1l8lButc8GJyCbne9X8xSi9-2c6WdTJhx/view?usp=sharing)
  
*Explore how the visual knowledge graph works in CogniCode.*

---

### 🔹 AI Chatbot Learning Assistant

[![Watch the Chatbot Demo](https://img.shields.io/badge/Watch%20Video-Chatbot%20Assistant-green?style=for-the-badge&logo=google-drive)](https://drive.google.com/file/d/1uQW-4hvsNbHJRXz2x8EKiqW)

---

## ✨ Key Features

### 🌐 Interactive Knowledge Graph
- **Visualized Learning Path:** Dynamic, beautiful D3.js graph displays Python concepts and their relationships.
- **Smart Navigation:** Click on any concept to focus, expand, and see contextually related topics.
- **Instant Highlights:** Real-time highlighting of relevant nodes and connections as you explore.
- **Concise Explanations:** Every node comes with a brief, clear explanation.

### 🤖 AI Learning Assistant
- **Multi-turn Conversation:** Maintain learning context in ongoing chat with the AI tutor.
- **Personalized Learning Modes:** Choose from different teaching styles to fit your needs.
- **Layered Answers:** Get concise answers first, then dive deeper if you wish.
- **Intelligent Code Analysis:** Automatic code review and suggestions for improvement.

### 🎯 Project-Based Learning
- **AI Task Breakdown:** The AI decomposes project descriptions into actionable learning steps.
- **Step-by-Step Guidance:** Each task step comes with detailed instructions and links to related knowledge.
- **Progress Tracking:** Visualize your learning progress and completion status in real time.
- **Theory & Practice:** Instantly connect practical tasks to relevant theory in the knowledge graph.

### 💻 Online IDE
- **Write & Run Code:** Edit and execute Python code directly in your browser.
- **Error Diagnosis:** Get smart error messages and AI-powered fix suggestions.
- **Line-by-Line Explanation:** Ask the AI for code walkthroughs.
- **Instant Feedback:** See results and errors immediately.

### 📚 Resource & Note Management
- **Upload/Download Materials:** Supports multiple formats (PDF, DOC, TXT, etc.).
- **Open Sharing:** Share resources with the community or keep them private.
- **Personal Notes:** Take notes, organize them, and sync across devices.
- **Cloud Sync:** Google Drive integration for seamless backup and access.

### 🔐 User System
- **Secure Authentication:** Register and log in with JWT-based security.
- **Personal Workspace:** All your learning data and progress in one place.
- **Privacy Controls:** Full export and privacy options for your data.

---

## 🏗️ Tech Stack & Project Structure

### Project Structure

```text
capstone/
├── app.py                     # Main Flask app entry point
├── api/                       # Vercel API routes
│   └── index.py
├── models_neon.py             # Neon PostgreSQL models
├── auth_middleware.py         # User authentication middleware
├── prompt.py                  # AI prompt configuration
├── google_drive_service.py    # Google Drive integration
├── templates/                 # Frontend HTML pages
│   ├── index.html
│   ├── graph.html
│   ├── learning_chatbot.html
│   ├── auth.html
├── static/
│   ├── styles.css
│   ├── script.js
│   ├── notes_fix_complete.js
│   └── upload_fix.js
├── Resources/                 # Uploaded user files
├── vercel.json                # Vercel deployment config
├── requirements.txt           # Python dependencies
└── .vercelignore              # Files to ignore during deployment
```


### Core Stack

- **Backend:** Flask 2.3.2, Neon PostgreSQL, OpenAI SDK, Google Drive API, JWT
- **Frontend:** D3.js v7, Vanilla JavaScript, CSS Grid/Flexbox, Font Awesome
- **Deployment:** Vercel (Serverless), Neon (Cloud DB), Google Drive

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.8+
- Flask 2.3.2+

### Local Setup

1. **Clone the repository**
    ```bash
    git clone git@github.com:kathrynSS/CogniCode.git
    cd capstone
    ```

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set environment variables**
    ```bash
    # Create .env file
    echo "DEEPSEEK_API_KEY=your-deepseek-api-key-here" > .env
    echo "GOOGLE_DRIVE_CREDENTIALS_PATH=path/to/credentials.json" >> .env
    ```

4. **Run the app**
    ```bash
    python app.py
    ```

5. **Open in browser**
    ```
    http://localhost:5000
    ```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Join the Community

- Open to issues, discussions, and pull requests — your feedback and contributions are highly appreciated!
- **If you find this project helpful, please give us a ⭐ Star — it motivates us to keep improving!**

<div align="center">

[👉 Try CogniCode Online!](https://capstone-six-alpha.vercel.app/)


