from supply_chain.lane_allocation import allocate_lane, allocate_window, calculate_processing_time
from supply_chain.queueing_theory import safe_mmc_metrics, min_servers_for_target

# calculate how full the parking lanes are
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

# Give a label and badge colour to the crossing stages for accessibility
STATUS_LABELS = {"registered": "Registered", "goods_declared": "Goods declared","allocated": "Waiting for immigration", "at_immigration": "At immigration","cleared": "Cleared", "exited": "Exited"}
STATUS_BADGES = {"registered": "secondary", "goods_declared": "info", "allocated": "primary","at_immigration": "warning", "cleared": "success", "exited": "dark"}

def _add_stage(rows):
    for row in rows:
        row["stage"] = STATUS_LABELS[row["status"]]
        row["stage_badge"] = STATUS_BADGES[row["status"]]
    return rows

# make lists with a join as left join keeps the empty lanes
LANE_SELECT = """
    SELECT l.id, l.lane_number, l.capacity, l.active,
           COUNT(c.id) AS occupied,
           COALESCE(SUM(c.processing_minutes), 0) AS workload_minutes
    FROM lanes l
    LEFT JOIN crossings c
           ON c.lane_id = l.id AND c.status IN ('allocated', 'at_immigration')
    GROUP BY l.id, l.lane_number, l.capacity, l.active
    ORDER BY l.lane_number
"""

def list_lanes():
    return _add_lane_status(query_all(LANE_SELECT))

# make a parameter-free query per number so that empty days gives ero and not none
def dashboard_stats():
    pipeline = {r["status"]: r["n"] for r in query_all(
        "SELECT status, COUNT(*) AS n FROM crossings "
        "WHERE status <> 'exited' GROUP BY status")}
    exits_today = query_one(
        "SELECT COUNT(*) AS n FROM crossings "
        "WHERE status = 'exited' AND DATE(exited_at) = CURDATE()")["n"]
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
        growth=((arrivals_today - arrivals_yesterday) / arrivals_yesterday * 100 # compares the arrivals with the previous day's arrivals
                if arrivals_yesterday 
                else None),
        avg_turnaround=float(times["turnaround"]) if times["turnaround"] is not None else None,
        avg_wait=float(times["wait"]) if times["wait"] is not None else None,
        lanes=lanes,
        lane_alerts=[l for l in lanes if l["badge"] in ("danger", "warning")],
        recent=list_crossings(per_page=10)[0],
    )

# Make the arrivals and exits per hour for the last 12 hours to make a chart
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


