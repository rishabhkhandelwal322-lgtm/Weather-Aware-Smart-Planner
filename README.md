# Weather-Aware Smart Planner

## Overview
Weather-Aware Smart Planner is a Python application that helps users plan their daily and weekly tasks around real-time and predicted weather conditions. It fetches live forecast data, intelligently reschedules weather-sensitive (outdoor) tasks, predicts good outdoor windows using a lightweight machine learning model, and visualizes productivity trends against weather patterns — all through an interactive Streamlit dashboard.

## Features
- **Live Weather Fetching** — Pulls current and 5-day forecasts via the OpenWeatherMap API, with response caching to reduce redundant calls.
- **Task Management (CRUD)** — Add, edit, complete, and delete tasks, each tagged as `outdoor` or `indoor` with priority and deadline.
- **Rule-Based Rescheduler** — Automatically flags or shifts outdoor tasks when rain, extreme heat, or high wind is forecast.
- **ML-Based Outdoor Window Prediction** — A trained scikit-learn model estimates the probability of a "good outdoor window" over the next few days, going beyond the raw forecast.
- **Notifications** — Email/desktop alerts when a task is rescheduled or a favorable window opens.
- **Analytics Dashboard** — Charts correlating task completion rates with weather conditions over time.
- **Interactive UI** — Streamlit-based dashboard with calendar, task list, forecast, and analytics views.

## Technologies / Tools Used
- **Language:** Python 3.10+
- **Web/API:** `requests` (OpenWeatherMap API)
- **Storage:** SQLite3
- **Machine Learning:** scikit-learn, pandas
- **Visualization:** matplotlib / plotly
- **UI:** Streamlit
- **Notifications:** smtplib / plyer
- **Testing:** pytest
- **Version Control:** Git & GitHub

## Project Structure
```
weather_planner/
├── main.py               # Entry point
├── dashboard.py           # Streamlit UI
├── weather_fetcher.py      # OpenWeatherMap API integration + caching
├── task_manager.py         # Task CRUD operations
├── planner.py              # Rule-based rescheduling engine
├── predictor.py            # ML model for outdoor window prediction
├── notifier.py              # Email/desktop notifications
├── analytics.py             # Productivity vs weather analytics
├── storage.py                # SQLite database layer
├── config.py                  # Configuration & API keys
├── models/
│   └── weather_model.pkl       # Trained ML model
├── data/
│   └── historical_weather.csv   # Training data for predictor
├── tests/
│   ├── test_planner.py
│   ├── test_predictor.py
│   └── test_task_manager.py
├── requirements.txt
├── README.md
└── statement.md
```

## Installation & Setup

1. Clone the repository
   ```bash
   git clone https://github.com/<your-username>/weather-planner.git
   cd weather-planner
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate    # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your API key
   Create a `.env` file in the project root:
   ```
   OPENWEATHER_API_KEY=your_api_key_here
   ```

5. Initialize the database
   ```bash
   python storage.py --init
   ```

6. Run the application
   ```bash
   streamlit run dashboard.py
   ```

## Testing
Run the full test suite with:
```bash
pytest tests/
```

## Screenshots
_(Add screenshots of the dashboard, task list, and analytics view here once the UI is built.)_

## License
This project was built as part of the VITyarthi "Build Your Own Project" coursework submission.
