import pymysql

from db import get_db, query_all, query_one
from supply_chain.lane_allocation import allocate_lane, calculate_processing_time, make_lane #call lane allogation and logic

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






