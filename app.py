
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/confirm", methods=["POST"])
def confirm():
    details = request.form.to_dict()
    return render_template("confirm_details.html", details=details)

@app.route("/goods")
def goods():
    return render_template("goods.html")

#dictionary of goods labels for the checkboxes in the goods.html template
goods_label = {
    "electronics": "Electronics",
    "furniture": "Furniture",
    "clothing_textiles": "Clothing & Textiles",
    "chemicals": "Chemicals",
    "food_beverages": "Food & Beverages",
    "automotive_parts": "Automotive Parts",
    "machinery_parts": "Machinery & Parts",
    "plastics": "Plastics",
    "building_materials": "Building Materials",
    "paper_products": "Paper Products"
}

@app.route("/confirm_goods", methods=["POST"])
def confirm_goods():
    form = request.form
    #Keep goods in ticked checkboxes
    def ticked(goods_key):
        return goods_key in form

    ticked_keys = filter(ticked, goods_label)

    #Convert key to readable name
    selected_goods = list(map(goods_label.get, ticked_keys))

    #Get other goods  
    other_goods = form.get("other_goods", "").strip()

    return render_template(
        "confirm_goods.html",
        selected=selected_goods,
        other_goods=other_goods,
    )




@app.route("/lane_allocation")
def lane_allocation():
    lane = 3  # Example allocation for now
    return render_template("lane_allocation.html", lane=lane)

@app.route("/admin_allocation")
def admin_allocation():
    window = 2  # Example allocation for now
    return render_template("admin_allocation.html", window=window)

if __name__ == "__main__":
    app.run(debug=True)
