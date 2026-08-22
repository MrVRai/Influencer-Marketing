# Influencer Marketing Engine 🚀

A comprehensive, modular AI-powered operating system for running a high-scale Influencer Marketing Agency.

---

## 📁 Repository Structure

```
Influencer-Marketing/
├── creator-discovery/          # 🔍 Creator Discovery, Sponsorship Intelligence & CRM
│   ├── core/                   # YouTube & Instagram API clients, Metrics & Sponsor Detectors
│   ├── utils/                  # CSV & formatted Excel exporters
│   ├── app.py                  # Streamlit Interactive Web Dashboard
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variables template
├── .gitignore                  # Protection for API keys & databases
└── README.md
```

---

## 🔍 Module 1: Creator Discovery & Sponsorship Scraper

Discover creators across **YouTube** and **Instagram**, compute performance metrics, detect past brand sponsors from descriptions/transcripts, and manage campaign rosters.

### Features
* **Multi-Platform Search**: Search by topic keyword or hashtag (`#skincare`, `#techreview`, `#fitness`) on YouTube and Instagram.
* **True Performance Metrics**:
  * **Median Views (Last 10–15 videos)** (filters out viral anomalies).
  * **Engagement Rate (ER)** ($\frac{\text{Likes} + \text{Comments}}{\text{Views}} \times 100$).
  * **View Consistency Score** (Coefficient of Variation).
  * **Composite Creator Score (0–100)**.
* **Automated Sponsorship Detection**:
  * Scans video descriptions, pinned comments, and auto-generated transcripts for sponsor phrases (*"Sponsored by"*, *"Thanks to..."*).
  * Extracts brand names, promo codes, and affiliate URLs (`bit.ly`, `amzn.to`).
  * Scans Instagram captions and sponsored hashtags (`#ad`, `#sponsored`, `#collab`).
* **Content Language Filter**: Auto-detects primary language across 24 supported languages (English, Hindi, Spanish, etc.).
* **Dynamic Rate & Margin Calculator**: Calculate estimated CPM placements and factor in agency margins.
* **Local CRM & Client-Ready Export**: SQLite database with instant CSV & styled Excel (`.xlsx`) export.

---

## 🚀 Getting Started

### 1. Clone & Navigate
```bash
git clone https://github.com/MrVRai/Influencer-Marketing.git
cd Influencer-Marketing/creator-discovery
```

### 2. Setup Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure API Keys (Optional)
Copy the example environment file:
```bash
cp .env.example .env
```
Add your credentials:
```ini
YOUTUBE_API_KEY=your_youtube_api_key_here
APIFY_API_TOKEN=your_apify_api_token_here
```
> **Note**: The tool includes an automatic zero-key fallback for YouTube so you can start discovering creators immediately even without API keys.

### 4. Launch the Dashboard
```bash
streamlit run app.py
```
Open **http://localhost:8501** in your browser.
