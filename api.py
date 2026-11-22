# JSON API for our projek

from flask import Blueprint, jsonify, request

import models

api = Blueprint("api", __name__, url_prefix="/api")


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


# list, filter and pagination 
@api.get("/crossings")
def crossings_list():
    page = request.args.get("page", "1")
    size = request.args.get("size", "20")
    status = request.args.get("status") or None
    if not (page.isdigit() and size.isdigit()) or int(page) < 1 or not 1 <= int(size) <= 100:
        return jsonify(error="page must be 1 or more and size must be between 1 and 100"), 400
    if status and status not in models.STATUS_LABELS:
        return jsonify(error="status must be one of: " + ", ".join(models.STATUS_LABELS)), 400
    rows, total = models.list_crossings(status, int(page), int(size))
    return jsonify(page=int(page), size=int(size), total=total, items=rows)


#    one crossing
@api.get("/crossings/<int:crossing_id>")
def crossings_get(crossing_id):
    crossing = models.get_crossing(crossing_id)
    if crossing is None:
        return jsonify(error="Crossing not found"), 404
    crossing["goods"] = models.list_crossing_goods(crossing_id)
    return jsonify(crossing)


#   register a truck and driver (Canopy 1)
@api.post("/crossings")
def crossings_create():
    data = _json_body()
    if data is None:
        return jsonify(error="Send a JSON object in the request body"), 400
    values, errors = models.validate_registration(data)
    if errors:
        return jsonify(errors=errors), 400
    ok, message, crossing_id = models.register_crossing(values)
    if not ok:
        return jsonify(error=message), 409          # duplicate manifest / licence
    return jsonify(models.get_crossing(crossing_id)), 201


#   update driver and truck details
@api.put("/crossings/<int:crossing_id>")
def crossings_update(crossing_id):
    if models.get_crossing(crossing_id) is None:
        return jsonify(error="Crossing not found"), 404
    data = _json_body()
    if data is None:
        return jsonify(error="Send a JSON object in the request body"), 400
    values, errors = models.validate_registration(data)
    if errors:
        return jsonify(errors=errors), 400
    ok, message = models.update_crossing(crossing_id, values)
    if not ok:
        return jsonify(error=message), 409
    return jsonify(models.get_crossing(crossing_id))


#    declare goods is of the type   {"goods": ["electronics"], "other_goods": ""}
@api.put("/crossings/<int:crossing_id>/goods")
def crossings_goods(crossing_id):
    if models.get_crossing(crossing_id) is None:
        return jsonify(error="Crossing not found"), 404
    data = _json_body()
    if data is None or not isinstance(data.get("goods", []), list):
        return jsonify(error='Send {"goods": [codes], "other_goods": "text"}'), 400
    known = {g["code"] for g in models.list_goods_categories()}
    unknown = [c for c in data.get("goods", []) if c not in known]
    if unknown:
        return jsonify(error="Unknown goods codes: " + ", ".join(map(str, unknown))), 400
    other = str(data.get("other_goods", "")).strip()
    if not data.get("goods") and not other:
        return jsonify(error="Declare at least one item."), 400
    ok, message = models.declare_goods(crossing_id, data.get("goods", []), other)
    if not ok:
        return jsonify(error=message), 409          # lane has already been allocated
    return jsonify(models.get_crossing(crossing_id))


#  run the lane allocation model
@api.post("/crossings/<int:crossing_id>/allocate")
def crossings_allocate(crossing_id):
    if models.get_crossing(crossing_id) is None:
        return jsonify(error="Crossing not found"), 404
    ok, message = models.allocate_crossing(crossing_id)
    if not ok:
        return jsonify(error=message), 409          # goods not declared / lanes full
    return jsonify(message=message, crossing=models.get_crossing(crossing_id))


#    immigration / canopy 2 step  {"expected_status": "allocated"}
@api.post("/crossings/<int:crossing_id>/advance")
def crossings_advance(crossing_id):
    if models.get_crossing(crossing_id) is None:
        return jsonify(error="Crossing not found"), 404
    data = _json_body() or {}
    ok, message = models.advance_crossing(crossing_id, str(data.get("expected_status", "")))
    if not ok:
        return jsonify(error=message), 409
    return jsonify(message=message, crossing=models.get_crossing(crossing_id))


#   lane occupancy
@api.get("/lanes")
def lanes_list():
    return jsonify(items=models.list_lanes())


# the dashboard numbers with the  the queueing model
@api.get("/kpis")
def kpis():
    return jsonify(stats=models.dashboard_stats(), queue_model=models.queue_prediction())
