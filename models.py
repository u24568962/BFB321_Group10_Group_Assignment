import pymysql

from db import get_db, query_all, query_one
from datetime import datetime, timedelta
from supply_chain.lane_allocation import mmc_metrics, allocate_lane, calculate_processing_time, make_lane  #call lane allogation and logic

# Read a crossing from the databse
# Use left join only for the lane and window as a new crossing doesnt have any yet and join will hide them
CROSSING_SELECT = """
    SELECT c.id, c.manifest_reference, c.crossing_status, c.other_goods,
           c.processing_minutes, c.predicted_wait_minutes,
           d.full_name AS driver_name, d.passport_number, d.nationality,
           d.contact_number, d.licence_number,
           t.registration_number AS truck_registration, t.country_registration,
           COALESCE(t.make_model, '') AS make_model,
           COALESCE(t.year, '') AS year,
           COALESCE(t.trailer_registration, '') AS trailer_registration,
           l.lane_number, w.window_number
    FROM crossings c
    JOIN drivers d ON d.id = c.driver_id
    JOIN trucks t ON t.id = c.truck_id
    LEFT JOIN lanes l ON l.id = c.lane_id   
    LEFT JOIN admin_windows w ON w.id = c.window_id
"""
# Get one crossing with its details 
def get_crossing(crossing_id):                                     
    return query_one(CROSSING_SELECT + " WHERE c.id = %s",
                     (crossing_id,))

# This is all of the goods categries used to build checkboxes  
def list_goods_categories():                                       
    return query_all(
        "SELECT id, code, label FROM goods_categories ORDER BY id")   

# These are the labels of the declared goods for a crossing 
def list_crossing_goods(crossing_id):                              
    rows = query_all("""
        SELECT g.label
        FROM crossing_goods cg
        JOIN goods_categories g ON g.id = cg.category_id
        WHERE cg.crossing_id = %s
        ORDER BY g.id
    """, (crossing_id,))
    return [r["label"] for r in rows]                              

# Check the registration form
def validate_registration(form):                                  
    errors = []

    def required_text(field, label, max_len):                      
        value = form.get(field, "").strip()
        if not value:
            errors.append(f"{label} is required.")
        elif len(value) > max_len:
            errors.append(f"{label} must be {max_len} characters "
                          "or fewer.")
        return value

    def whole_number(field, label):                                
        try:                                                       
            value = int(form.get(field, ""))                       
            if value < 0:                                          
                errors.append(f"{label} cannot be negative.")      
            return value                                           
        except ValueError:                                         
            errors.append(f"{label} must be a whole number.")      

    values = dict(                                                 
        full_name=required_text("driver_name", "Driver name", 100),
        passport_number=required_text("passport_number", "Passport number", 20).upper(),
        nationality=required_text("nationality", "Nationality", 60),
        contact_number=required_text("contact_number", "Contact number", 20),
        licence_number=required_text("licence_number", "Driver's licence number", 30),
        registration_number=required_text("truck_registration", "Truck registration number", 15).upper(),
        country_registration=required_text("country_registration", "Country of registration", 60),
        make_model=form.get("make_model", "").strip() or None,
        year=whole_number("year", "Year") if form.get("year") else None,
        trailer_registration=form.get("trailer_registration", "").strip().upper() or None,
        manifest_reference=required_text("manifest_reference", "Manifest reference number", 30),
    )
    if values["year"] is not None and not 1950 <= values["year"] <= 2100:   
        errors.append("Year must be between 1950 and 2100.")
    return values, errors

# Save one transaction
def register_crossing(v):                                          
    db = get_db()                                                  
    try:                                                           
        with db.cursor() as cur:                                   
            # driver checks and insert or update
            cur.execute("SELECT id FROM drivers WHERE passport_number = %s FOR UPDATE",
                        (v["passport_number"],))
            driver = cur.fetchone()
            if driver is None:
                cur.execute(
                    "INSERT INTO drivers (full_name, passport_number, nationality, "
                    "contact_number, licence_number) VALUES (%s, %s, %s, %s, %s)",
                    (v["full_name"], v["passport_number"], v["nationality"],
                     v["contact_number"], v["licence_number"]))
                driver_id = cur.lastrowid
            else:
                driver_id = driver["id"]
                cur.execute(
                    "UPDATE drivers SET full_name = %s, nationality = %s, "
                    "contact_number = %s, licence_number = %s WHERE id = %s",
                    (v["full_name"], v["nationality"], v["contact_number"],
                     v["licence_number"], driver_id))

            # trucks with registration checks  
            cur.execute("SELECT id FROM trucks WHERE registration_number = %s FOR UPDATE",
                        (v["registration_number"],))
            truck = cur.fetchone()
            if truck is None:
                cur.execute(
                    "INSERT INTO trucks (registration_number, country_registration, "
                    "make_model, year, trailer_registration) VALUES (%s, %s, %s, %s, %s)",
                    (v["registration_number"], v["country_registration"],
                     v["make_model"], v["year"], v["trailer_registration"]))
                truck_id = cur.lastrowid
            else:
                truck_id = truck["id"]
                cur.execute(
                    "UPDATE trucks SET country_registration = %s, make_model = %s, "
                    "year = %s, trailer_registration = %s WHERE id = %s",
                    (v["country_registration"], v["make_model"], v["year"],
                     v["trailer_registration"], truck_id))

            #crossing and audit
            cur.execute(
                "INSERT INTO crossings (manifest_reference, driver_id, truck_id) "
                "VALUES (%s, %s, %s)",
                (v["manifest_reference"], driver_id, truck_id))
            crossing_id = cur.lastrowid
            cur.execute(
                "INSERT INTO status_events (crossing_id, from_status, to_status) "
                "VALUES (%s, NULL, 'registered')", (crossing_id,))

        db.commit()                                               
        return True, f"Truck {v['registration_number']} registered.", crossing_id

    except pymysql.err.IntegrityError:                             
        db.rollback()
        return False, ("The manifest number or driver's licence number is "
                       "already registered."), None
    except Exception:                                              
        db.rollback()    #undo everything if there are errors                                         
        raise                                                     

# Save the goods
def declare_goods(crossing_id, codes, other_goods):               
    db = get_db()                                                  
    try:                                                           
        with db.cursor() as cur:                                   
            cur.execute("SELECT crossing_status FROM crossings WHERE id = %s FOR UPDATE",
                        (crossing_id,))
            crossing = cur.fetchone()
            if crossing is None:                                   
                db.rollback()                                     
                return False, "That crossing does not exist."
            if crossing["crossing_status"] not in ("registered", "goods_declared"):
                db.rollback()
                return False, "A lane has already been allocated, so the goods can no longer change."

            #replace the old list  
            cur.execute("DELETE FROM crossing_goods WHERE crossing_id = %s", (crossing_id,))
            for code in codes:
                cur.execute(
                    "INSERT INTO crossing_goods (crossing_id, category_id) "
                    "SELECT %s, id FROM goods_categories WHERE code = %s",
                    (crossing_id, code))
            cur.execute(
                "UPDATE crossings SET other_goods = %s, processing_minutes = %s, "
                "crossing_status = 'goods_declared' WHERE id = %s",
                (other_goods or None, calculate_processing_time(codes, other_goods),
                 crossing_id))
            if crossing["crossing_status"] == "registered":       # only the first time
                cur.execute(
                    "INSERT INTO status_events (crossing_id, from_status, to_status) "
                    "VALUES (%s, 'registered', 'goods_declared')", (crossing_id,))

        db.commit()                                                
        return True, "Goods saved."
    except Exception:                                              
        db.rollback()                                              
        raise     

# Allocate the lane and the windows
WINDOW_SQL = """
    SELECT w.id, w.window_number,
           COALESCE(SUM(c.processing_minutes), 0) AS workload_minutes
    FROM admin_windows w
    LEFT JOIN crossings c
           ON c.window_id = w.id
          AND c.crossing_status IN ('allocated', 'at_immigration')
    WHERE w.is_open = 1
    GROUP BY w.id, w.window_number
    ORDER BY workload_minutes, w.window_number
    LIMIT 1
"""

def allocate_crossing(crossing_id):                                
    db = get_db()                                                  
    try:                                                           
        with db.cursor() as cur:                                   
            cur.execute("SELECT crossing_status, other_goods FROM crossings "
                        "WHERE id = %s FOR UPDATE", (crossing_id,))
            crossing = cur.fetchone()
            if crossing is None:                                   
                db.rollback()                                      
                return False, "That crossing does not exist."
            if crossing["crossing_status"] != "goods_declared":
                db.rollback()
                if crossing["crossing_status"] == "registered":
                    return False, "Declare the goods before allocating a lane."
                return True, "This truck already has a lane."      

            #lock the lanes and build the models
            cur.execute("SELECT id FROM lanes WHERE active = 1 FOR UPDATE")
            cur.execute("""
                SELECT l.id, l.lane_number, l.capacity, c.processing_minutes
                FROM lanes l
                LEFT JOIN crossings c
                       ON c.lane_id = l.id
                      AND c.crossing_status IN ('allocated', 'at_immigration')
                WHERE l.active = 1
                ORDER BY l.lane_number
            """)
            lanes, lane_ids = {}, {}
            for row in cur.fetchall():
                number = row["lane_number"]
                if number not in lanes:
                    lanes[number] = make_lane(number, row["capacity"])       
                    lane_ids[number] = row["id"]
                if row["processing_minutes"] is not None:
                    lanes[number]["queue"].append(float(row["processing_minutes"]))

            #let the model choose the lane    
            cur.execute("SELECT g.code FROM crossing_goods cg "
                        "JOIN goods_categories g ON g.id = cg.category_id "
                        "WHERE cg.crossing_id = %s", (crossing_id,))
            codes = [r["code"] for r in cur.fetchall()]
            result = allocate_lane(list(lanes.values()), codes,               
                                   crossing["other_goods"] or "")
            if result is None:                                    
                db.rollback()                                      
                return False, "All lanes are full. Ask the driver to wait and try again."

            #choose a window that is open with the smallest workload
            cur.execute(WINDOW_SQL)
            window = cur.fetchone()
            if window is None:
                db.rollback()
                return False, "No admin window is open."

            #save allocation + audit
            cur.execute(
                "UPDATE crossings SET crossing_status = 'allocated', lane_id = %s, "
                "window_id = %s, processing_minutes = %s, predicted_wait_minutes = %s, "
                "allocated_at = NOW() WHERE id = %s",
                (lane_ids[result["lane"]], window["id"], result["processing_min"],
                 result["predicted_wait_min"], crossing_id))
            cur.execute(
                "INSERT INTO status_events (crossing_id, from_status, to_status) "
                "VALUES (%s, 'goods_declared', 'allocated')", (crossing_id,))

        db.commit()                                                
        return True, (f"Lane {result['lane']}, admin window {window['window_number']}. "
                      f"Predicted wait {result['predicted_wait_min']} min.")
    except Exception:                                              
        db.rollback()                                              
        raise  

# create labels and badge colours for the crossing stages
STATUS_LABELS = {"registered": "Registered", "goods_declared": "Goods declared", "allocated": "Waiting for immigration", "at_immigration": "At immigration", "cleared": "Cleared", "exited": "Exited"}

STATUS_BADGES = {"registered": "secondary", "goods_declared": "info", "allocated": "primary", "at_immigration": "warning", "cleared": "success", "exited": "dark"}

#add the stage rows
def _add_stage(rows):
    for row in rows:
        row["stage"] = STATUS_LABELS[row["crossing_status"]]
        row["stage_badge"] = STATUS_BADGES[row["crossing_status"]]
    return rows

#make a list ofnthe trucks with window and lane that are not cleared  
def list_immigration_queue():
    rows = query_all(CROSSING_SELECT + """
        WHERE c.crossing_status IN ('allocated', 'at_immigration')
        ORDER BY w.window_number, c.allocated_at
    """)
    return _add_goods(_add_stage(rows))

#make a list oft he cleared trucks that can leave
def list_ready_to_exit():
    rows = query_all(CROSSING_SELECT + """
        WHERE c.crossing_status = 'cleared'
        ORDER BY c.cleared_at
    """)
    return _add_goods(_add_stage(rows))

# put the declared goods at the row so officer sees them  
def _add_goods(rows):
    for row in rows:
        row["goods"] = list_crossing_goods(row["id"])
    return rows

# We need to move the trucks to the next step
#show next status and time of steps
NEXT_STEP = {
    "allocated": ("at_immigration",
        "UPDATE crossings SET crossing_status = 'at_immigration', "
        "immigration_started_at = NOW() WHERE id = %s"),
    "at_immigration": ("cleared",
        "UPDATE crossings SET crossing_status = 'cleared', "
        "cleared_at = NOW() WHERE id = %s"),
    "cleared": ("exited",
        "UPDATE crossings SET crossing_status = 'exited', "
        "exited_at = NOW() WHERE id = %s"),
}

def advance_crossing(crossing_id, expected_status, user_id=None):
    if expected_status not in NEXT_STEP:
        return False, "Truck cannot move to next step."
    new_status, update_sql = NEXT_STEP[expected_status]
    db = get_db()
    try:
        with db.cursor() as cur:
            #lock crossing, two officials cant click same truck at same time
            cur.execute("SELECT crossing_status FROM crossings WHERE id = %s FOR UPDATE",
                        (crossing_id,))
            crossing = cur.fetchone()
            if crossing is None:
                db.rollback()
                return False, "Crossing does not exist."
            if crossing["crossing_status"] != expected_status:
                db.rollback()
                return False, "Truck already moved to next step."

            cur.execute(update_sql, (crossing_id,))
            cur.execute(
                "INSERT INTO status_events (crossing_id, from_status, to_status, user_id) "
                "VALUES (%s, %s, %s, %s)",
                (crossing_id, expected_status, new_status, user_id))

        db.commit() # status+ audit row saved together
        return True, f"Truck moved to '{STATUS_LABELS[new_status]}'."
    except Exception:
        db.rollback() # undo both
        raise

# Calculate the lane occupancy on the dashboard  
#Calculate how full the lane is  
def lane_status(occupied, capacity, active=True):
    if not active:
        return "Closed", "secondary"
    if occupied >= capacity:
        return "Full", "danger"
    if occupied >= capacity - 1:
        return "Nearly full", "warning"
    return "Free", "success"

def _add_lane_status(rows):
    for row in rows:
        row["status"], row["badge"] = lane_status(row["occupied"], row["capacity"], row["active"])
    return rows
#use left join to keep the empty lanes in rhe list 
LANE_SELECT = """
    SELECT l.id, l.lane_number, l.capacity, l.active,
           COUNT(c.id) AS occupied,
           COALESCE(SUM(c.processing_minutes), 0) AS workload_minutes
    FROM lanes l
    LEFT JOIN crossings c
           ON c.lane_id = l.id AND c.crossing_status IN ('allocated', 'at_immigration')
    GROUP BY l.id, l.lane_number, l.capacity, l.active
    ORDER BY l.lane_number
"""

def list_lanes():
    return _add_lane_status(query_all(LANE_SELECT))

# Last 10 crossings for recent crossings table
def list_recent_crossings(limit=10):
    return _add_stage(query_all("""
        SELECT c.id, c.manifest_reference, c.crossing_status, c.arrived_at,
               d.full_name, t.registration_number
        FROM crossings c
        JOIN drivers d ON d.id = c.driver_id
        JOIN trucks t ON t.id = c.truck_id
        ORDER BY c.arrived_at DESC, c.id DESC
        LIMIT %s
    """, (limit,)))

# Show the kpis for the dashboard
def dashboard_stats():
    pipeline = {r["status"]: r["n"] for r in query_all(
        "SELECT crossing_status AS status, COUNT(*) AS n FROM crossings "
        "WHERE crossing_status <> 'exited' GROUP BY crossing_status")}
    exits_today = query_one(
        "SELECT COUNT(*) AS n FROM crossings "
        "WHERE crossing_status = 'exited' AND DATE(exited_at) = CURDATE()")["n"]
    arrivals_today = query_one(
        "SELECT COUNT(*) AS n FROM crossings WHERE DATE(arrived_at) = CURDATE()")["n"]
    arrivals_yesterday = query_one(
        "SELECT COUNT(*) AS n FROM crossings "
        "WHERE DATE(arrived_at) = CURDATE() - INTERVAL 1 DAY")["n"]
    times = query_one("""
        SELECT AVG(CASE WHEN DATE(exited_at) = CURDATE()
                        THEN TIMESTAMPDIFF(SECOND, arrived_at, exited_at) END) / 60 AS turnaround,
               AVG(CASE WHEN DATE(immigration_started_at) = CURDATE()
                        THEN TIMESTAMPDIFF(SECOND, allocated_at, immigration_started_at) END) / 60 AS wait
        FROM crossings
    """)

    lanes = list_lanes()
    return dict(
        pipeline=pipeline,
        in_border=sum(pipeline.values()),
        exits_today=exits_today,
        arrivals_today=arrivals_today,
        growth=((arrivals_today - arrivals_yesterday) / arrivals_yesterday * 100
                if arrivals_yesterday else None),
        avg_turnaround=float(times["turnaround"]) if times["turnaround"] is not None else None,
        avg_wait=float(times["wait"]) if times["wait"] is not None else None,
        lanes=lanes,
        lane_alerts=[l for l in lanes if l["badge"] in ("danger", "warning")],
        recent=list_recent_crossings(10),
    )

# make arrivals per hour for a bar chart
def hourly_flow(hours=12):
    rows = query_all("""
        SELECT DATE_FORMAT(arrived_at, '%%Y-%%m-%%d %%H') AS hk, COUNT(*) AS arrivals
        FROM crossings
        WHERE arrived_at >= NOW() - INTERVAL %s HOUR
        GROUP BY hk
    """, (hours,))
    by_hour = {r["hk"]: r["arrivals"] for r in rows}
    now, out = datetime.now(), []
    for back in range(hours - 1, -1, -1):       
        h = now - timedelta(hours=back)
        hk = h.strftime("%Y-%m-%d %H")
        out.append(dict(label=h.strftime("%H:00"), arrivals=by_hour.get(hk, 0)))
    top = max((h["arrivals"] for h in out), default=0) or 1
    for h in out:
        h["height"] = max(8, round(h["arrivals"] / top * 100)) if h["arrivals"] else 8
    return out

#use queieng model with live data  
#predict the wait at admin windows (M/M/c)
def queue_prediction():
    arrivals = query_one("SELECT COUNT(*) AS n FROM crossings "
                         "WHERE arrived_at >= NOW() - INTERVAL 1 HOUR")["n"]
    service = query_one("SELECT AVG(processing_minutes) AS m FROM crossings "
                        "WHERE processing_minutes IS NOT NULL")["m"]
    windows = query_one("SELECT COUNT(*) AS n FROM admin_windows WHERE is_open = 1")["n"]
    if not service or not windows:
        return None
    try:
        result = mmc_metrics(arrivals / 60, 1 / float(service), windows)
    except ValueError:  # utilisation >= 1 (model keeps growing)
        return dict(overloaded=True, windows=windows)
    result.update(overloaded=False, windows=windows, arrivals_per_hour=arrivals)
    return result





                          








