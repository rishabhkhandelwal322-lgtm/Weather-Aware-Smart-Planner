"""
dashboard.py
Streamlit UI for Weather Aware Smart Planner project.
Created for final semester project / mini project presentation.

Run using command:
streamlit run dashboard.py
"""

from datetime import datetime
import streamlit as st

# Custom modules imports
import storage
import task_manager
import weather_fetcher
import planner
import analytics
import notifier

# checking if ml predictor model module is present
try:
    import predictor
    predictor_available = True
except Exception as err:
    predictor_available = False
    import_err_msg = str(err)

# initialize sqlite database
storage.init_db()

# setting up streamlit page
st.set_page_config(
    page_title="Weather-Aware Smart Planner", 
    page_icon="⛅", 
    layout="wide"
)

# ==========================================
# SIDEBAR SECTION
# ==========================================

st.sidebar.title("⛅ Smart Planner")
user_location = st.sidebar.text_input(
    "Location", 
    value="Ashta,IN", 
    help="Format: City,CountryCode (e.g. Ashta,IN)"
)

# Trigger manual planning cycle button
if st.sidebar.button("🔄 Run Planning Cycle", use_container_width=True):
    try:
        with st.spinner("Fetching weather forecast and updating task schedule..."):
            plan_summary = planner.run_planning_cycle(user_location)
            notifier.notify_planning_summary(plan_summary)
            
        chk_count = plan_summary['checked']
        resched_count = len(plan_summary['rescheduled'])
        unres_count = len(plan_summary['unresolved'])
        
        st.sidebar.success(
            f"Done! Checked {chk_count} outdoor task(s). "
            f"Rescheduled {resched_count}, "
            f"{unres_count} remaining unresolved."
        )
    except weather_fetcher.WeatherFetchError as weather_err:
        st.sidebar.error(f"Weather Fetch Error: {weather_err}")

st.sidebar.markdown("---")
st.sidebar.caption(
    "Note: If API key is not configured, please use Manual Forecast Entry "
    "or run 'python seed_demo_data.py' via terminal to load test data."
)

# ==========================================
# MAIN DASHBOARD TABS
# ==========================================

task_tab, forecast_tab, analytics_tab, log_tab = st.tabs(
    ["📋 Tasks", "🌦️ Forecast", "📊 Analytics", "🕒 Activity Log"]
)

# ------------------------------------------
# TAB 1: TASKS MANAGEMENT
# ------------------------------------------
with task_tab:
    st.subheader("Add New Task")
    
    with st.form("task_creation_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        t_title = c1.text_input("Title")
        t_type = c2.selectbox("Type", task_manager.VALID_TYPES)
        t_priority = c3.selectbox("Priority", task_manager.VALID_PRIORITIES, index=1)

        c4, c5 = st.columns(2)
        t_date = c4.date_input("Scheduled Date", value=datetime.now())
        t_deadline = c5.date_input("Deadline (Optional)", value=None)

        t_desc = st.text_area("Description (Optional)", height=68)
        btn_submit = st.form_submit_button("Add Task", use_container_width=True)

        if btn_submit:
            try:
                task_manager.create_task(
                    title=t_title,
                    task_type=t_type,
                    description=t_desc,
                    priority=t_priority,
                    deadline=t_deadline.isoformat() if t_deadline else None,
                    scheduled_date=t_date.isoformat() if t_date else None,
                )
                st.success(f"Task '{t_title}' added successfully!")
                st.rerun()
            except task_manager.ValidationError as val_err:
                st.error(str(val_err))

    st.markdown("---")
    st.subheader("Task List")

    # Filter section
    flt_col1, flt_col2 = st.columns(2)
    sel_status = flt_col1.selectbox(
        "Filter by Status", 
        [None, "pending", "rescheduled", "completed", "cancelled"],
        format_func=lambda item: "All" if item is None else str(item).capitalize()
    )
    sel_type = flt_col2.selectbox(
        "Filter by Task Type", 
        [None, "outdoor", "indoor"],
        format_func=lambda item: "All" if item is None else str(item).capitalize()
    )

    task_records = task_manager.list_tasks(status=sel_status, task_type=sel_type)

    if not task_records:
        st.info("No tasks found matching criteria.")
    else:
        for t in task_records:
            row_cols = st.columns([4, 2, 2, 2, 1, 1])
            row_cols[0].write(f"**{t['title']}**")
            row_cols[1].write(t["task_type"])
            row_cols[2].write(t["priority"])
            
            sch_date_str = t['scheduled_date'] if t['scheduled_date'] else '—'
            row_cols[3].write(f"{t['status']} → {sch_date_str}")

            # Mark Complete Action
            if t["status"] != "completed":
                if row_cols[4].button("✅", key=f"btn_done_{t['id']}", help="Mark as Completed"):
                    task_manager.mark_complete(t["id"])
                    st.rerun()
            else:
                row_cols[4].write("✔️")

            # Delete Action
            if row_cols[5].button("🗑️", key=f"btn_del_{t['id']}", help="Delete Task"):
                task_manager.remove_task(t["id"])
                st.rerun()

# ------------------------------------------
# TAB 2: WEATHER FORECAST
# ------------------------------------------
with forecast_tab:
    st.subheader(f"5-Day Weather Forecast — {user_location}")

    try:
        weather_days = weather_fetcher.get_5day_forecast(user_location)
    except weather_fetcher.WeatherFetchError as fetch_err:
        weather_days = []
        st.warning(f"Unable to fetch live weather data: {fetch_err}. Displaying offline/cached records.")

    if not weather_days:
        st.info("No weather data available for this location.")
    else:
        grid_cols = st.columns(len(weather_days))
        for col, day_data in zip(grid_cols, weather_days):
            with col:
                st.markdown(f"**{day_data['forecast_date']}**")
                st.write(f"{day_data['temperature_c']}°C")
                st.write(day_data["condition"])
                st.write(f"💨 {day_data['wind_speed_kph']} km/h")
                st.write(f"🌧️ {day_data['rain_probability']:.0%}")

                if predictor_available:
                    try:
                        outdoor_prob = predictor.predict_for_forecast(day_data)
                        st.progress(int(outdoor_prob), text=f"{outdoor_prob}% suitable outdoor score")
                    except FileNotFoundError:
                        # Model file is missing or not trained yet
                        pass

        st.markdown("---")
        st.subheader("Weather Trends")

        try:
            import pandas as pd
            
            dates_list = [d["forecast_date"] for d in weather_days]
            temps_list = [d["temperature_c"] for d in weather_days]
            rain_list = [round(d["rain_probability"] * 100, 1) for d in weather_days]

            df_trends = pd.DataFrame({
                "Date": dates_list,
                "Temperature (°C)": temps_list,
                "Rain Probability (%)": rain_list,
            }).set_index("Date")

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.caption("Temperature Trend")
                st.line_chart(df_trends["Temperature (°C)"])
            with g_col2:
                st.caption("Precipitation Probability Trend")
                st.bar_chart(df_trends["Rain Probability (%)"])
                
        except ImportError as pd_err:
            st.warning(f"Pandas import failed ({pd_err}). Showing tabular fallback:")
            
            raw_table = "| Date | Temperature (°C) | Rain Probability (%) |\n|---|---|---|\n"
            for d in weather_days:
                raw_table += f"| {d['forecast_date']} | {d['temperature_c']} | {round(d['rain_probability'] * 100, 1)} |\n"
            st.markdown(raw_table)

    st.markdown("---")
    st.subheader("Manual Weather Entry")
    st.caption("Manually input forecast data to test planner offline.")

    with st.form("manual_weather_entry_form", clear_on_submit=True):
        mc1, mc2, mc3, mc4 = st.columns(4)
        m_date = mc1.date_input("Date")
        m_temp = mc2.number_input("Temp (°C)", value=28.0)
        m_cond = mc3.selectbox("Condition", weather_fetcher.VALID_CONDITIONS)
        m_wind = mc4.number_input("Wind Speed (km/h)", value=10.0, min_value=0.0)
        m_rain = st.slider("Rain Probability", 0.0, 1.0, 0.2)

        btn_save_weather = st.form_submit_button("Save Forecast", use_container_width=True)
        if btn_save_weather:
            try:
                weather_fetcher.add_manual_forecast(
                    location=user_location,
                    forecast_date=m_date.isoformat(),
                    temperature_c=m_temp,
                    condition=m_cond,
                    wind_speed_kph=m_wind,
                    rain_probability=m_rain,
                )
                st.success(f"Forecast entry saved for {m_date.isoformat()}.")
                st.rerun()
            except ValueError as v_err:
                st.error(str(v_err))

# ------------------------------------------
# TAB 3: ANALYTICS & CHARTS
# ------------------------------------------
with analytics_tab:
    st.subheader("Productivity & Task Analytics")

    if st.button("Generate / Refresh Charts"):
        with st.spinner("Generating performance reports..."):
            analytics_data = analytics.generate_full_report(user_location)
        st.session_state["analytics_report"] = analytics_data

    current_report = st.session_state.get("analytics_report")

    if not current_report:
        st.info("Click the button above to render analytics charts.")
    else:
        tot_stats = current_report["overall_stats"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tasks", tot_stats["total"])
        m2.metric("Completed", tot_stats["completed"])
        m3.metric("Pending", tot_stats["pending"])
        m4.metric("Completion Rate", f"{tot_stats['completion_rate_pct']}%")

        ch_col1, ch_col2 = st.columns(2)
        with ch_col1:
            if current_report["charts"]["completion_by_type"]:
                st.image(current_report["charts"]["completion_by_type"], use_container_width=True)
            else:
                st.info("Insufficient data for task type chart.")
        with ch_col2:
            if current_report["charts"]["weather_correlation"]:
                st.image(current_report["charts"]["weather_correlation"], use_container_width=True)
            else:
                st.info("Insufficient data for weather correlation chart.")

        if current_report["charts"]["status_breakdown"]:
            st.image(current_report["charts"]["status_breakdown"], width=400)
        else:
            st.info("No status breakdown data available.")

    st.markdown("---")
    st.subheader("Weather Variable Correlation Heatmap")
    st.caption("Correlation matrix showing relations between temperature, rain, wind speed, and weather feasibility ratings.")

    if not predictor_available:
        st.warning(f"ML predictor requirements missing ({_predictor_import_error}). Unable to generate heatmap.")
    else:
        try:
            import plotly.express as px
            
            corr_data = analytics.get_weather_correlation_matrix()
            heat_fig = px.imshow(
                corr_data, 
                text_auto=".2f", 
                color_continuous_scale="RdBu_r", 
                zmin=-1, 
                zmax=1,
                aspect="auto"
            )
            heat_fig.update_layout(height=450)
            st.plotly_chart(heat_fig, use_container_width=True)
        except ImportError as px_err:
            st.warning(f"Plotly library not available: {px_err}")

# ------------------------------------------
# TAB 4: SYSTEM LOGS
# ------------------------------------------
with log_tab:
    st.subheader("System Activity Log")
    db_logs = storage.get_logs(limit=30)

    if not db_logs:
        st.info("No recent logs found.")
    else:
        for entry in db_logs:
            st.write(f"🕒 `{entry['timestamp']}` — **{entry['action']}** — {entry['details']}")