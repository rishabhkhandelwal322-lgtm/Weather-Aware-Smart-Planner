import warnings

# Suppress all sklearn model version warnings without importing sklearn directly
warnings.filterwarnings("ignore", message=".*InconsistentVersionWarning.*")
warnings.filterwarnings("ignore", message=".*Trying to unpickle estimator.*")


"""
dashboard.py
-------------
Streamlit front end for the Weather-Aware Smart Planner. Ties
together every other module into one interactive UI:

  - Sidebar: set location, run the planning cycle, trigger notifications
  - Tasks tab: add/list/complete/delete tasks
  - Forecast tab: 5-day forecast + ML-predicted good-outdoor-day probability
  - Analytics tab: completion-rate and weather-correlation charts
  - Activity Log tab: recent create/reschedule/complete history

Run with:
    streamlit run dashboard.py
"""

from datetime import datetime

import streamlit as st

import storage
import task_manager
import weather_fetcher
import planner
import predictor
import analytics
import notifier

storage.init_db()

st.set_page_config(page_title="Weather-Aware Smart Planner", page_icon="⛅", layout="wide")


# ------------------------------------------------------------- sidebar ----

st.sidebar.title("⛅ Smart Planner")
location = st.sidebar.text_input("Location", value="Ashta,IN", help="Format: City,CountryCode")

if st.sidebar.button("🔄 Run Planning Cycle", use_container_width=True):
    try:
        with st.spinner("Fetching forecast and checking tasks..."):
            summary = planner.run_planning_cycle(location)
            notifier.notify_planning_summary(summary)
        st.sidebar.success(
            f"Checked {summary['checked']} outdoor task(s). "
            f"Rescheduled {len(summary['rescheduled'])}, "
            f"{len(summary['unresolved'])} unresolved."
        )
    except weather_fetcher.WeatherFetchError as e:
        st.sidebar.error(f"Weather fetch failed: {e}")

st.sidebar.markdown("---")
st.sidebar.caption(
    "Tip: if you don't have an API key set up yet, use the "
    "**Manual Forecast Entry** panel in the Forecast tab, or run "
    "`python seed_demo_data.py` from the terminal for sample data."
)


# --------------------------------------------------------------- tabs ----

tab_tasks, tab_forecast, tab_analytics, tab_log = st.tabs(
    ["📋 Tasks", "🌦️ Forecast", "📊 Analytics", "🕒 Activity Log"]
)


# ----------------------------------------------------------- Tasks tab ----

with tab_tasks:
    st.subheader("Add a Task")
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        title = col1.text_input("Title")
        task_type = col2.selectbox("Type", task_manager.VALID_TYPES)
        priority = col3.selectbox("Priority", task_manager.VALID_PRIORITIES, index=1)

        col4, col5 = st.columns(2)
        scheduled_date = col4.date_input("Scheduled date", value=datetime.now())
        deadline = col5.date_input("Deadline (optional)", value=None)

        description = st.text_area("Description (optional)", height=68)
        submitted = st.form_submit_button("Add Task", use_container_width=True)

        if submitted:
            try:
                task_manager.create_task(
                    title=title,
                    task_type=task_type,
                    description=description,
                    priority=priority,
                    deadline=deadline.isoformat() if deadline else None,
                    scheduled_date=scheduled_date.isoformat() if scheduled_date else None,
                )
                st.success(f"Added '{title}'.")
                st.rerun()
            except task_manager.ValidationError as e:
                st.error(str(e))

    st.markdown("---")
    st.subheader("Your Tasks")

    col_f1, col_f2 = st.columns(2)
    status_filter = col_f1.selectbox(
        "Filter by status", [None, "pending", "rescheduled", "completed", "cancelled"],
        format_func=lambda x: "All" if x is None else x.capitalize(),
    )
    type_filter = col_f2.selectbox(
        "Filter by type", [None, "outdoor", "indoor"],
        format_func=lambda x: "All" if x is None else x.capitalize(),
    )

    tasks = task_manager.list_tasks(status=status_filter, task_type=type_filter)

    if not tasks:
        st.info("No tasks match the current filters.")
    else:
        for task in tasks:
            cols = st.columns([4, 2, 2, 2, 1, 1])
            cols[0].write(f"**{task['title']}**")
            cols[1].write(task["task_type"])
            cols[2].write(task["priority"])
            cols[3].write(f"{task['status']} → {task['scheduled_date'] or '—'}")

            if task["status"] != "completed":
                if cols[4].button("✅", key=f"complete_{task['id']}", help="Mark complete"):
                    task_manager.mark_complete(task["id"])
                    st.rerun()
            else:
                cols[4].write("✔️")

            if cols[5].button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
                task_manager.remove_task(task["id"])
                st.rerun()


# --------------------------------------------------------- Forecast tab ----

with tab_forecast:
    st.subheader(f"5-Day Forecast — {location}")

    try:
        forecast_days = weather_fetcher.get_5day_forecast(location)
    except weather_fetcher.WeatherFetchError as e:
        forecast_days = []
        st.warning(f"Couldn't fetch live forecast: {e}. Showing cached data if available.")

    if not forecast_days:
        st.info("No forecast data available yet for this location.")
    else:
        cols = st.columns(len(forecast_days))
        for col, day in zip(cols, forecast_days):
            with col:
                st.markdown(f"**{day['forecast_date']}**")
                st.write(f"{day['temperature_c']}°C")
                st.write(day["condition"])
                st.write(f"💨 {day['wind_speed_kph']} km/h")
                st.write(f"🌧️ {day['rain_probability']:.0%}")

                try:
                    prob = predictor.predict_for_forecast(day)
                    st.progress(int(prob), text=f"{prob}% good outdoor day")
                except FileNotFoundError:
                    pass  # model not trained yet; skip prediction silently

    st.markdown("---")
    st.subheader("Manual Forecast Entry")
    st.caption("Add or overwrite a forecast without calling the API.")

    with st.form("manual_forecast_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        m_date = c1.date_input("Date")
        m_temp = c2.number_input("Temp (°C)", value=28.0)
        m_condition = c3.selectbox("Condition", weather_fetcher.VALID_CONDITIONS)
        m_wind = c4.number_input("Wind (km/h)", value=10.0, min_value=0.0)
        m_rain = st.slider("Rain probability", 0.0, 1.0, 0.2)

        if st.form_submit_button("Save Forecast", use_container_width=True):
            try:
                weather_fetcher.add_manual_forecast(
                    location=location,
                    forecast_date=m_date.isoformat(),
                    temperature_c=m_temp,
                    condition=m_condition,
                    wind_speed_kph=m_wind,
                    rain_probability=m_rain,
                )
                st.success(f"Saved forecast for {m_date.isoformat()}.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))


# -------------------------------------------------------- Analytics tab ----

with tab_analytics:
    st.subheader("Productivity Analytics")

    if st.button("Generate / Refresh Charts"):
        with st.spinner("Crunching numbers..."):
            report = analytics.generate_full_report(location)
        st.session_state["analytics_report"] = report

    report = st.session_state.get("analytics_report")

    if not report:
        st.info("Click 'Generate / Refresh Charts' to build the latest analytics.")
    else:
        stats = report["overall_stats"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tasks", stats["total"])
        m2.metric("Completed", stats["completed"])
        m3.metric("Pending", stats["pending"])
        m4.metric("Completion Rate", f"{stats['completion_rate_pct']}%")

        c1, c2 = st.columns(2)
        with c1:
            st.image(report["charts"]["completion_by_type"], use_container_width=True)
        with c2:
            st.image(report["charts"]["weather_correlation"], use_container_width=True)

        st.image(report["charts"]["status_breakdown"], width=400)


# ------------------------------------------------------ Activity Log tab ----

with tab_log:
    st.subheader("Recent Activity")
    logs = storage.get_logs(limit=30)

    if not logs:
        st.info("No activity logged yet.")
    else:
        for log in logs:
            st.write(f"🕒 `{log['timestamp']}` — **{log['action']}** — {log['details']}")




