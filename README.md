# Quantum Cloud Resource Management System (QCRMS)

## About the Project
QCRMS is a web-based application designed to manage quantum cloud resources.
It helps users manage cloud providers, devices, reservations, jobs, results,
and feedback through a centralized dashboard.

## Features
- Dashboard with resource summaries
- User management
- Cloud provider management
- Quantum device management
- Resource reservations
- Job submission and tracking
- Execution results
- User feedback

## Technologies Used
- Python
- Flask
- HTML
- CSS
- Oracle Database XE 21c

## Project Structure
- `app.py` – Flask application
- `templates/` – HTML templates
- `static/css/` – CSS stylesheets
- `.gitignore` – Files excluded from Git

## Database
The application uses Oracle Database XE 21c.
Configure your database connection using environment variables
before running the application.

## How to Run
1. Install Python.
2. Install the required Python packages.
3. Configure the Oracle database.
4. Set the database password in the `.env` file.
5. Run `python app.py`.
6. Open `http://127.0.0.1:5000` in your browser.

## Note
This project was developed for academic and learning purposes.
## Application Screenshots

### 1. Dashboard
![QCRMS Dashboard](screenshots/dashboard.png)

### 2. User Management
![User Management](screenshots/users.png)

### 3. Quantum Devices
![Quantum Devices](screenshots/devices.png)

### 4. Job Management
![Job Management](screenshots/jobs.png)

### 5. Execution Results
![Execution Results](screenshots/results.png)
