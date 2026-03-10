import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

app = Flask(__name__)


def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )
    return conn


@app.route("/")
def home():
    return jsonify({"message": "Job API is running"}), 200


@app.route("/jobs", methods=["GET"])
def get_jobs():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM jobs ORDER BY id;")
    jobs = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(jobs), 200


@app.route("/jobs/<int:job_id>", methods=["GET"])
def get_job(job_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM jobs WHERE id = %s;", (job_id,))
    job = cur.fetchone()

    cur.close()
    conn.close()

    if job is None:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(job), 200


@app.route("/jobs", methods=["POST"])
def create_job():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    title = data.get("title")
    company = data.get("company")

    if not title or not company:
        return jsonify({"error": "title and company are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        INSERT INTO jobs (title, company)
        VALUES (%s, %s)
        RETURNING id, title, company;
        """,
        (title, company)
    )
    new_job = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return jsonify(new_job), 201


@app.route("/jobs/<int:job_id>", methods=["PUT"])
def update_job(job_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM jobs WHERE id = %s;", (job_id,))
    existing_job = cur.fetchone()

    if existing_job is None:
        cur.close()
        conn.close()
        return jsonify({"error": "Job not found"}), 404

    updated_title = data.get("title", existing_job["title"])
    updated_company = data.get("company", existing_job["company"])

    cur.execute(
        """
        UPDATE jobs
        SET title = %s, company = %s
        WHERE id = %s
        RETURNING id, title, company;
        """,
        (updated_title, updated_company, job_id)
    )
    updated_job = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return jsonify(updated_job), 200


@app.route("/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM jobs WHERE id = %s;", (job_id,))
    job = cur.fetchone()

    if job is None:
        cur.close()
        conn.close()
        return jsonify({"error": "Job not found"}), 404

    cur.execute("DELETE FROM jobs WHERE id = %s;", (job_id,))
    conn.commit()

    cur.close()
    conn.close()

    return "", 204


if __name__ == "__main__":
    app.run(debug=True)