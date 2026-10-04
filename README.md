# Company Employee Dashboard

A Streamlit web app that visualizes insights from 1,000 employee records.

## Features

1. **Average salary by department** — bar chart of mean salary per department  
2. **Employee distribution by department** — donut chart with headcount share  
3. **Salary vs experience** — scatter plot with trend line  
4. **Employee tenure** — tenure buckets with average / median / max metrics  
5. **Performance distribution** — score histogram and performance bands  

Sidebar filters let you narrow results by department and years of experience. Top-level KPIs show employee count, average salary, average experience, and average performance.

## Project structure

```
Company_Dashboard/
├── main.py                 # Streamlit app
├── requirenments.txt       # Python dependencies
├── Data/
│   └── employee_data_1000.csv
└── README.md
```

## Setup

1. Create and activate a virtual environment (optional but recommended):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirenments.txt
```

## Run the app

```powershell
streamlit run main.py
```

Or with the project venv:

```powershell
.\venv\Scripts\streamlit.exe run main.py
```

The dashboard opens in your browser (usually at `http://localhost:8501`).

## Data

The app reads `Data/employee_data_1000.csv`, which includes:

| Column | Description |
|--------|-------------|
| Employee ID | Unique employee identifier |
| Age | Age in years |
| Gender | Gender |
| Department | Department name |
| Salary | Annual salary |
| Joining Date | Date joined |
| Job Role | Job title |
| Experience | Years of experience |
| Performance Score | Score from ~0–10 |
| YearsOfService | Tenure as `"X years and Y months"` |
