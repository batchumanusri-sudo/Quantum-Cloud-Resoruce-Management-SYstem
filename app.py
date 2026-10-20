from flask import Flask, render_template, request, redirect, url_for, flash
import oracledb
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "qcrms_secret_key_change_later"

DB_CONFIG = {
    "user": "SYSTEM",
    "password": os.getenv("DB_PASSWORD"),
    "dsn": "localhost:1521/xepdb1"
}


def get_connection():
    conn = oracledb.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT USER,
               SYS_CONTEXT('USERENV', 'CON_NAME'),
               SYS_CONTEXT('USERENV', 'SERVICE_NAME')
        FROM DUAL
    """)
    print("Flask database:", cursor.fetchone())

    cursor.execute("""
        SELECT OWNER, TABLE_NAME
        FROM ALL_TABLES
        WHERE TABLE_NAME = 'USERS'
    """)
    print("USERS tables:", cursor.fetchall())

    cursor.execute("SELECT COUNT(*) FROM USERS")
    print("Flask USERS count:", cursor.fetchone()[0])

    cursor.close()
    return conn
# ---------------- DASHBOARD ----------------
@app.route("/")
def dashboard():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM USERS ORDER BY USER_ID ASC")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM PROVIDERS ORDER BY PROVIDER_ID ASC")
        total_providers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM DEVICES ORDER BY DEVICE_ID ASC")
        total_devices = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM RESERVATIONS ORDER BY RESERVATION_ID ASC")
        total_reservations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM JOBS ORDER BY JOB_ID ASC")
        total_jobs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM RESULTS ORDER BY RESULT_ID ASC")
        total_results = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM FEEDBACK ORDER BY FEEDBACK_ID ASC")
        total_feedback = cursor.fetchone()[0]

        return render_template(
            "dashboard.html",
            total_users=total_users,
            total_providers=total_providers,
            total_devices=total_devices,
            total_reservations=total_reservations,
            total_jobs=total_jobs,
            total_results=total_results,
            total_feedback=total_feedback
        )

    finally:
        cursor.close()
        conn.close()


# ---------------- USERS ----------------

@app.route("/users", methods=["GET", "POST"])
def users():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip()
            role = request.form.get("role", "STUDENT").upper()

            if not first_name or not last_name or not email:
                flash("Please fill in all required fields.", "error")
            elif role not in ("ADMIN", "RESEARCHER", "STUDENT"):
                flash("Invalid user role.", "error")
            else:
                cursor.execute("""
                    INSERT INTO USERS
                    (FIRST_NAME, LAST_NAME, EMAIL, ROLE)
                    VALUES (:1, :2, :3, :4)
                """, (first_name, last_name, email, role))

                conn.commit()
                flash("User added successfully!", "success")

            return redirect(url_for("users"))

        cursor.execute("""
            SELECT USER_ID, FIRST_NAME, LAST_NAME,
                   EMAIL, ROLE, STATUS
            FROM USERS
            ORDER BY USER_ID ASC
        """)
        user_records = cursor.fetchall()

        return render_template("users.html", users=user_records)

    except oracledb.IntegrityError:
        conn.rollback()
        flash("Email already exists or the entered data is invalid.", "error")
        return redirect(url_for("users"))

    except oracledb.Error as error:
        conn.rollback()
        flash(f"Database error: {error}", "error")
        return redirect(url_for("users"))

    finally:
        cursor.close()
        conn.close()


# ---------------- PROVIDERS ----------------

@app.route("/providers", methods=["GET", "POST"])
def providers():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            provider_name = request.form.get("provider_name", "").strip()
            provider_type = request.form.get("provider_type", "").strip()
            region = request.form.get("region", "").strip()
            status = request.form.get("status", "ACTIVE").upper()

            if not provider_name or not provider_type or not region:
                flash("Please fill in all provider fields.", "error")
            else:
                cursor.execute("""
                    INSERT INTO PROVIDERS
                    (PROVIDER_NAME, PROVIDER_TYPE, REGION, STATUS)
                    VALUES (:1, :2, :3, :4)
                """, (provider_name, provider_type, region, status))

                conn.commit()
                flash("Provider added successfully!", "success")

            return redirect(url_for("providers"))

        cursor.execute("""
            SELECT PROVIDER_ID, PROVIDER_NAME,
                   PROVIDER_TYPE, REGION, STATUS
            FROM PROVIDERS
            ORDER BY PROVIDER_ID DESC
        """)
        provider_records = cursor.fetchall()

        return render_template(
            "providers.html",
            providers=provider_records
        )

    except oracledb.Error as error:
        conn.rollback()
        flash(f"Database error: {error}", "error")
        return redirect(url_for("providers"))

    finally:
        cursor.close()
        conn.close()


# ---------------- DEVICES ----------------

@app.route("/devices", methods=["GET", "POST"])
def devices():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            device_name = request.form.get("device_name", "").strip()
            device_type = request.form.get("device_type", "").strip()
            total_qubits = request.form.get("total_qubits", "").strip()
            availability = request.form.get(
                "availability", "AVAILABLE"
            ).upper()
            provider_id = request.form.get("provider_id", "").strip()

            if not all([
                device_name, device_type, total_qubits, provider_id
            ]):
                flash("Please fill in all device fields.", "error")
            elif availability not in ("AVAILABLE", "UNAVAILABLE"):
                flash("Invalid availability status.", "error")
            else:
                try:
                    qubits = int(total_qubits)
                    provider = int(provider_id)

                    if qubits < 0:
                        raise ValueError

                    cursor.execute("""
                        INSERT INTO DEVICES
                        (DEVICE_NAME, DEVICE_TYPE, TOTAL_QUBITS,
                         AVAILABILITY, PROVIDER_ID)
                        VALUES (:1, :2, :3, :4, :5)
                    """, (
                        device_name, device_type, qubits,
                        availability, provider
                    ))

                    conn.commit()
                    flash("Device added successfully!", "success")

                except ValueError:
                    flash("Enter valid numbers for qubits and provider.", "error")

            return redirect(url_for("devices"))

        cursor.execute("""
            SELECT D.DEVICE_ID, D.DEVICE_NAME, D.DEVICE_TYPE,
                   D.TOTAL_QUBITS, D.AVAILABILITY,
                   D.PROVIDER_ID, P.PROVIDER_NAME
            FROM DEVICES D
            LEFT JOIN PROVIDERS P
                ON D.PROVIDER_ID = P.PROVIDER_ID
            ORDER BY D.DEVICE_ID DESC
        """)
        device_records = cursor.fetchall()

        cursor.execute("""
            SELECT PROVIDER_ID, PROVIDER_NAME
            FROM PROVIDERS
            ORDER BY PROVIDER_NAME
        """)
        provider_records = cursor.fetchall()

        return render_template(
            "devices.html",
            devices=device_records,
            providers=provider_records
        )

    except oracledb.Error as error:
        conn.rollback()
        flash(f"Database error: {error}", "error")
        return redirect(url_for("devices"))

    finally:
        cursor.close()
        conn.close()


# ---------------- RESERVATIONS ----------------

@app.route("/reservations", methods=["GET", "POST"])
def reservations():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            user_id = request.form.get("user_id", "").strip()
            device_id = request.form.get("device_id", "").strip()
            start_time = request.form.get("start_time", "").strip()
            end_time = request.form.get("end_time", "").strip()

            try:
                user_id = int(user_id)
                device_id = int(device_id)
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)

                if end_dt <= start_dt:
                    flash("End time must be after start time.", "error")
                    return redirect(url_for("reservations"))

                cursor.execute("""
                    SELECT COUNT(*) FROM USERS WHERE USER_ID = :1
                """, (user_id,))
                if cursor.fetchone()[0] == 0:
                    flash("Selected user does not exist.", "error")
                    return redirect(url_for("reservations"))

                cursor.execute("""
                    SELECT COUNT(*) FROM DEVICES
                    WHERE DEVICE_ID = :1
                      AND AVAILABILITY = 'AVAILABLE'
                """, (device_id,))
                if cursor.fetchone()[0] == 0:
                    flash("Selected device is not available.", "error")
                    return redirect(url_for("reservations"))

                cursor.execute("""
                    INSERT INTO RESERVATIONS
                    (USER_ID, DEVICE_ID, START_TIME, END_TIME, STATUS)
                    VALUES (:1, :2, :3, :4, :5)
                """, (
                    user_id, device_id, start_dt,
                    end_dt, "PENDING"
                ))

                conn.commit()
                flash("Reservation created successfully!", "success")

            except ValueError:
                flash("Please enter valid reservation details.", "error")

            return redirect(url_for("reservations"))

        cursor.execute("""
            SELECT R.RESERVATION_ID, R.USER_ID,
                   U.FIRST_NAME || ' ' || U.LAST_NAME,
                   R.DEVICE_ID, D.DEVICE_NAME,
                   R.START_TIME, R.END_TIME, R.STATUS
            FROM RESERVATIONS R
            JOIN USERS U ON R.USER_ID = U.USER_ID
            JOIN DEVICES D ON R.DEVICE_ID = D.DEVICE_ID
            ORDER BY R.RESERVATION_ID DESC
        """)
        reservation_records = cursor.fetchall()

        cursor.execute("""
            SELECT USER_ID, FIRST_NAME, LAST_NAME
            FROM USERS
            ORDER BY FIRST_NAME
        """)
        user_records = cursor.fetchall()

        cursor.execute("""
            SELECT DEVICE_ID, DEVICE_NAME, AVAILABILITY
            FROM DEVICES
            ORDER BY DEVICE_NAME
        """)
        device_records = cursor.fetchall()

        return render_template(
            "reservations.html",
            reservations=reservation_records,
            users=user_records,
            devices=device_records
        )

    except oracledb.Error as error:
        conn.rollback()
        flash(f"Database error: {error}", "error")
        return redirect(url_for("reservations"))

    finally:
        cursor.close()
        conn.close()


# ---------------- JOBS ----------------

@app.route("/jobs", methods=["GET", "POST"])
def jobs():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            job_name = request.form.get("job_name", "").strip()
            job_type = request.form.get("job_type", "").strip()
            user_id = request.form.get("user_id", "").strip()
            device_id = request.form.get("device_id", "").strip()
            priority = request.form.get("priority", "NORMAL").upper()

            if not all([job_name, job_type, user_id, device_id]):
                flash("Please fill in all job fields.", "error")
            elif priority not in ("LOW", "NORMAL", "HIGH"):
                flash("Invalid priority.", "error")
            else:
                try:
                    user_id = int(user_id)
                    device_id = int(device_id)

                    cursor.execute("""
                        SELECT COUNT(*) FROM USERS WHERE USER_ID = :1
                    """, (user_id,))
                    if cursor.fetchone()[0] == 0:
                        flash("Selected user does not exist.", "error")
                        return redirect(url_for("jobs"))

                    cursor.execute("""
                        SELECT COUNT(*) FROM DEVICES
                        WHERE DEVICE_ID = :1
                          AND AVAILABILITY = 'AVAILABLE'
                    """, (device_id,))
                    if cursor.fetchone()[0] == 0:
                        flash("Selected device is not available.", "error")
                        return redirect(url_for("jobs"))

                    cursor.execute("""
                        INSERT INTO JOBS
                        (USER_ID, DEVICE_ID, JOB_NAME,
                         JOB_TYPE, PRIORITY, STATUS)
                        VALUES (:1, :2, :3, :4, :5, :6)
                    """, (
                        user_id, device_id, job_name,
                        job_type, priority, "SUBMITTED"
                    ))

                    conn.commit()
                    flash("Job submitted successfully!", "success")

                except ValueError:
                    flash("Enter valid user and device IDs.", "error")

            return redirect(url_for("jobs"))

        cursor.execute("""
            SELECT J.JOB_ID, J.JOB_NAME, J.JOB_TYPE,
                   J.PRIORITY, J.STATUS, J.SUBMITTED_AT,
                   U.FIRST_NAME || ' ' || U.LAST_NAME,
                   D.DEVICE_NAME
            FROM JOBS J
            JOIN USERS U ON J.USER_ID = U.USER_ID
            JOIN DEVICES D ON J.DEVICE_ID = D.DEVICE_ID
            ORDER BY J.JOB_ID DESC
        """)
        job_records = cursor.fetchall()

        cursor.execute("""
            SELECT USER_ID, FIRST_NAME, LAST_NAME
            FROM USERS
            ORDER BY FIRST_NAME
        """)
        user_records = cursor.fetchall()

        cursor.execute("""
            SELECT DEVICE_ID, DEVICE_NAME, AVAILABILITY
            FROM DEVICES
            ORDER BY DEVICE_NAME
        """)
        device_records = cursor.fetchall()

        return render_template(
            "jobs.html",
            jobs=job_records,
            users=user_records,
            devices=device_records
        )

    except oracledb.Error as error:
        conn.rollback()
        flash(f"Database error: {error}", "error")
        return redirect(url_for("jobs"))

    finally:
        cursor.close()
        conn.close()


# ---------------- EXECUTION RESULTS ----------------

@app.route("/results", methods=["GET", "POST"])
def results():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            job_id = request.form.get("job_id", "").strip()
            execution_time = request.form.get(
                "execution_time", ""
            ).strip()
            result_status = request.form.get(
                "result_status", ""
            ).upper()
            output_data = request.form.get("output_data", "").strip()

            if not all([job_id, execution_time, result_status]):
                flash(
                    "Job, execution time, and result status are required.",
                    "error"
                )
                return redirect(url_for("results"))

            if result_status not in ("COMPLETED", "FAILED"):
                flash("Select a valid result status.", "error")
                return redirect(url_for("results"))

            try:
                job_id = int(job_id)
                execution_time = float(execution_time)

                if execution_time < 0:
                    raise ValueError

            except ValueError:
                flash(
                    "Enter a valid job ID and non-negative execution time.",
                    "error"
                )
                return redirect(url_for("results"))

            cursor.execute("""
                SELECT COUNT(*) FROM JOBS WHERE JOB_ID = :1
            """, (job_id,))

            if cursor.fetchone()[0] == 0:
                flash("Selected job does not exist.", "error")
                return redirect(url_for("results"))

            cursor.execute("""
                INSERT INTO RESULTS
                (JOB_ID, EXECUTION_TIME, RESULT_STATUS,
                 OUTPUT_DATA, COMPLETED_AT)
                VALUES (:1, :2, :3, :4, CURRENT_TIMESTAMP)
            """, (
                job_id, execution_time,
                result_status, output_data or None
            ))

            conn.commit()
            flash("Execution result saved successfully!", "success")
            return redirect(url_for("results"))

        cursor.execute("""
            SELECT R.RESULT_ID, R.JOB_ID, J.JOB_NAME,
                   R.EXECUTION_TIME, R.RESULT_STATUS,
                   R.OUTPUT_DATA, R.COMPLETED_AT
            FROM RESULTS R
            JOIN JOBS J ON R.JOB_ID = J.JOB_ID
            ORDER BY R.RESULT_ID DESC
        """)

        fetched_results = cursor.fetchall()
        result_records = []

        for row in fetched_results:
            output = row[5]

            if hasattr(output, "read"):
                output = output.read()

            result_records.append((
                row[0], row[1], row[2], row[3],
                row[4], output, row[6]
            ))

        cursor.execute("""
            SELECT JOB_ID, JOB_NAME, STATUS
            FROM JOBS
            ORDER BY JOB_ID DESC
        """)
        job_records = cursor.fetchall()

        return render_template(
            "results.html",
            results=result_records,
            jobs=job_records
        )

    except oracledb.Error as error:
        conn.rollback()
        flash(f"Database error: {error}", "error")
        return redirect(url_for("results"))

    finally:
        cursor.close()
        conn.close()


# ---------------- FEEDBACK ----------------

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            user_id = request.form.get("user_id", "").strip()
            rating = request.form.get("rating", "").strip()
            comments = request.form.get("comments", "").strip()

            try:
                user_id = int(user_id)
                rating = int(rating)

                if rating < 1 or rating > 5:
                    raise ValueError

                cursor.execute("""
                    SELECT COUNT(*) FROM USERS WHERE USER_ID = :1
                """, (user_id,))

                if cursor.fetchone()[0] == 0:
                    flash("Selected user does not exist.", "error")
                    return redirect(url_for("feedback"))

                cursor.execute("""
                    INSERT INTO FEEDBACK
                    (USER_ID, RATING, COMMENTS, SUBMITTED_AT)
                    VALUES (:1, :2, :3, CURRENT_TIMESTAMP)
                """, (user_id, rating, comments or None))

                conn.commit()
                flash("Feedback submitted successfully!", "success")

            except ValueError:
                flash("Select a valid user and a rating from 1 to 5.", "error")

            return redirect(url_for("feedback"))

        cursor.execute("""
            SELECT F.FEEDBACK_ID, F.USER_ID,
                   U.FIRST_NAME || ' ' || U.LAST_NAME,
                   F.RATING, F.COMMENTS, F.SUBMITTED_AT
            FROM FEEDBACK F
            JOIN USERS U ON F.USER_ID = U.USER_ID
            ORDER BY F.FEEDBACK_ID DESC
        """)
        feedback_records = cursor.fetchall()

        cursor.execute("""
            SELECT USER_ID, FIRST_NAME, LAST_NAME
            FROM USERS
            ORDER BY FIRST_NAME
        """)
        user_records = cursor.fetchall()

        return render_template(
            "feedback.html",
            feedback=feedback_records,
            users=user_records
        )

    except oracledb.Error as error:
        conn.rollback()
        flash(f"Database error: {error}", "error")
        return redirect(url_for("feedback"))

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)