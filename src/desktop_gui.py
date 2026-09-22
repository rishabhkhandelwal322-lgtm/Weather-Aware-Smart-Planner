"""
desktop_gui.py
-----------------
A native desktop popup window (Tkinter) for the Weather-Aware Smart
Planner. Launched from run_interactive.py, this gives a real,
clickable interface alongside the terminal menu and the Streamlit
dashboard -- a third way to work with the project, no browser or
typing commands required.

Run standalone with:
    python desktop_gui.py
or launch it from the terminal menu (run_interactive.py, option 13).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import storage
import task_manager
import weather_fetcher
import planner
import predictor
import notifier

storage.init_db()


class PlannerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather-Aware Smart Planner")
        self.geometry("780x560")
        self.minsize(680, 480)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tasks_tab = TasksTab(notebook)
        self.weather_tab = WeatherTab(notebook)
        self.planner_tab = PlannerTab(notebook, refresh_tasks_callback=self.tasks_tab.refresh)

        notebook.add(self.tasks_tab, text="Tasks")
        notebook.add(self.weather_tab, text="Weather")
        notebook.add(self.planner_tab, text="Planner")


class TasksTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)

        form = ttk.LabelFrame(self, text="Add Task", padding=8)
        form.pack(fill="x", pady=(0, 8))

        ttk.Label(form, text="Title:").grid(row=0, column=0, sticky="w")
        self.title_entry = ttk.Entry(form, width=30)
        self.title_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(form, text="Type:").grid(row=0, column=2, sticky="w")
        self.type_combo = ttk.Combobox(form, values=["outdoor", "indoor"], width=10, state="readonly")
        self.type_combo.set("outdoor")
        self.type_combo.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(form, text="Priority:").grid(row=1, column=0, sticky="w")
        self.priority_combo = ttk.Combobox(form, values=["low", "medium", "high"], width=10, state="readonly")
        self.priority_combo.set("medium")
        self.priority_combo.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=1, column=2, sticky="w")
        self.date_entry = ttk.Entry(form, width=12)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=1, column=3, padx=5, pady=2)

        ttk.Button(form, text="Add Task", command=self.add_task).grid(row=0, column=4, rowspan=2, padx=10)

        list_frame = ttk.LabelFrame(self, text="Your Tasks", padding=8)
        list_frame.pack(fill="both", expand=True)

        columns = ("id", "title", "type", "priority", "status", "date")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)
        for col, width in zip(columns, (40, 220, 70, 70, 100, 100)):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=6)
        ttk.Button(btn_frame, text="Mark Complete", command=self.complete_selected).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Delete", command=self.delete_selected).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh).pack(side="left", padx=4)

        self.refresh()

    def add_task(self):
        title = self.title_entry.get().strip()
        task_type = self.type_combo.get()
        priority = self.priority_combo.get()
        date = self.date_entry.get().strip() or None

        try:
            task_manager.create_task(
                title=title, task_type=task_type, priority=priority, scheduled_date=date,
            )
            self.title_entry.delete(0, tk.END)
            self.refresh()
        except task_manager.ValidationError as e:
            messagebox.showerror("Could not add task", str(e))

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for task in task_manager.list_tasks():
            self.tree.insert("", "end", values=(
                task["id"], task["title"], task["task_type"], task["priority"],
                task["status"], task["scheduled_date"] or "—",
            ))

    def _get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No selection", "Select a task in the list first.")
            return None
        return int(self.tree.item(selection[0])["values"][0])

    def complete_selected(self):
        task_id = self._get_selected_id()
        if task_id is None:
            return
        try:
            task_manager.mark_complete(task_id)
            self.refresh()
        except task_manager.ValidationError as e:
            messagebox.showerror("Error", str(e))

    def delete_selected(self):
        task_id = self._get_selected_id()
        if task_id is None:
            return
        if messagebox.askyesno("Confirm delete", f"Delete task #{task_id}?"):
            try:
                task_manager.remove_task(task_id)
                self.refresh()
            except task_manager.ValidationError as e:
                messagebox.showerror("Error", str(e))


class WeatherTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Location:").pack(side="left")
        self.location_entry = ttk.Entry(top, width=20)
        self.location_entry.insert(0, "Ashta,IN")
        self.location_entry.pack(side="left", padx=6)
        ttk.Button(top, text="Fetch Forecast", command=self.fetch_forecast).pack(side="left", padx=6)
        ttk.Button(top, text="Predict Good Day", command=self.predict_today).pack(side="left", padx=6)

        self.output = tk.Text(self, height=22, wrap="word", state="disabled")
        self.output.pack(fill="both", expand=True, pady=(8, 0))

    def _write(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.configure(state="disabled")

    def fetch_forecast(self):
        location = self.location_entry.get().strip() or "Ashta,IN"
        try:
            current = weather_fetcher.get_current_weather(location)
            lines = [
                f"Current in {location}: {current['temperature_c']}°C, "
                f"{current['description']}, wind {current['wind_speed_kph']} km/h\n",
                "5-Day Forecast:",
            ]
            for day in weather_fetcher.get_5day_forecast(location):
                lines.append(
                    f"  {day['forecast_date']}: {day['temperature_c']}°C, "
                    f"{day['condition']}, rain {day['rain_probability']:.0%}"
                )
            self._write("\n".join(lines))
        except weather_fetcher.WeatherFetchError as e:
            messagebox.showerror("Weather fetch failed", str(e))

    def predict_today(self):
        location = self.location_entry.get().strip() or "Ashta,IN"
        try:
            forecast = weather_fetcher.get_forecast_for_date(location, datetime.now().strftime("%Y-%m-%d"))
            if not forecast:
                self._write("No forecast available for today yet. Fetch the forecast first.")
                return
            prob = predictor.predict_for_forecast(forecast)
            self._write(f"Predicted good-outdoor-day probability for today: {prob}%")
        except FileNotFoundError:
            messagebox.showinfo("Model not trained", "Train the ML model first (from the terminal menu, option 9).")
        except weather_fetcher.WeatherFetchError as e:
            messagebox.showerror("Weather fetch failed", str(e))


class PlannerTab(ttk.Frame):
    def __init__(self, parent, refresh_tasks_callback=None):
        super().__init__(parent, padding=10)
        self.refresh_tasks_callback = refresh_tasks_callback

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Location:").pack(side="left")
        self.location_entry = ttk.Entry(top, width=20)
        self.location_entry.insert(0, "Ashta,IN")
        self.location_entry.pack(side="left", padx=6)
        ttk.Button(top, text="Run Planning Cycle", command=self.run_cycle).pack(side="left", padx=6)

        self.output = tk.Text(self, height=22, wrap="word", state="disabled")
        self.output.pack(fill="both", expand=True, pady=(8, 0))

    def _write(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.configure(state="disabled")

    def run_cycle(self):
        location = self.location_entry.get().strip() or "Ashta,IN"
        try:
            summary = planner.run_planning_cycle(location)
            notifier.notify_planning_summary(summary)

            lines = [f"Checked {summary['checked']} outdoor task(s).\n"]
            for r in summary["rescheduled"]:
                lines.append(f"Rescheduled '{r['title']}': {r['old_date']} -> {r['new_date']}")
            for u in summary["unresolved"]:
                lines.append(f"Could not reschedule '{u['title']}': {u['reason']}")
            if not summary["rescheduled"] and not summary["unresolved"]:
                lines.append("Nothing needed rescheduling.")

            self._write("\n".join(lines))
            if self.refresh_tasks_callback:
                self.refresh_tasks_callback()
        except weather_fetcher.WeatherFetchError as e:
            messagebox.showerror("Weather fetch failed", str(e))


def launch():
    """Entry point used by run_interactive.py and standalone execution."""
    app = PlannerGUI()
    app.mainloop()


if __name__ == "__main__":
    launch()
