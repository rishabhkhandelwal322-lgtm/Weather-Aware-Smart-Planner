"""
build_report.py
-----------------
Generates the full VITyarthi project report PDF for the
Weather-Aware Smart Planner, combining all 15 required sections
with the design diagrams and analytics charts already generated.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle,
    ListFlowable, ListItem, KeepTogether
)

DIAG = "/home/claude/weather_planner/diagrams"
CHARTS = "/home/claude/weather_planner/reports"
OUT = "/home/claude/weather_planner/Weather_Aware_Smart_Planner_Report.pdf"

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(name="CoverTitle", fontSize=26, leading=32, alignment=TA_CENTER,
                           spaceAfter=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#2C3E50")))
styles.add(ParagraphStyle(name="CoverSub", fontSize=14, leading=20, alignment=TA_CENTER,
                           spaceAfter=8, textColor=colors.HexColor("#4A6FA5")))
styles.add(ParagraphStyle(name="CoverMeta", fontSize=11, leading=16, alignment=TA_CENTER,
                           spaceAfter=4))
styles.add(ParagraphStyle(name="SectionHeading", fontSize=16, leading=20, spaceBefore=6,
                           spaceAfter=10, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#2C3E50"),
                           borderWidth=0, borderColor=colors.HexColor("#4A6FA5")))
styles.add(ParagraphStyle(name="SubHeading", fontSize=12.5, leading=16, spaceBefore=10,
                           spaceAfter=6, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#4A6FA5")))
styles.add(ParagraphStyle(name="BodyJustify", fontSize=10.2, leading=15, alignment=TA_JUSTIFY,
                           spaceAfter=8))
styles.add(ParagraphStyle(name="Caption", fontSize=8.5, leading=11, alignment=TA_CENTER,
                           textColor=colors.HexColor("#555555"), spaceAfter=14, spaceBefore=4,
                           fontName="Helvetica-Oblique"))
styles.add(ParagraphStyle(name="CodeBlock", fontSize=8, leading=11, fontName="Courier",
                           backColor=colors.HexColor("#F4F4F4"), borderPadding=6, spaceAfter=8))

styles.add(ParagraphStyle(name="TableCell", fontSize=8.3, leading=11, fontName="Helvetica"))
styles.add(ParagraphStyle(name="TableHeader", fontSize=8.7, leading=11, fontName="Helvetica-Bold",
                           textColor=colors.white))

story = []

# ============================================================ COVER PAGE ====
story.append(Spacer(1, 4*cm))
story.append(Paragraph("Weather-Aware Smart Planner", styles["CoverTitle"]))
story.append(Paragraph("A Python-Based Task Scheduling System with Weather Forecast Integration and Machine Learning", styles["CoverSub"]))
story.append(Spacer(1, 2*cm))
story.append(Paragraph("VITyarthi — Build Your Own Project", styles["CoverMeta"]))
story.append(Paragraph("Project Report", styles["CoverMeta"]))
story.append(Spacer(1, 2*cm))
story.append(Paragraph("Submitted by: Rishabh Khandelwal", styles["CoverMeta"]))
story.append(Paragraph("Program: B.Tech, Computer Science Engineering (AI/ML Specialization)", styles["CoverMeta"]))
story.append(Paragraph("GitHub Repository: github.com/rishabhkhandelwal322-lgtm/Weather-Aware-Smart-Planner", styles["CoverMeta"]))
story.append(PageBreak())

# ============================================================ 2. INTRODUCTION ====
story.append(Paragraph("2. Introduction", styles["SectionHeading"]))
story.append(Paragraph(
    "The Weather-Aware Smart Planner is a Python application designed to help individuals manage "
    "their daily tasks in a way that accounts for real-world weather conditions. Traditional to-do "
    "list and calendar applications treat time as the only planning variable, which frequently leads "
    "to disrupted schedules when outdoor-dependent tasks are planned on days with unfavorable weather. "
    "This project addresses that gap by combining live weather forecast data, a rule-based rescheduling "
    "engine, a machine learning prediction layer, and a productivity analytics dashboard into a single, "
    "cohesive system.",
    styles["BodyJustify"]))
story.append(Paragraph(
    "The system is built entirely in Python, using SQLite for persistent storage, the OpenWeatherMap "
    "API for live weather data, scikit-learn for a probabilistic prediction model, and Streamlit for an "
    "interactive front-end dashboard. The project demonstrates the practical application of core "
    "programming concepts — API integration, relational data modeling, rule-based automation, machine "
    "learning, and user interface design — within a single, functioning application.",
    styles["BodyJustify"]))

# ============================================================ 3. PROBLEM STATEMENT ====
story.append(Paragraph("3. Problem Statement", styles["SectionHeading"]))
story.append(Paragraph(
    "People frequently plan outdoor tasks — errands, workouts, commutes, events — without factoring in "
    "short-term weather changes, leading to disrupted schedules, wasted time, and missed opportunities "
    "to take advantage of favorable weather windows. Existing calendar and to-do applications treat time "
    "as the only planning variable and ignore environmental conditions entirely. There is a clear need "
    "for a planning tool that actively incorporates weather forecasts and trends into task scheduling "
    "decisions, rather than leaving that correlation entirely to the user's manual judgment.",
    styles["BodyJustify"]))
story.append(Paragraph(
    "This project is scoped as a single-user, local desktop/web application (delivered via Streamlit) "
    "and does not include multi-user accounts, native mobile apps, or integration with third-party "
    "calendar services in this iteration. The target users are students and individuals who plan "
    "outdoor-dependent tasks and want a lightweight, automated assistant that reduces the manual effort "
    "of checking forecasts and rescheduling tasks by hand.",
    styles["BodyJustify"]))

# ============================================================ 4. FUNCTIONAL REQUIREMENTS ====
story.append(Paragraph("4. Functional Requirements", styles["SectionHeading"]))
func_reqs = [
    ("Task Management (CRUD)", "Users can create, view, filter, update, complete, and delete tasks. "
     "Each task is tagged as 'outdoor' or 'indoor', with a priority level, an optional deadline, and a "
     "scheduled date."),
    ("Live Weather Forecast Retrieval", "The system fetches current conditions and a 5-day/3-hour "
     "forecast from the OpenWeatherMap API, aggregates the 3-hour blocks into daily summaries, and "
     "caches them locally to minimize redundant API calls."),
    ("Manual Forecast Entry", "Users can manually insert or overwrite forecast data for a given date and "
     "location without depending on the live API — useful for testing, offline use, or covering gaps in "
     "the 5-day API window."),
    ("Rule-Based Rescheduling Engine", "Outdoor tasks scheduled on a day with a rain probability above a "
     "defined threshold are automatically identified and moved to the next available day within the "
     "forecast window that meets the favorable-weather criteria."),
    ("ML-Based Outdoor Window Prediction", "A trained scikit-learn classification model estimates the "
     "probability (0–100%) that a given day is favorable for outdoor activity, based on temperature, "
     "rain probability, wind speed, and seasonal month — providing a smoother, more nuanced signal than "
     "the rule-based threshold alone."),
    ("Notifications", "The system sends desktop notifications (via plyer) and, when configured, email "
     "notifications (via SMTP) whenever a task is automatically rescheduled or cannot be rescheduled "
     "within the forecast window."),
    ("Productivity Analytics", "The system computes and visualizes task completion rates overall, by "
     "task type (outdoor vs indoor), and correlated against weather conditions (rainy vs clear days), "
     "producing chart images for reporting."),
    ("Interactive Dashboard", "A Streamlit-based web dashboard ties all the above together into a single "
     "interface with dedicated tabs for tasks, forecast, analytics, and activity history."),
]
for title, desc in func_reqs:
    story.append(Paragraph(f"<b>{title}:</b> {desc}", styles["BodyJustify"]))

# ============================================================ 5. NON-FUNCTIONAL REQUIREMENTS ====
story.append(Paragraph("5. Non-Functional Requirements", styles["SectionHeading"]))
nf_table_data = [
    ["Requirement", "How It Is Addressed"],
    ["Performance", "Forecast data is cached in SQLite (one row per location/date) so repeated planning "
     "cycles within the same day do not re-hit the external API."],
    ["Reliability", "All task and forecast data is persisted in a local SQLite database (planner.db), "
     "surviving application restarts. Every state-changing operation is wrapped in a transactional "
     "connection context manager with rollback on failure."],
    ["Security", "API keys and SMTP credentials are stored in a local .env file, loaded via "
     "python-dotenv, and excluded from version control via .gitignore — never hardcoded in source."],
    ["Usability", "The Streamlit dashboard provides a clear, tabbed interface requiring no configuration "
     "to view tasks; sensible defaults (medium priority, current date) reduce data-entry friction."],
    ["Scalability", "The modular design (separate storage, fetcher, planner, predictor, notifier, and "
     "analytics modules) allows additional locations, users, or forecast sources to be added without "
     "restructuring the core system."],
    ["Maintainability", "Each module has a single, well-defined responsibility with docstrings and type-"
     "consistent function signatures; the test suite (tests/) validates core planner and task-manager "
     "behavior independently."],
    ["Error Handling", "Custom exception classes (WeatherFetchError, ValidationError, NotificationError) "
     "are raised for expected failure modes and caught at the UI/CLI boundary, so a missing API key or "
     "invalid input never crashes the application outright."],
]
nf_table_data = [
    [Paragraph(f"<b>{row[0]}</b>", styles["TableCell"]) if i > 0 else Paragraph(f"<b>{row[0]}</b>", styles["TableHeader"]),
     Paragraph(row[1], styles["TableCell"]) if i > 0 else Paragraph(f"<b>{row[1]}</b>", styles["TableHeader"])]
    for i, row in enumerate(nf_table_data)
]
nf_table = Table(nf_table_data, colWidths=[3.3*cm, 12.7*cm])
nf_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2C3E50")),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F5F8FC")]),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(nf_table)
story.append(PageBreak())

# ============================================================ 6. SYSTEM ARCHITECTURE ====
story.append(Paragraph("6. System Architecture", styles["SectionHeading"]))
story.append(Paragraph(
    "The system follows a layered architecture. A presentation layer (the Streamlit dashboard, plus a "
    "CLI entry point via task_manager.py) sits above an application logic layer containing the task "
    "manager, planner engine, ML predictor, and analytics modules. These depend on two support services "
    "— the weather fetcher and the notifier — which in turn depend on a single data layer (storage.py) "
    "backed by a local SQLite database. External dependencies are limited to the OpenWeatherMap API and "
    "the operating system's notification/SMTP facilities.",
    styles["BodyJustify"]))
story.append(Image(f"{DIAG}/architecture.png", width=16.5*cm, height=16.5*cm*(7.5/11)))
story.append(Paragraph("Figure 6.1 — System Architecture Diagram", styles["Caption"]))
story.append(PageBreak())

# ============================================================ 7. DESIGN DIAGRAMS ====
story.append(Paragraph("7. Design Diagrams", styles["SectionHeading"]))

story.append(Paragraph("7.1 Use Case Diagram", styles["SubHeading"]))
story.append(Paragraph(
    "The single actor (User) interacts with eleven use cases spanning task management, forecast "
    "handling, planning automation, notifications, and analytics.", styles["BodyJustify"]))
story.append(Image(f"{DIAG}/use_case.png", width=15.5*cm, height=15.5*cm*(8/10)))
story.append(Paragraph("Figure 7.1 — Use Case Diagram", styles["Caption"]))
story.append(PageBreak())

story.append(Paragraph("7.2 Workflow / Process Flow Diagram", styles["SubHeading"]))
story.append(Paragraph(
    "This diagram illustrates the core rescheduling logic executed each time a planning cycle runs: "
    "each outdoor task's scheduled date is checked against the cached forecast, and tasks landing on a "
    "high-rain-probability day are automatically moved to the next available favorable day, with a "
    "notification sent on success and an unresolved flag raised if no suitable day exists in the window.",
    styles["BodyJustify"]))
story.append(Image(f"{DIAG}/workflow.png", width=13*cm, height=13*cm*(11.5/9.5)))
story.append(Paragraph("Figure 7.2 — Planner Rescheduling Workflow", styles["Caption"]))
story.append(PageBreak())

story.append(Paragraph("7.3 Sequence Diagram", styles["SubHeading"]))
story.append(Paragraph(
    "The sequence diagram below traces a single 'Run Planning Cycle' interaction from the user clicking "
    "the button in the dashboard through to the forecast fetch (with cache check), task evaluation, "
    "rescheduling, and notification dispatch.", styles["BodyJustify"]))
story.append(Image(f"{DIAG}/sequence.png", width=16.5*cm, height=16.5*cm*(10.6/12)))
story.append(Paragraph("Figure 7.3 — Sequence Diagram: Run Planning Cycle", styles["Caption"]))
story.append(PageBreak())

story.append(Paragraph("7.4 Class / Component Diagram", styles["SubHeading"]))
story.append(Paragraph(
    "Each Python module is represented as a UML-style class box showing its key attributes and public "
    "functions, with dependency arrows showing which modules the dashboard orchestrates and how data "
    "flows down to the shared storage layer.", styles["BodyJustify"]))
story.append(Image(f"{DIAG}/class_diagram.png", width=16.5*cm, height=16.5*cm*(9/13)))
story.append(Paragraph("Figure 7.4 — Class / Component Diagram", styles["Caption"]))
story.append(PageBreak())

story.append(Paragraph("7.5 ER Diagram / Database Schema", styles["SubHeading"]))
story.append(Paragraph(
    "The SQLite database consists of three tables: tasks, forecasts, and logs. The logs table has a "
    "formal foreign-key relationship to tasks (one task generates zero or more log entries). The "
    "forecasts table has no formal foreign key to tasks; instead, the planner joins them logically at "
    "the application level by matching a task's scheduled_date against a forecast's (location, "
    "forecast_date) pair.", styles["BodyJustify"]))
story.append(Image(f"{DIAG}/er_diagram.png", width=16.5*cm, height=16.5*cm*(7/11)))
story.append(Paragraph("Figure 7.5 — Entity-Relationship Diagram", styles["Caption"]))
story.append(PageBreak())

# ============================================================ 8. DESIGN DECISIONS ====
story.append(Paragraph("8. Design Decisions & Rationale", styles["SectionHeading"]))
decisions = [
    ("SQLite over a JSON file or a full DBMS", "SQLite provides real relational structure (enabling the "
     "tasks–logs foreign key and SQL-based filtering/aggregation for analytics) without requiring a "
     "separate database server, keeping the project fully self-contained and easy to run for evaluation."),
    ("Rule-based rescheduling and ML prediction, in combination", "The planner's rule-based threshold "
     "(rain probability > 0.5) is deterministic, auditable, and simple to explain and test. The ML "
     "predictor was added on top as a complementary, probabilistic signal (0-100% confidence) that "
     "learns smoother decision boundaries across temperature, wind, and seasonality — offering a richer "
     "signal in the dashboard without replacing the transparent rule that actually drives rescheduling."),
    ("Synthetic training data for the ML model", "No multi-year historical weather log was available for "
     "this project's target location. A synthetic dataset was generated with realistic seasonal "
     "temperature curves, monsoon-aware rain probability distributions, and deliberate label noise (7%) "
     "so the model learns generalizable patterns rather than memorizing a hand-written rule."),
    ("Caching forecast data rather than fetching on every call", "The OpenWeatherMap free tier has "
     "request-rate constraints, and repeated calls within the same day would be wasteful. Caching by "
     "(location, date) in the forecasts table means a full planning cycle costs at most one API call "
     "per uncached day."),
    ("Streamlit for the dashboard instead of Tkinter or Flask", "Streamlit allows a full interactive "
     "multi-tab web UI to be built directly in Python with minimal boilerplate, making it well suited to "
     "a project of this scope compared to hand-writing HTML/CSS/JS for Flask or building a native "
     "Tkinter GUI."),
    ("Graceful degradation for optional features", "Desktop and email notifications, and the ML "
     "predictor, are all designed to fail silently (returning a status rather than raising) when not "
     "configured or not yet trained, so the core task-and-planner functionality never depends on them "
     "being present."),
]
for title, desc in decisions:
    story.append(Paragraph(f"<b>{title}:</b> {desc}", styles["BodyJustify"]))

# ============================================================ 9. IMPLEMENTATION DETAILS ====
story.append(Paragraph("9. Implementation Details", styles["SectionHeading"]))
story.append(Paragraph(
    "The project is implemented as nine Python modules plus a Streamlit dashboard, totaling roughly "
    "1,600 lines of application code excluding tests and generated assets.", styles["BodyJustify"]))

impl_table_data = [
    ["Module", "Responsibility", "Key Libraries"],
    ["storage.py", "SQLite schema, connection management, CRUD for tasks/forecasts/logs", "sqlite3"],
    ["weather_fetcher.py", "Live API fetch + aggregation, caching, manual forecast entry", "requests, python-dotenv"],
    ["planner.py", "Rule-based rescheduling engine, good-window lookup", "storage, weather_fetcher"],
    ["predictor.py", "Synthetic data generation, model training, probability prediction", "scikit-learn, pandas, joblib"],
    ["task_manager.py", "Input validation, task CRUD wrapper, CLI interface", "argparse"],
    ["notifier.py", "Desktop and email notifications with graceful fallback", "plyer, smtplib"],
    ["analytics.py", "Completion-rate stats, weather correlation, chart generation", "matplotlib"],
    ["dashboard.py", "Streamlit UI tying every module together", "streamlit"],
]
impl_table_data = [
    [Paragraph(f"<b>{row[0]}</b>", styles["TableCell"]) if i > 0 else Paragraph(f"<b>{row[0]}</b>", styles["TableHeader"]),
     Paragraph(row[1], styles["TableCell"]) if i > 0 else Paragraph(f"<b>{row[1]}</b>", styles["TableHeader"]),
     Paragraph(row[2], styles["TableCell"]) if i > 0 else Paragraph(f"<b>{row[2]}</b>", styles["TableHeader"])]
    for i, row in enumerate(impl_table_data)
]
impl_table = Table(impl_table_data, colWidths=[3.6*cm, 8.6*cm, 3.8*cm])
impl_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2C3E50")),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F5F8FC")]),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(impl_table)
story.append(Spacer(1, 12))

story.append(Paragraph("Example: the core rescheduling logic (planner.py)", styles["SubHeading"]))
code_snippet = """def run_planning_cycle(location):
    forecast_days = weather_fetcher.get_5day_forecast(location)
    forecast_by_date = {f["forecast_date"]: f for f in forecast_days}
    outdoor_tasks = storage.get_tasks(status="pending", task_type="outdoor")

    for task in outdoor_tasks:
        forecast = forecast_by_date.get(task["scheduled_date"])
        if not _is_bad_weather_day(forecast):
            continue  # already on a good day
        new_date = _find_next_good_day(forecast_by_date, after_date=task["scheduled_date"])
        if new_date:
            storage.reschedule_task(task["id"], new_date, reason="...")"""
story.append(Paragraph(code_snippet.replace("\n", "<br/>").replace(" ", "&nbsp;"), styles["CodeBlock"]))
story.append(PageBreak())

# ============================================================ 10. SCREENSHOTS / RESULTS ====
story.append(Paragraph("10. Screenshots / Results", styles["SectionHeading"]))
story.append(Paragraph(
    "The following charts are generated by analytics.py from sample task and forecast data, "
    "demonstrating the system's ability to correlate task completion outcomes with weather conditions.",
    styles["BodyJustify"]))
story.append(Image(f"{CHARTS}/weather_correlation.png", width=13*cm, height=13*cm*(4/6)))
story.append(Paragraph("Figure 10.1 — Outdoor Task Completion Rate vs Weather Condition. Clear-day "
                        "completion (83%) substantially exceeds rainy-day completion (33%), demonstrating "
                        "the real-world value of weather-aware rescheduling.", styles["Caption"]))
story.append(Image(f"{CHARTS}/completion_by_type.png", width=13*cm, height=13*cm*(4/6)))
story.append(Paragraph("Figure 10.2 — Task Completion Rate: Outdoor vs Indoor Tasks", styles["Caption"]))
story.append(Image(f"{CHARTS}/status_breakdown.png", width=10*cm, height=10*cm))
story.append(Paragraph("Figure 10.3 — Overall Task Status Breakdown", styles["Caption"]))
story.append(PageBreak())

# ============================================================ 11. TESTING APPROACH ====
story.append(Paragraph("11. Testing Approach", styles["SectionHeading"]))
story.append(Paragraph(
    "Testing combined automated unit tests (in the tests/ directory, run via pytest) with manual "
    "end-to-end verification of each module as it was built:", styles["BodyJustify"]))
testing_items = [
    "storage.py was verified by creating a task, rescheduling it, caching a forecast, and confirming "
    "all fields round-tripped correctly through the database, including the activity log.",
    "weather_fetcher.py's aggregation logic was tested against a mocked OpenWeatherMap response "
    "containing mixed clear/rainy 3-hour blocks, verifying the daily rollup correctly took the maximum "
    "rain probability and wind speed, and the most frequent condition label.",
    "planner.py was tested end-to-end with a mocked forecast containing one rainy day followed by clear "
    "days, confirming a task scheduled on the rainy day was correctly moved to the next clear day and "
    "logged.",
    "predictor.py's trained model was validated with an 80/20 train-test split, achieving 93.8% test "
    "accuracy and a 0.933 ROC-AUC score, then sanity-checked with manually chosen extreme cases (e.g. "
    "a calm clear day scoring 91.3% favorable vs a heavy-rain day scoring 3.6%).",
    "task_manager.py's CLI and validation layer were tested with both valid inputs and deliberately "
    "invalid ones (empty title, non-existent task ID) to confirm errors are reported cleanly without "
    "crashing.",
    "notifier.py was tested with no SMTP/desktop configuration present, confirming it reports failure "
    "status without raising an exception that would interrupt a planning cycle.",
    "analytics.py and dashboard.py were verified by seeding a realistic sample dataset (seed_demo_data.py) "
    "and confirming the computed statistics matched the seeded data exactly, and that the Streamlit app "
    "served without runtime errors across all four tabs.",
]
story.append(ListFlowable(
    [ListItem(Paragraph(item, styles["BodyJustify"]), leftIndent=12) for item in testing_items],
    bulletType="bullet"))

# ============================================================ 12. CHALLENGES FACED ====
story.append(Paragraph("12. Challenges Faced", styles["SectionHeading"]))
challenges = [
    ("Aggregating 3-hour forecast blocks into daily summaries", "The OpenWeatherMap free tier only "
     "provides 3-hour resolution data, not true daily summaries. This required writing custom "
     "aggregation logic (worst-case rain probability, maximum wind, average temperature, most frequent "
     "condition) to produce a meaningful single value per day."),
    ("Avoiding an unrealistically perfect ML model", "An early version of the synthetic training data "
     "produced a model with near-100% accuracy because the label was a deterministic function of the "
     "features. Deliberate label noise (7%) was introduced to force the model to learn a genuinely "
     "probabilistic, generalizable decision boundary instead of memorizing the rule."),
    ("Windows-specific tooling friction", "Setting up the local development environment involved several "
     "Windows-specific obstacles: PowerShell here-string parsing issues when creating .gitignore, PATH "
     "not including the pip user-script directory (breaking direct `streamlit`/`pytest` commands until "
     "invoked via `python -m`), and Git line-ending (LF/CRLF) warnings."),
    ("Git repository history conflicts", "An initial mismatch between the local repository history and "
     "GitHub's auto-generated default file required resolving a merge conflict on README.md using "
     "`git pull --allow-unrelated-histories` before the first push would succeed."),
]
for title, desc in challenges:
    story.append(Paragraph(f"<b>{title}:</b> {desc}", styles["BodyJustify"]))

story.append(PageBreak())

# ============================================================ 13. LEARNINGS ====
story.append(Paragraph("13. Learnings & Key Takeaways", styles["SectionHeading"]))
learnings = [
    "Designing a clean separation between a rule-based system and a machine learning layer clarified "
    "when each approach is appropriate: rules for deterministic, explainable decisions; ML for a "
    "smoother, probabilistic signal layered on top.",
    "Caching strategy matters even in small projects — without it, a free-tier API's rate limits would "
    "make repeated testing impractical.",
    "Synthetic data generation requires deliberate imperfection (label noise, realistic variance) to "
    "produce a model that behaves like a real-world predictor rather than an overfit lookup table.",
    "Building a project incrementally, module by module, with a working test at each stage (storage, "
    "then fetcher, then planner, then the UI) made integration far less error-prone than writing "
    "everything and testing only at the end.",
    "Version control workflows have real friction points beyond just 'git add, commit, push' — merge "
    "conflicts, cross-platform line endings, and PATH configuration are practical skills as important as "
    "the application code itself.",
]
story.append(ListFlowable(
    [ListItem(Paragraph(item, styles["BodyJustify"]), leftIndent=12) for item in learnings],
    bulletType="bullet"))

# ============================================================ 14. FUTURE ENHANCEMENTS ====
story.append(Paragraph("14. Future Enhancements", styles["SectionHeading"]))
future = [
    "Multi-user support with authentication, allowing the planner to be deployed as a shared service.",
    "Integration with real historical weather archives (e.g. Open-Meteo's historical API) to replace "
    "the synthetic training dataset with genuine location-specific climate patterns.",
    "Two-way sync with external calendars (Google Calendar) so rescheduled tasks update automatically "
    "outside the app.",
    "A mobile-friendly companion view or push notifications instead of desktop-only alerts.",
    "Expanding the rescheduling rule set beyond rain probability to jointly weigh temperature extremes, "
    "wind, and air quality.",
]
story.append(ListFlowable(
    [ListItem(Paragraph(item, styles["BodyJustify"]), leftIndent=12) for item in future],
    bulletType="bullet"))

# ============================================================ 15. REFERENCES ====
story.append(Paragraph("15. References", styles["SectionHeading"]))
references = [
    "OpenWeatherMap API Documentation — https://openweathermap.org/api",
    "Streamlit Documentation — https://docs.streamlit.io",
    "scikit-learn Documentation — https://scikit-learn.org/stable/documentation.html",
    "Python sqlite3 Documentation — https://docs.python.org/3/library/sqlite3.html",
    "ReportLab User Guide — https://www.reportlab.com/docs/reportlab-userguide.pdf",
    "matplotlib Documentation — https://matplotlib.org/stable/",
]
story.append(ListFlowable(
    [ListItem(Paragraph(item, styles["BodyJustify"]), leftIndent=12) for item in references],
    bulletType="bullet"))

# ============================================================ BUILD ====
doc = SimpleDocTemplate(OUT, pagesize=A4,
                         topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm,
                         title="Weather-Aware Smart Planner - Project Report",
                         author="Rishabh Khandelwal")
doc.build(story)
print(f"Report built: {OUT}")
