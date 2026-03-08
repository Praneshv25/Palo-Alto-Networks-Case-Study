import sqlite3
import json
import uuid
import os
from datetime import datetime, timedelta, timezone
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
            role TEXT NOT NULL CHECK(role IN ('User', 'Guardian', 'Admin')),
            password_hash TEXT,
            lat REAL,
            lng REAL
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
            created_at TEXT NOT NULL,
            source_count INTEGER NOT NULL DEFAULT 1,
            lat REAL,
            lng REAL,
            news_source TEXT
        );

        CREATE TABLE IF NOT EXISTS news_articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('Local_Physical', 'Digital_Security')),
            published_at TEXT NOT NULL,
            lat REAL,
            lng REAL
        );

        CREATE TABLE IF NOT EXISTS votes (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL REFERENCES safety_reports(id),
            user_id TEXT NOT NULL REFERENCES users(id),
            vote_type TEXT NOT NULL CHECK(vote_type IN ('up', 'down')),
            created_at TEXT NOT NULL,
            UNIQUE(report_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS safe_circle_messages (
            id TEXT PRIMARY KEY,
            circle_owner_id TEXT NOT NULL REFERENCES users(id),
            sender_id TEXT NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
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

    # (id, username, neighborhood, role, password_hash, lat, lng)
    users = [
        ("user_001", "maria", "North End", "Guardian", "pass123", 40.4401, -86.9077),
        ("user_002", "jake", "Downtown", "User", "pass456", 40.4275, -86.9077),
        ("user_003", "aisha", "Eastside", "User", "pass789", 40.4260, -86.8950),
        ("user_004", "tom", "Midtown", "Admin", "admin123", 40.4220, -86.9200),
        ("user_005", "lily", "Southside", "User", "pass321", 40.4150, -86.9077),
    ]
    db.executemany(
        "INSERT INTO users (id, username, neighborhood, role, password_hash, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?)",
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

    def utc_iso(dt):
        return dt.isoformat() + "Z"

    raw_posts = [
        ("post_001", "user_002", "OMG THERE IS A CRAZY FIRE ON NORTH SALISBURY STREET EVERYONE IS GOING TO DIE!!! The smoke is insane run for your lives!!!",
         utc_iso(now - timedelta(hours=5)), "Social"),
        ("post_002", "user_003", "Some sketchy guy just tried to break into my neighbor's car near State Street!! I saw the whole thing this neighborhood is going downhill FAST. We need to do something!!",
         utc_iso(now - timedelta(hours=4)), "Social"),
        ("post_003", "user_005", "SCAM ALERT!!! Got a fake email from 'Duke Energy' saying I owe $500 and they'll cut my power. The link looks super shady DO NOT CLICK IT people!!!",
         utc_iso(now - timedelta(hours=3)), "Manual_Entry"),
        ("post_004", "user_001", "There's a downed power line on Northwestern Ave near State Street. Sparks everywhere. Stay away from the area.",
         utc_iso(now - timedelta(hours=2)), "Manual_Entry"),
        ("post_005", "user_004", "Heads up — multiple people reporting a phishing text message pretending to be from Purdue University asking for SSNs.",
         utc_iso(now - timedelta(hours=1)), "News_Aggregator"),
        ("post_006", "user_002", "There's a huge pothole on Northwestern Ave that just wrecked my tire. The city needs to fix this ASAP before someone gets hurt!!!",
         utc_iso(now - timedelta(minutes=45)), "Social"),
        ("post_007", "user_003", "FLOOD WARNING!! Burnett Creek is overflowing!! Water is getting into the parking lot on the south side. This is NOT a drill people!!",
         utc_iso(now - timedelta(minutes=30)), "Social"),
        ("post_008", "user_005", "Someone hacked into the neighborhood Facebook group and is posting malware links. DO NOT click anything from 'Admin_Official' account!!",
         utc_iso(now - timedelta(minutes=15)), "Social"),
    ]
    db.executemany(
        "INSERT INTO raw_posts (id, author_id, content, timestamp, source_type) VALUES (?, ?, ?, ?, ?)",
        raw_posts,
    )

    # West Lafayette, IN neighbourhood coords used as incident locations
    PA_COORDS = {
        "north":    (40.4401, -86.9077),    # rep_001 – North End
        "downtown": (40.4275, -86.9077),    # rep_002 – Downtown
        "digital":  (None,    None),         # digital reports have no physical location
        "north2":   (40.4380, -86.9020),    # rep_004 – main street area
        "midtown":  (40.4220, -86.9200),    # rep_005 – Midtown
        "greer":    (40.4190, -86.9140),    # rep_006 – South park area
    }

    # (id, parent_post_id, category, severity, title, summary, checklist,
    #  status, location_radius, is_ai_generated, trust_label, upvotes, downvotes,
    #  resolution_note, created_at, source_count, lat, lng)
    reports = [
        ("rep_001", "post_001", "Local_Physical", "High",
         "Structure Fire: North Salisbury Street",
         "A fire has been reported on North Salisbury Street with visible smoke. Emergency services are responding to the scene. Journal & Courier confirms multiple units on scene.",
         json.dumps(["Avoid North Salisbury Street and surrounding blocks.", "Close windows if you smell smoke.", "Check official city alerts for updates."]),
         "Active", 800, 1, "community_verified", 5, 1,
         None, utc_iso(now - timedelta(hours=5)), 2, *PA_COORDS["north"],
         "Journal & Courier: Firefighters respond to blaze on N. Salisbury St"),

        ("rep_002", "post_002", "Local_Physical", "Medium",
         "Vehicle Break-In Attempt: Downtown Area",
         "An attempted vehicle break-in has been reported in the Downtown area near State Street. No injuries or successful theft confirmed.",
         json.dumps(["Lock vehicles and remove visible valuables.", "Report suspicious activity to local police.", "Consider installing a dashcam or motion-sensor light."]),
         "Active", 500, 1, "ai_generated", 2, 0,
         None, utc_iso(now - timedelta(hours=4)), 1, *PA_COORDS["downtown"], None),

        ("rep_003", "post_003", "Digital_Security", "Medium",
         "Phishing Email: Fake Utility Bill Notice",
         "A phishing email impersonating Duke Energy is circulating, claiming overdue payment and threatening service disconnection. No data breach has been confirmed.",
         json.dumps(["Do not click links in unsolicited emails.", "Verify the sender address matches official Duke Energy domains.", "Report the email as spam in your client."]),
         "Active", 0, 1, "ai_generated", 1, 0,
         None, utc_iso(now - timedelta(hours=3)), 1, *PA_COORDS["digital"], None),

        ("rep_004", "post_004", "Local_Physical", "High",
         "Downed Power Line: Northwestern Ave & State St",
         "A downed power line has been reported at Northwestern Ave near State Street. Electrical sparks have been observed.",
         json.dumps(["Stay at least 30 feet away from the downed line.", "Do not touch anything in contact with the wire.", "Call 911 if you haven't already."]),
         "Resolved", 600, 1, "community_verified", 7, 0,
         "Utility crew has secured the area and restored power.", utc_iso(now - timedelta(hours=2)), 1, *PA_COORDS["north2"], None),

        ("rep_005", "post_005", "Digital_Security", "High",
         "SMS Phishing: Fake University Messages",
         "Multiple residents are receiving phishing text messages impersonating Purdue University and requesting Social Security numbers.",
         json.dumps(["Do not reply or provide personal information.", "Block the sender and report to your carrier.", "Notify the university IT security office of the impersonation."]),
         "Active", 0, 1, "ai_generated", 3, 0,
         None, utc_iso(now - timedelta(hours=1)), 1, *PA_COORDS["digital"], None),

        ("rep_006", "post_007", "Local_Physical", "Medium",
         "Creek Overflow: Burnett Creek Area",
         "Burnett Creek is overflowing into the adjacent parking lot on the south side. No structural damage reported yet. WLFI News 18 reports the city has been notified.",
         json.dumps(["Avoid parking near Burnett Creek.", "Monitor local weather and flood advisories.", "Report rising water to public works."]),
         "Active", 400, 1, "community_verified", 3, 0,
         None, utc_iso(now - timedelta(minutes=30)), 2, *PA_COORDS["greer"],
         "WLFI News 18: Burnett Creek flooding threatens south-side parking"),

        # Far-away reports — used to test "Near Me" filter
        ("rep_007", None, "Local_Physical", "High",
         "Wildfire: Malibu Canyon Road Evacuations",
         "A fast-moving wildfire near Malibu Canyon Road has prompted evacuation orders for several residential areas. Cal Fire reports the blaze is 0% contained.",
         json.dumps(["Follow all evacuation orders immediately.", "Tune in to local emergency broadcasts for updates.", "Do not return until authorities declare it safe."]),
         "Active", 5000, 1, "ai_generated", 8, 0,
         None, utc_iso(now - timedelta(hours=3)), 1, 34.0455, -118.7815, None),

        ("rep_008", None, "Digital_Security", "High",
         "Data Breach: Regional Bank Customer Records Exposed",
         "A major data breach at a regional financial institution has exposed customer account numbers and personal data for thousands of clients across the southeast.",
         json.dumps(["Monitor your bank statements for unauthorized transactions.", "Change online banking passwords immediately.", "Enable two-factor authentication on all financial accounts."]),
         "Active", 0, 1, "ai_generated", 4, 0,
         None, utc_iso(now - timedelta(hours=6)), 1, 25.7617, -80.1918, None),

        ("rep_009", None, "Local_Physical", "Medium",
         "Gas Leak: Capitol Hill Neighborhood",
         "Crews are responding to a reported gas leak in the Capitol Hill area. Residents within two blocks are advised to evacuate as a precaution.",
         json.dumps(["Leave the area immediately if you smell gas.", "Do not use electrical switches or open flames.", "Call your gas utility's emergency line."]),
         "Active", 800, 1, "ai_generated", 2, 0,
         None, utc_iso(now - timedelta(hours=1)), 1, 47.6253, -122.3222, None),
    ]
    for r in reports:
        db.execute(
            """INSERT INTO safety_reports
               (id, parent_post_id, category, severity, title, summary, checklist,
                status, location_radius, is_ai_generated, trust_label, upvotes, downvotes,
                resolution_note, created_at, source_count, lat, lng, news_source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            r,
        )

    seed_votes = [
        ("vote_001", "rep_001", "user_001", "up", utc_iso(now - timedelta(hours=4, minutes=50))),
        ("vote_002", "rep_001", "user_003", "up", utc_iso(now - timedelta(hours=4, minutes=45))),
        ("vote_003", "rep_001", "user_004", "up", utc_iso(now - timedelta(hours=4, minutes=40))),
        ("vote_004", "rep_001", "user_005", "up", utc_iso(now - timedelta(hours=4, minutes=30))),
        ("vote_005", "rep_001", "user_002", "up", utc_iso(now - timedelta(hours=4, minutes=20))),
        ("vote_006", "rep_001", "user_003", "down", utc_iso(now - timedelta(hours=4, minutes=10))),
        ("vote_007", "rep_004", "user_002", "up", utc_iso(now - timedelta(hours=1, minutes=50))),
        ("vote_008", "rep_004", "user_003", "up", utc_iso(now - timedelta(hours=1, minutes=40))),
        ("vote_009", "rep_004", "user_005", "up", utc_iso(now - timedelta(hours=1, minutes=30))),
        ("vote_010", "rep_006", "user_002", "down", utc_iso(now - timedelta(minutes=25))),
        ("vote_011", "rep_006", "user_004", "down", utc_iso(now - timedelta(minutes=20))),
        ("vote_012", "rep_006", "user_001", "up", utc_iso(now - timedelta(minutes=15))),
    ]
    # user_003 already voted up on rep_001 (vote_002), so the UNIQUE constraint prevents vote_006
    seed_votes = [v for i, v in enumerate(seed_votes) if i != 5]

    for v in seed_votes:
        db.execute(
            "INSERT INTO votes (id, report_id, user_id, vote_type, created_at) VALUES (?, ?, ?, ?, ?)",
            v,
        )

    # Seed group chat messages for user_001's circle
    chat_messages = [
        ("msg_001", "user_001", "user_001",
         "Hey everyone, is everyone okay after the fire on Salisbury Street?",
         utc_iso(now - timedelta(hours=4, minutes=30))),
        ("msg_002", "user_001", "user_002",
         "We're fine over here. Could see the smoke from Downtown though.",
         utc_iso(now - timedelta(hours=4, minutes=25))),
        ("msg_003", "user_001", "user_003",
         "All safe on the east side. Fire trucks went by about an hour ago.",
         utc_iso(now - timedelta(hours=4, minutes=20))),
        ("msg_004", "user_001", "user_001",
         "Good to hear. Stay away from Salisbury, the road is still blocked off.",
         utc_iso(now - timedelta(hours=4, minutes=15))),
        ("msg_005", "user_001", "user_002",
         "Has anyone heard about the break-in attempt near State Street?",
         utc_iso(now - timedelta(hours=3))),
        ("msg_006", "user_001", "user_003",
         "Yes, I filed a report. Keep your car doors locked tonight.",
         utc_iso(now - timedelta(hours=2, minutes=50))),
        ("msg_007", "user_001", "user_001",
         "Power is back on our block after the downed line on Northwestern Ave.",
         utc_iso(now - timedelta(hours=1, minutes=30))),
        ("msg_008", "user_001", "user_002",
         "Stay away from Northwestern Ave, still sparking near State St.",
         utc_iso(now - timedelta(hours=1, minutes=20))),
        ("msg_009", "user_001", "user_003",
         "The utility crew just arrived. Should be cleared soon.",
         utc_iso(now - timedelta(minutes=45))),
        ("msg_010", "user_001", "user_001",
         "Thanks for the updates everyone. Stay safe out there!",
         utc_iso(now - timedelta(minutes=10))),
    ]
    db.executemany(
        "INSERT INTO safe_circle_messages (id, circle_owner_id, sender_id, content, created_at) VALUES (?, ?, ?, ?, ?)",
        chat_messages,
    )

    # Dummy local news articles
    # Intended matches:
    #   news_001 → rep_001 (Salisbury St fire)
    #   news_002 → rep_006 (Burnett Creek flooding)
    #   news_003 → rep_002 (vehicle break-ins)
    #   news_004 → rep_005 (Purdue phishing SMS)
    #   news_005 / news_006 → no existing report (new incidents users may report)
    news_articles = [
        ("news_001", "Local_Physical",
         "Firefighters respond to structure fire on N. Salisbury St",
         "West Lafayette Fire Department units responded to a structure fire on North Salisbury Street early this morning. Heavy smoke was visible from several blocks away. Residents are advised to avoid the area while crews work to contain the blaze.",
         "Journal & Courier",
         utc_iso(now - timedelta(hours=5, minutes=10)),
         40.4401, -86.9077),

        ("news_002", "Local_Physical",
         "Burnett Creek flooding threatens south-side parking",
         "Rising water levels in Burnett Creek have caused overflow into a parking lot on the south side of West Lafayette. City public works has been notified and crews are assessing the situation. Drivers are urged to avoid the area.",
         "WLFI News 18",
         utc_iso(now - timedelta(minutes=45)),
         40.4190, -86.9140),

        ("news_003", "Local_Physical",
         "Police warn of vehicle break-in spree near State Street",
         "West Lafayette Police Department is asking residents to secure their vehicles after a series of break-in attempts were reported near the State Street corridor downtown. Officers are increasing patrols in the area.",
         "Purdue Exponent",
         utc_iso(now - timedelta(hours=3, minutes=30)),
         40.4275, -86.9077),

        ("news_004", "Digital_Security",
         "Purdue IT warns of phishing texts requesting SSNs",
         "Purdue University IT Security has issued an alert warning students and staff about fraudulent text messages impersonating the university and requesting Social Security numbers. Recipients are urged not to respond and to report the messages.",
         "Purdue Exponent",
         utc_iso(now - timedelta(hours=2)),
         None, None),

        ("news_005", "Local_Physical",
         "Suspicious package reported near Chauncey Hill Mall",
         "West Lafayette police briefly closed a section of Chauncey Hill Mall area after a suspicious package was reported. The package was later determined to be harmless. No injuries were reported.",
         "Journal & Courier",
         utc_iso(now - timedelta(hours=1)),
         40.4248, -86.9081),

        ("news_006", "Digital_Security",
         "Tippecanoe County residents targeted by Medicare scam calls",
         "The Tippecanoe County Sheriff's Office reports a wave of scam phone calls targeting seniors, with callers impersonating Medicare representatives and requesting payment information.",
         "WLFI News 18",
         utc_iso(now - timedelta(hours=4)),
         None, None),
    ]
    db.executemany(
        """INSERT INTO news_articles (id, category, title, content, source, published_at, lat, lng)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        news_articles,
    )

    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
        seed_db()
