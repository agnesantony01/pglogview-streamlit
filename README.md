# 📊 PgLogView - PostgreSQL Log Analyzer

PgLogView is an interactive, lightweight log analysis tool for PostgreSQL, built using [Streamlit](https://streamlit.io/). It enables database administrators and developers to visualize and filter logs for better insight into system behavior, query performance, and error patterns.

Inspired by [pgBadger](https://github.com/dalibo/pgbadger), PgLogView provides a modern, browser-based interface for easy log inspection without needing heavy setup.

---

## 🚀 Features

- 📁 Upload `.log` or `.txt` files from PostgreSQL
- 🔍 Filter logs by:
  - Log level (LOG, ERROR, FATAL, etc.)
  - Database, User, Application
  - Date range
  - Keywords
- 📊 Visual Dashboards:
  - Line chart of connections over time
  - Session bar charts
  - Top SQL statements
  - Frequent errors
  - Heatmap of event distribution (by day and hour)
- 📥 Download filtered logs as **CSV** or **Excel**
- 🎨 Clean, user-friendly layout built with Streamlit


---

## 🛠️ Installation & Running Locally

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/pglogview-streamlit.git
cd pglogview-streamlit
