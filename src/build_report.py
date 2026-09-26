"""
build_report.py
Script to generate the final PDF report for the Weather-Aware Smart Planner project.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle,
    ListFlowable, ListItem
)

# Resolve project paths
root_dir = Path(__file__).resolve().parent.parent
diag_path = root_dir / "diagrams"
charts_path = root_dir / "reports"
out_pdf = root_dir / "Weather_Aware_Smart_Planner_Report.pdf"

# Initialize custom styles
styles = getSampleStyleSheet()

styles.add(ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Helvetica-Bold',
                          fontSize=26, leading=32, alignment=TA_CENTER, spaceAfter=14,
                          textColor=colors.HexColor('#2C3E50')))

styles.add(ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=14, leading=20,
                          alignment=TA_CENTER, spaceAfter=8, textColor=colors.HexColor('#4A6FA5')))

styles.add(ParagraphStyle('CoverMeta', parent=styles['Normal'], fontSize=11, leading=16,
                          alignment=TA_CENTER, spaceAfter=4))

styles.add(ParagraphStyle('SectionHeading', parent=styles['Normal'], fontName='Helvetica-Bold',
                          fontSize=16, leading=20, spaceBefore=6, spaceAfter=10,
                          textColor=colors.HexColor('#2C3E50')))

styles.add(ParagraphStyle('SubHeading', parent=styles['Normal'], fontName='Helvetica-Bold',
                          fontSize=12.5, leading=16, spaceBefore=10, spaceAfter=6,
                          textColor=colors.HexColor('#4A6FA5')))

styles.add(ParagraphStyle('BodyJustify', parent=styles['Normal'], fontSize=10.2, leading=15,
                          alignment=TA_JUSTIFY, spaceAfter=8))

styles.add(ParagraphStyle('Caption', parent=styles['Normal'], fontName='Helvetica-Oblique',
                          fontSize=8.5, leading=11, alignment=TA_CENTER,
                          textColor=colors.HexColor('#555555'), spaceBefore=4, spaceAfter=14))

styles.add(ParagraphStyle('CodeBlock', parent=styles['Normal'], fontName='Courier', fontSize=8,
                          leading=11, backColor=colors.HexColor('#F4F4F4'), borderPadding=6,
                          spaceAfter=8))

styles.add(ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica',
                          fontSize=8.3, leading=11))

styles.add(ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold',
                          fontSize=8.7, leading=11, textColor=colors.white))


def generate_pdf():
    story = []

    # Cover Page
    story.extend([
        Spacer(1, 4 * cm),
        Paragraph("Weather-Aware Smart Planner", styles["CoverTitle"]),
        Paragraph("A Smart Task Scheduler Integrating Live Weather Data and Machine Learning in Python", styles["CoverSub"]),
        Spacer(1, 2 * cm),
        Paragraph("VITyarthi — Project Work", styles["CoverMeta"]),
        Paragraph("Project Report", styles["CoverMeta"]),
        Spacer(1, 2 * cm),
        Paragraph("Submitted by: Rishabh Khandelwal", styles["CoverMeta"]),
        Paragraph("Program: B.Tech, CSE (AI/ML Specialization)", styles["CoverMeta"]),
        Paragraph("GitHub Repository: github.com/rishabhkhandelwal322-lgtm/Weather-Aware-Smart-Planner", styles["CoverMeta"]),
        PageBreak()
    ])

    # Section 1: Introduction
    story.append(Paragraph("1. Introduction", styles["SectionHeading"]))
    story.append(Paragraph(
        "The Weather-Aware Smart Planner was built around a simple problem: a normal calendar can tell us when something "
        "is scheduled, but it usually does not tell us whether the weather is suitable for it. For example, an "
        "outdoor errand may be planned for a day with heavy rain. The planner connects the forecast with the task "
        "list and can move outdoor tasks when the conditions are not suitable. It also uses an ML model to give an "
        "outdoor suitability score.",
        styles["BodyJustify"]))
    
    story.append(Paragraph(
        "The project was developed in Python. SQLite is used for local data storage, OpenWeatherMap provides live "
        "forecasts, scikit-learn is used for the ML part, and Streamlit is used for the web interface. Putting these "
        "pieces together gave us practical experience with APIs, databases, machine learning, and UI development.", styles["BodyJustify"]))

    # Section 2: Problem Statement
    story.append(Paragraph("2. Problem Statement", styles["SectionHeading"]))
    story.append(Paragraph(
        "Outdoor activities such as running, errands, or other outdoor work can be affected by weather changes. If the "
        "forecast is not checked before starting, it can result in a cancellation or an unnecessary trip. Normal task "
        "management apps generally do not connect tasks with weather, so the user has to check both separately. This "
        "project tries to reduce that extra step by checking the weather and adjusting suitable outdoor tasks when needed.", styles["BodyJustify"]))
    
    story.append(Paragraph(
        "For the current version, the application is a local, single-user dashboard running through Streamlit. Cloud accounts, "
        "mobile apps, and Google Calendar syncing are not included yet. The main aim is to give students or individual "
        "users a simple way to reduce the manual work involved in checking weather for outdoor tasks.", styles["BodyJustify"]))

    # Section 3: Functional Requirements
    story.append(Paragraph("3. Functional Requirements", styles["SectionHeading"]))
    reqs = [
        ("Task CRUD Operations", "Users can add, view, update, finish, or delete tasks. Each entry takes a "
         "name, priority level, optional target date, and a tag marking it indoor or outdoor."),
        ("Live Forecast Fetching", "Retrieves 5-day/3-hour forecasts from OpenWeatherMap. The app aggregates "
         "these short blocks into single-day summaries and caches them locally to limit API calls."),
        ("Manual Weather Overrides", "Allows manually injecting weather values for testing, working offline, "
         "or filling gaps when looking past the API's standard window."),
        ("Automated Rescheduling Engine", "If an outdoor task sits on a day with high rain chance, the system "
         "finds the next clear day in the forecast window and shifts the task there."),
        ("ML Outdoor Score Predictor", "A scikit-learn classification model analyzes temperature, rain risk, "
         "wind speed, and time of year to generate a 0-100% suitability score for outdoor activities."),
        ("Alerts & Notifications", "Triggers desktop popups via plyer (or SMTP email alerts if set up) when "
         "tasks get automatically moved or can't be safely rescheduled."),
        ("Productivity Analytics", "Generates visual breakdowns of task completion rates, comparing clear vs. "
         "rainy day outcomes to highlight efficiency gains."),
        ("Streamlit Interface", "An interactive Web UI divided into logical tabs for organizing tasks, viewing "
         "forecasts, checking analytics, and browsing execution logs."),
    ]
    for label, text in reqs:
        story.append(Paragraph(f"<b>{label}:</b> {text}", styles["BodyJustify"]))

    # Section 4: Non-Functional Requirements
    story.append(Paragraph("4. Non-Functional Requirements", styles["SectionHeading"]))
    nf_raw = [
        ("Requirement", "How It Is Addressed"),
        ("Performance", "Weather responses are saved in SQLite per date/location so recurring runs don't hit "
         "the OpenWeather API unnecessarily."),
        ("Reliability", "Task and weather state persist locally in planner.db. Database changes use "
         "transaction wrappers so failed writes roll back safely without corrupting data."),
        ("Security", "Sensitive keys sit inside a local .env file using python-dotenv. They are explicitly "
         "git-ignored so secrets never reach the repository."),
        ("Usability", "Streamlit handles UI rendering cleanly. Common fields like current date and medium priority "
         "are pre-filled to keep data entry fast."),
        ("Scalability", "Modules stay isolated (storage, fetcher, engine, predictor, notifications). New weather "
         "sources or storage backends can be added with minimal refactoring."),
        ("Maintainability", "Code follows clear single-responsibility modules with unit coverage in tests/ "
         "checking core rescheduling rules."),
        ("Error Handling", "Custom error handles (e.g., WeatherFetchError) catch API failures or bad user inputs "
         "early so the dashboard doesn't crash unexpectedly.")
    ]

    nf_table_cells = []
    for idx, (title, desc) in enumerate(nf_raw):
        style_type = "TableHeader" if idx == 0 else "TableCell"
        nf_table_cells.append([
            Paragraph(f"<b>{title}</b>", styles[style_type]),
            Paragraph(f"<b>{desc}</b>" if idx == 0 else desc, styles[style_type])
        ])

    nf_table = Table(nf_table_cells, colWidths=[3.3 * cm, 12.7 * cm])
    nf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([nf_table, PageBreak()])

    # Section 5: Architecture
    story.append(Paragraph("5. System Architecture", styles["SectionHeading"]))
    story.append(Paragraph(
        "The application uses a standard layered setup. The Streamlit UI and CLI interface form the entry "
        "layer, passing calls into core business modules (task operations, scheduling, ML predictions, and analytics). "
        "These core services talk to background modules—namely the OpenWeather wrapper and notification handlers—which "
        "interact directly with SQLite for storage.", styles["BodyJustify"]))
    story.append(Image(str(diag_path / "architecture.png"), width=16.5 * cm, height=16.5 * cm * (7.5 / 11)))
    story.append(Paragraph("Figure 5.1 — System Architecture Diagram", styles["Caption"]))
    story.append(PageBreak())

    # Section 6: Diagrams
    story.append(Paragraph("6. Design Diagrams", styles["SectionHeading"]))

    story.append(Paragraph("6.1 Use Case Diagram", styles["SubHeading"]))
    story.append(Paragraph("This diagram shows the main things a user can do in the system, including managing tasks, getting weather data, running scheduling rules, and viewing analytics.", styles["BodyJustify"]))
    story.append(Image(str(diag_path / "use_case.png"), width=15.5 * cm, height=15.5 * cm * (8 / 10)))
    story.append(Paragraph("Figure 6.1 — Use Case Diagram", styles["Caption"]))
    story.append(PageBreak())

    story.append(Paragraph("6.2 Workflow / Process Flow Diagram", styles["SubHeading"]))
    story.append(Paragraph("This shows the main flow of a planning cycle. Pending outdoor tasks are checked against the forecast, and tasks on rainy days can be moved to the next suitable clear day. The user is also notified when a change is made.", styles["BodyJustify"]))
    story.append(Image(str(diag_path / "workflow.png"), width=13 * cm, height=13 * cm * (11.5 / 9.5)))
    story.append(Paragraph("Figure 6.2 — Planner Rescheduling Workflow", styles["Caption"]))
    story.append(PageBreak())

    story.append(Paragraph("6.3 Sequence Diagram", styles["SubHeading"]))
    story.append(Paragraph("This diagram follows what happens after the user selects 'Run Planning Cycle'. It covers checking the cached forecast, deciding whether a task needs to move, changing the task date, and sending notifications.", styles["BodyJustify"]))
    story.append(Image(str(diag_path / "sequence.png"), width=16.5 * cm, height=16.5 * cm * (10.6 / 12)))
    story.append(Paragraph("Figure 6.3 — Sequence Diagram: Run Planning Cycle", styles["Caption"]))
    story.append(PageBreak())

    story.append(Paragraph("6.4 Class / Component Diagram", styles["SubHeading"]))
    story.append(Paragraph("This gives a structural view of the project modules, their main functions, and how the different components connect with the SQLite storage layer.", styles["BodyJustify"]))
    story.append(Image(str(diag_path / "class_diagram.png"), width=16.5 * cm, height=16.5 * cm * (9 / 13)))
    story.append(Paragraph("Figure 6.4 — Class / Component Diagram", styles["Caption"]))
    story.append(PageBreak())

    story.append(Paragraph("6.5 ER Diagram / Database Schema", styles["SubHeading"]))
    story.append(Paragraph("This diagram shows the database tables used for tasks, forecasts, and logs. The logs table connects to tasks through foreign keys, while forecast data is looked up using the date and location.", styles["BodyJustify"]))
    story.append(Image(str(diag_path / "er_diagram.png"), width=16.5 * cm, height=16.5 * cm * (7 / 11)))
    story.append(Paragraph("Figure 6.5 — Entity-Relationship Diagram", styles["Caption"]))
    story.append(PageBreak())

    # Section 7: Design Decisions
    story.append(Paragraph("7. Design Decisions & Rationale", styles["SectionHeading"]))
    design_decisions = [
        ("SQLite over flat JSON or heavy SQL servers", "SQLite was a practical choice because the project did not need a separate database server. It still gives us relational queries, foreign keys, and the data operations needed for the charts."),
        ("Combining hard rules with ML scoring", "The rescheduling rule uses more than 50% rain chance, which makes the decision easy to understand and test. The ML model is used separately to give a 'favorable weather' score based on temperature, wind, and seasonality."),
        ("Using synthetic dataset for ML training", "Since we did not have years of localized weather history, we created a synthetic dataset with seasonal temperatures, monsoon rain trends, and 7% noise. The noise was added so the model would not simply learn an overly simple pattern."),
        ("Caching daily weather forecasts", "During testing, the same weather data can be requested several times. To avoid unnecessary OpenWeather API calls, weather entries are stored locally by location and date, so later planning cycles can use the cached rows."),
        ("Choosing Streamlit over Flask or Tkinter", "Streamlit let us build the multi-tab dashboard mostly in Python. This meant we did not have to create a separate HTML/JavaScript frontend, and it was simpler for this project than using a desktop GUI."),
        ("Graceful feature fallback", "If desktop notifications are not available or the ML model has not been trained, the application records a warning "
         "instead of stopping the rest of the process.")
    ]
    for topic, rationale in design_decisions:
        story.append(Paragraph(f"<b>{topic}:</b> {rationale}", styles["BodyJustify"]))

    # Section 8: Implementation Details
    story.append(Paragraph("8. Implementation Details", styles["SectionHeading"]))
    story.append(Paragraph(
        "The project has 11 modules under src/ and around 2,100 lines of Python code, excluding automated tests and asset "
        "builders. Source code, tests, trained models, and generated outputs are kept separate so the project is easier to work with.", styles["BodyJustify"]))

    modules_meta = [
        ("Module", "Responsibility", "Key Libraries"),
        ("src/storage.py", "SQLite schema setup, connection handling, task/forecast CRUD operations", "sqlite3"),
        ("src/weather_fetcher.py", "Live weather API fetching, 3-hr aggregation, local caching", "requests, python-dotenv"),
        ("src/planner.py", "Rescheduling engine logic, good-weather window searches", "storage, weather_fetcher"),
        ("src/predictor.py", "Synthetic dataset generation, ML training pipeline, prediction helper", "scikit-learn, pandas, joblib"),
        ("src/task_manager.py", "CLI parser, user input validation layer", "argparse"),
        ("src/notifier.py", "Desktop popups and email dispatching with silent failover", "plyer, smtplib"),
        ("src/analytics.py", "Calculates task completion metrics and outputs chart graphics", "matplotlib"),
        ("src/dashboard.py", "Streamlit web interface orchestrating all modules across 4 tabs", "streamlit"),
        ("src/run_interactive.py", "CLI menu navigation with terminal charts and image popup support", "termcharts, rich, matplotlib"),
        ("src/seed_demo_data.py", "Utility script for pre-populating sample tasks and weather history", "storage")
    ]

    impl_table_cells = []
    for idx, (m, r, l) in enumerate(modules_meta):
        style_type = "TableHeader" if idx == 0 else "TableCell"
        impl_table_cells.append([
            Paragraph(f"<b>{m}</b>", styles[style_type]),
            Paragraph(f"<b>{r}</b>" if idx == 0 else r, styles[style_type]),
            Paragraph(f"<b>{l}</b>" if idx == 0 else l, styles[style_type])
        ])

    impl_table = Table(impl_table_cells, colWidths=[4.3 * cm, 7.9 * cm, 3.8 * cm])
    impl_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([impl_table, Spacer(1, 12)])

    story.append(Paragraph("Core Rescheduling Implementation (src/planner.py)", styles["SubHeading"]))
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

    # Section 9: Results
    story.append(Paragraph("9. Screenshots / Results", styles["SectionHeading"]))
    story.append(Paragraph("The following charts are produced by analytics.py from the sample data in the project. They are mainly used to compare task completion under different weather conditions.", styles["BodyJustify"]))
    story.append(Image(str(charts_path / "weather_correlation.png"), width=13 * cm, height=13 * cm * (4 / 6)))
    story.append(Paragraph("Figure 9.1 — Task Completion: Clear vs Rainy Days. Clear day completion (83%) drops significantly on rainy days (33%), confirming why automated rescheduling is useful.", styles["Caption"]))
    story.append(Image(str(charts_path / "completion_by_type.png"), width=13 * cm, height=13 * cm * (4 / 6)))
    story.append(Paragraph("Figure 9.2 — Task Completion Rate: Outdoor vs Indoor Tasks", styles["Caption"]))
    story.append(Image(str(charts_path / "status_breakdown.png"), width=10 * cm, height=10 * cm))
    story.append(Paragraph("Figure 9.3 — Overall Task Status Breakdown", styles["Caption"]))
    story.append(PageBreak())

    # Section 10: Testing
    story.append(Paragraph("10. Testing Approach", styles["SectionHeading"]))
    story.append(Paragraph("Testing was done in two ways: automated unit tests using pytest and manual checks of the CLI and Streamlit interface. This helped us catch both logic errors and issues that only appeared when using the application.", styles["BodyJustify"]))
    
    test_steps = [
        "Verified storage.py by creating tasks, changing schedules, storing forecasts, and confirming data consistency in SQLite logs.",
        "Tested weather_fetcher.py against mock 3-hour API responses to make sure aggregation correctly selected maximum rain probability and wind speeds.",
        "Executed end-to-end planner tests with fake weather data, confirming rainy-day tasks shifted to the right target date.",
        "Evaluated predictor.py with an 80/20 train-test split, hitting 93.8% accuracy (0.933 ROC-AUC), and sanity-checked edge cases manually.",
        "Tested CLI arguments in task_manager.py with invalid dates and empty parameters to verify error messages display properly.",
        "Verified notifier.py fallback behaviors when email secrets or desktop notification drivers were missing.",
        "Seeded demo datasets via seed_demo_data.py to ensure chart outputs matched actual database values without Streamlit errors.",
        "Fixed a termcharts edge-case in run_interactive.py where passing identical zero values caused division-by-zero crashes, adding safe fallback formatting.",
        "Ran full regression test runs after organizing modules under src/ to verify relative import paths and path resolutions."
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(step, styles["BodyJustify"]), leftIndent=12) for step in test_steps],
        bulletType="bullet"))

    # Section 11: Challenges
    story.append(Paragraph("11. Challenges Faced", styles["SectionHeading"]))
    challenges = [
        ("Summarizing 3-hour weather intervals", "OpenWeather's free tier supplies 3-hour chunks rather than daily "
         "forecasts. Aggregation rules had to be written to pick worst-case rain probabilities and maximum wind speeds per day."),
        ("Avoiding overly simplistic ML accuracy", "Initial synthetic datasets were too predictable, leading "
         "to 100% accuracy models. Adding a 7% noise factor forced the classifier to learn realistic, generalizable boundaries."),
        ("Environment setup on Windows", "Troubleshot PowerShell execution issues, missing pip bin paths for "
         "Streamlit CLI execution, and Git CRLF line-ending discrepancies."),
        ("Git merge conflicts on setup", "Resolved initial commit history conflicts with default remote repository "
         "files using git pull --allow-unrelated-histories."),
        ("Cleaning up rogue files", "Cleaned leftover Codespaces devcontainer settings and unneeded boilerplate "
         "files after cross-checking repository files with git ls-files."),
        ("Handling empty databases on Streamlit Cloud", "Discovered a deployment bug where empty database "
         "returns triggered stringified 'None' paths in image components. Solved it with explicit check logic in the dashboard.")
    ]
    for header, detail in challenges:
        story.append(Paragraph(f"<b>{header}:</b> {detail}", styles["BodyJustify"]))
    story.append(PageBreak())

    # Section 12: Learnings
    story.append(Paragraph("12. Learnings & Key Takeaways", styles["SectionHeading"]))
    learnings = [
        "One thing we learned was that not every part of the application needs machine learning. The scheduling rules are easier to control with fixed conditions, while the ML model is useful for giving a probability-style score in the UI.",
        "Caching became important during development because the weather API has limits. Saving the forecast locally meant we could test the planner repeatedly without making the same API request every time.",
        "We also learned that synthetic data can be too easy for a model if the generated values follow the labels too closely. Adding realistic variation and noise made the training data less predictable.",
        "Working on the modules one at a time made debugging easier. We could test storage, weather fetching, and planning separately before connecting everything to the Streamlit interface.",
        "A working program is only part of the project. We also had to deal with Git history, environment variables, Windows-specific issues, and differences in file paths between environments."
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(l, styles["BodyJustify"]), leftIndent=12) for l in learnings],
        bulletType="bullet"))

    # Section 13: Future Enhancements
    story.append(Paragraph("13. Future Enhancements", styles["SectionHeading"]))
    future_work = [
        "Adding multi-user accounts and authentication for shared deployment.",
        "Connecting real climate archive APIs (like Open-Meteo) to replace synthetic training datasets.",
        "Two-way integration with external services like Google Calendar or Outlook.",
        "Mobile companion app or SMS/push alerts for on-the-go notifications.",
        "Expanding rescheduling rules to consider air quality, humidity, and extreme temperatures."
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(fw, styles["BodyJustify"]), leftIndent=12) for fw in future_work],
        bulletType="bullet"))

    # Section 14: References
    story.append(Paragraph("14. References", styles["SectionHeading"]))
    refs = [
        "OpenWeatherMap API Documentation — https://openweathermap.org/api",
        "Streamlit Documentation — https://docs.streamlit.io",
        "scikit-learn Documentation — https://scikit-learn.org/stable/documentation.html",
        "Python sqlite3 Documentation — https://docs.python.org/3/library/sqlite3.html",
        "ReportLab User Guide — https://www.reportlab.com/docs/reportlab-userguide.pdf",
        "matplotlib Documentation — https://matplotlib.org/stable/"
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(r, styles["BodyJustify"]), leftIndent=12) for r in refs],
        bulletType="bullet"))

    # Render Document
    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="Weather-Aware Smart Planner - Project Report",
        author="Rishabh Khandelwal"
    )
    doc.build(story)
    print(f"Report built successfully: {out_pdf}")


if __name__ == "__main__":
    generate_pdf()
    