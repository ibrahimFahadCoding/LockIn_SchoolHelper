import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from together import Together
import calendar  # Import the calendar module to get month names

# Initialize Together AI client
client = Together(api_key="5bd126d37c96a0f67f1e75a0ae0f8f959fcee795b32df2fedd56547e5127b7dd")


# Function to generate a weekly schedule
def generate_schedule(user_input):
    system_prompt = {
        "role": "system",
        "content": (
            "You are a helpful assistant that creates a schedule from Monday to Sunday."
            " Use short tasks with real times (e.g., 08:00 AM–09:30 AM | Monday | Morning routine)."
            " Vary durations (e.g., 15, 30, 45, 60 mins, etc.)."
        )
    }
    user_prompt = {"role": "user", "content": user_input}

    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[system_prompt, user_prompt],
        temperature=0.6,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


# Function to parse the schedule into a DataFrame
def parse_schedule_to_df(schedule_text):
    rows = []
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for line in schedule_text.split('\n'):
        if "–" in line and "|" in line:
            try:
                # Try to split by the first pipe (|) and ensure correct formatting
                time_range, task_and_day = line.split("|", 1)
                task_and_day = task_and_day.strip()

                # Extract the day and task
                task, day = "", "Unknown"
                for weekday in days_of_week:
                    if weekday in task_and_day:
                        task = task_and_day.replace(weekday, "").strip()
                        day = weekday
                        break

                # Clean up the time range and split into start and end times
                time_range = time_range.strip()
                start_str, end_str = time_range.split("–")
                start = datetime.strptime(start_str.strip(), "%I:%M %p")
                end = datetime.strptime(end_str.strip(), "%I:%M %p")

                # Append the row
                rows.append({
                    "Task": task,
                    "Day": day,
                    "Start": start,
                    "End": end
                })
            except Exception as e:
                st.error(f"Error parsing schedule: {e}")
                continue

    return pd.DataFrame(rows)


# Function to create a calendar grid
def plot_calendar(df, month, year):
    days_in_month = pd.date_range(f"{year}-{month}-01", periods=31, freq="D").to_pydatetime()

    # Initialize a blank grid with columns as days of the week
    calendar_data = {day: [] for day in range(1, 32)}  # Day slots from 1 to 31

    for i in range(1, 32):
        current_day = datetime(year, month, i)
        current_day_weekday = current_day.weekday()  # Monday = 0, Sunday = 6

        # Loop through the tasks and assign them to the correct date
        for _, task in df.iterrows():
            task_date = task["Start"].date()
            if task_date == current_day.date():
                calendar_data[i].append(
                    f"{task['Task']} ({task['Start'].strftime('%I:%M %p')} - {task['End'].strftime('%I:%M %p')})")

    # Create a plotly table-style calendar grid
    fig = go.Figure()
    fig.update_layout(
        title=f"Calendar: {calendar.month_name[month]} {year}",
        showlegend=False,
        margin=dict(t=40, b=40, l=40, r=40),
        height=600,
        plot_bgcolor="white"
    )

    # Loop through days and add task text to each day
    for i in range(1, 32):
        if i <= len(days_in_month):
            current_day = days_in_month[i - 1]
            day_tasks = "\n".join(calendar_data[i]) if calendar_data[i] else "No tasks"
            fig.add_trace(go.Scatter(
                x=[current_day] * len(calendar_data[i]), y=[i] * len(calendar_data[i]),
                mode="text",
                text=calendar_data[i],
                textposition="top center",
                showlegend=False
            ))

    fig.update_xaxes(tickvals=days_in_month, ticktext=[current_day.strftime('%d') for current_day in days_in_month])
    fig.update_yaxes(tickvals=list(range(1, 32)), ticktext=[""] * 32, tickmode="array", showgrid=False, zeroline=False)

    return fig


# Streamlit app
def app():
    st.title("🗓️ AI Schedule Planner")

    user_input = st.text_area("💬 What would you like to schedule for the week?",
                              placeholder="e.g. meetings, study sessions, workouts")

    if st.button("⚡ Generate Schedule"):
        with st.spinner("Generating weekly schedule..."):
            schedule_text = generate_schedule(user_input)
            st.success("✅ Schedule generated!")

            # Display raw text of the schedule
            st.subheader("📝 Raw Weekly Schedule Text")
            st.code(schedule_text)

            # Parse the schedule text into a DataFrame
            df_schedule = parse_schedule_to_df(schedule_text)

            if df_schedule.empty:
                st.warning("⚠️ Couldn’t parse the schedule properly. Try again or simplify your input.")
            else:
                # Display parsed DataFrame
                st.subheader("📊 Visual Weekly Schedule")
                st.dataframe(df_schedule)

                # Generate calendar and display
                st.subheader(f"📅 Calendar for {calendar.month_name[datetime.now().month]} {datetime.now().year}")
                fig = plot_calendar(df_schedule, datetime.now().month, datetime.now().year)
                st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    app()
