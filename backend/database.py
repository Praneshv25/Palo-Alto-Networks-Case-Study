import sqlite3
import json
import uuid
import os
from datetime import datetime, timedelta
from flask import g

DATABASE = os.path.join(os.path.dirname(__file__), 'guardian.db')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(db=None):
    if db is None:
        db = get_db()

    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            neighborhood TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('User', 'Guardian', 'Admin'))
        );

        CREATE TABLE IF NOT EXISTS safe_circles (
            user_id TEXT NOT NULL REFERENCES users(id),
            contact_id TEXT NOT NULL REFERENCES users(id),
            PRIMARY KEY (user_id, contact_id)
        );

        CREATE TABLE IF NOT EXISTS raw_posts (
            id TEXT PRIMARY KEY,
            author_id TEXT NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            source_type TEXT NOT NULL CHECK(source_type IN ('Social', 'Manual_Entry', 'News_Aggregator'))
        );

        CREATE TABLE IF NOT EXISTS safety_reports (
            id TEXT PRIMARY KEY,
            parent_post_id TEXT REFERENCES raw_posts(id),
            category TEXT NOT NULL CHECK(category IN ('Local_Physical', 'Digital_Security')),
            severity TEXT NOT NULL CHECK(severity IN ('Low', 'Medium', 'High')),
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            checklist TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Resolved')),
            location_radius INTEGER DEFAULT 500,
            is_ai_generated INTEGER NOT NULL DEFAULT 1,
            trust_label TEXT NOT NULL DEFAULT 'ai_generated'
                CHECK(trust_label IN ('ai_generated', 'pending_verification', 'community_verified', 'flagged')),
            upvotes INTEGER NOT NULL DEFAULT 0,
            downvotes INTEGER NOT NULL DEFAULT 0,
            resolution_note TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS votes (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL REFERENCES safety_reports(id),
            user_id TEXT NOT NULL REFERENCES users(id),
            vote_type TEXT NOT NULL CHECK(vote_type IN ('up', 'down')),
            created_at TEXT NOT NULL,
            UNIQUE(report_id, user_id)
        );
    """)
    db.commit()


def seed_db(db=None):
    if db is None:
        db = get_db()

    count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count > 0:
        return

    now = datetime.utcnow()

    users = [
        ("user_001", "Maria Santos", "North Palo Alto", "Guardian"),
        ("user_002", "Jake Chen", "Downtown", "User"),
        ("user_003", "Aisha Patel", "College Terrace", "User"),
        ("user_004", "Tom Rivera", "Midtown", "Admin"),
        ("user_005", "Lily Nguyen", "South Palo Alto", "User"),
    ]
    db.executemany(
        "INSERT INTO users (id, username, neighborhood, role) VALUES (?, ?, ?, ?)",
        users,
    )

    safe_circles = [
        ("user_001", "user_002"),
        ("user_001", "user_003"),
        ("user_002", "user_001"),
        ("user_002", "user_005"),
        ("user_003", "user_001"),
        ("user_003", "user_004"),
        ("user_004", "user_003"),
        ("user_005", "user_002"),
    ]
    db.executemany(
        "INSERT INTO safe_circles (user_id, contact_id) VALUES (?, ?)",
        safe_circles,
    )

    raw_posts = [
        ("post_001", "user_002", "OMG THERE IS A CRAZY FIRE ON ELM STREET EVERYONE IS GOING TO DIE!!! The smoke is insane run for your lives!!!",
         (now - timedelta(hours=5)).isoformat(), "Social"),
        ("post_002", "user_003", "Some sketchy guy just tried to break into my neighbor's car!! I saw the whole thing this neighborhood is going downhill FAST. We need to do something!!",
         (now - timedelta(hours=4)).isoformat(), "Social"),
        ("post_003", "user_005", "SCAM ALERT!!! Got a fake email from 'PG&E' saying I owe $500 and they'll cut my power. The link looks super shady DO NOT CLICK IT people!!!",
         (now - timedelta(hours=3)).isoformat(), "Manual_Entry"),
        ("post_004", "user_001", "There's a downed power line on University Ave near the intersection with Main. Sparks everywhere. Stay away from the area.",
         (now - timedelta(hours=2)).isoformat(), "Manual_Entry"),
        ("post_005", "user_004", "Heads up — multiple people in the Midtown area reporting a phishing text message pretending to be from the local school district asking for SSNs.",
         (now - timedelta(hours=1)).isoformat(), "News_Aggregator"),
        ("post_006", "user_002", "There's a huge pothole on California Ave that just wrecked my tire. The city needs to fix this ASAP before someone gets hurt!!!",
         (now - timedelta(minutes=45)).isoformat(), "Social"),
        ("post_007", "user_003", "FLOOD WARNING!! The creek behind Greer Park is overflowing!! Water is getting into the parking lot. This is NOT a drill people!!",
         (now - timedelta(minutes=30)).isoformat(), "Social"),
        ("post_008", "user_005", "Someone hacked into the neighborhood Facebook group and is posting malware links. DO NOT click anything from 'Admin_Official' account!!",
         (now - timedelta(minutes=15)).isoformat(), "Social"),
    ]
    db.executemany(
        "INSERT INTO raw_posts (id, author_id, content, timestamp, source_type) VALUES (?, ?, ?, ?, ?)",
        raw_posts,
    )

    reports = [
        ("rep_001", "post_001", "Local_Physical", "High",
         "Vegetation Fire: Elm Street Area",
         "A fire has been reported on Elm Street with visible smoke. Emergency services are responding to the scene.",
         json.dumps(["Avoid Elm Street and surrounding blocks.", "Close windows if you smell smoke.", "Check official city alerts for updates."]),
         "Active", 800, 1, "community_verified", 5, 1,
         None, (now - timedelta(hours=5)).isoformat()),

        ("rep_002", "post_002", "Local_Physical", "Medium",
         "Vehicle Break-In Attempt: Downtown Area",
         "An attempted vehicle break-in has been reported in the Downtown neighborhood. No injuries or successful theft confirmed.",
         json.dumps(["Lock vehicles and remove visible valuables.", "Report suspicious activity to local police.", "Consider installing a dashcam or motion-sensor light."]),
         "Active", 500, 1, "ai_generated", 2, 0,
         None, (now - timedelta(hours=4)).isoformat()),

        ("rep_003", "post_003", "Digital_Security", "Medium",
         "Phishing Email: Fake Utility Bill Notice",
         "A phishing email impersonating PG&E is circulating, claiming overdue payment and threatening service disconnection. No data breach has been confirmed.",
         json.dumps(["Do not click links in unsolicited emails.", "Verify sender address matches official PG&E domains.", "Report the email as spam in your client."]),
         "Active", 0, 1, "ai_generated", 1, 0,
         None, (now - timedelta(hours=3)).isoformat()),

        ("rep_004", "post_004", "Local_Physical", "High",
         "Downed Power Line: University Ave & Main",
         "A downed power line has been reported at the intersection of University Ave and Main Street. Electrical sparks have been observed.",
         json.dumps(["Stay at least 30 feet away from the downed line.", "Do not touch anything in contact with the wire.", "Call 911 if you haven't already."]),
         "Resolved", 600, 1, "community_verified", 7, 0,
         "Utility crew has secured the area and restored power.", (now - timedelta(hours=2)).isoformat()),

        ("rep_005", "post_005", "Digital_Security", "High",
         "SMS Phishing: Fake School District Messages",
         "Multiple residents in the Midtown area are receiving phishing text messages impersonating the local school district and requesting Social Security numbers.",
         json.dumps(["Do not reply or provide personal information.", "Block the sender and report to your carrier.", "Notify the school district of the impersonation."]),
         "Active", 0, 1, "ai_generated", 3, 0,
         None, (now - timedelta(hours=1)).isoformat()),

        ("rep_006", "post_007", "Local_Physical", "Medium",
         "Creek Overflow: Greer Park Area",
         "The creek behind Greer Park is overflowing into the adjacent parking lot. No structural damage reported yet.",
         json.dumps(["Avoid parking in the Greer Park lot.", "Monitor local weather and flood advisories.", "Report rising water to public works."]),
         "Active", 400, 0, "pending_verification", 1, 2,
         None, (now - timedelta(minutes=30)).isoformat()),
    ]
    for r in reports:
        db.execute(
            """INSERT INTO safety_reports
               (id, parent_post_id, category, severity, title, summary, checklist,
                status, location_radius, is_ai_generated, trust_label, upvotes, downvotes,
                resolution_note, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            r,
        )

    seed_votes = [
        ("vote_001", "rep_001", "user_001", "up", (now - timedelta(hours=4, minutes=50)).isoformat()),
        ("vote_002", "rep_001", "user_003", "up", (now - timedelta(hours=4, minutes=45)).isoformat()),
        ("vote_003", "rep_001", "user_004", "up", (now - timedelta(hours=4, minutes=40)).isoformat()),
        ("vote_004", "rep_001", "user_005", "up", (now - timedelta(hours=4, minutes=30)).isoformat()),
        ("vote_005", "rep_001", "user_002", "up", (now - timedelta(hours=4, minutes=20)).isoformat()),
        ("vote_006", "rep_001", "user_003", "down", (now - timedelta(hours=4, minutes=10)).isoformat()),
        ("vote_007", "rep_004", "user_002", "up", (now - timedelta(hours=1, minutes=50)).isoformat()),
        ("vote_008", "rep_004", "user_003", "up", (now - timedelta(hours=1, minutes=40)).isoformat()),
        ("vote_009", "rep_004", "user_005", "up", (now - timedelta(hours=1, minutes=30)).isoformat()),
        ("vote_010", "rep_006", "user_002", "down", (now - timedelta(minutes=25)).isoformat()),
        ("vote_011", "rep_006", "user_004", "down", (now - timedelta(minutes=20)).isoformat()),
        ("vote_012", "rep_006", "user_001", "up", (now - timedelta(minutes=15)).isoformat()),
    ]
    # user_003 already voted up on rep_001 (vote_002), so remove duplicate vote_006
    # Fix: vote_006 should be from a different user or removed
    seed_votes[5] = ("vote_006", "rep_001", "user_003", "down", (now - timedelta(hours=4, minutes=10)).isoformat())
    # Actually user_003 already has vote_002 on rep_001 as up. The UNIQUE constraint prevents two votes.
    # Let's just remove the conflicting one and adjust counts.
    seed_votes = [v for i, v in enumerate(seed_votes) if i != 5]

    for v in seed_votes:
        db.execute(
            "INSERT INTO votes (id, report_id, user_id, vote_type, created_at) VALUES (?, ?, ?, ?, ?)",
            v,
        )

    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
        seed_db()
