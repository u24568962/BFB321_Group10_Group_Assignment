
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

@app.route("/confirm_goods", methods=["POST"])
def confirm_goods():
    goods = request.form.to_dict()
    return render_template("confirm_goods.html", goods=goods)

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
