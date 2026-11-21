import pymysql

from db import get_db, query_all, query_one
from supply_chain.lane_allocation import allocate_lane, calculate_processing_time, make_lane #call model functions

# Read a crossing from the databse
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
def get_crossing(crossing_id):                                     
    return query_one(CROSSING_SELECT + " WHERE c.id = %s",
                     (crossing_id,))

#Replace the goods_label dictionary with list_goods_categories 
def list_goods_categories():                                       
    return query_all(
        "SELECT id, code, label FROM goods_categories ORDER BY id")   

def list_crossing_goods(crossing_id):                              
    rows = query_all("""
        SELECT g.label
        FROM crossing_goods cg
        JOIN goods_categories g ON g.id = cg.category_id
        WHERE cg.crossing_id = %s
        ORDER BY g.id
    """, (crossing_id,))
    return [r["label"] for r in rows]                              






