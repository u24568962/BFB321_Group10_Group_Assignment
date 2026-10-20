
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/confirm", methods=["POST"])
def confirm():
    details = request.form.to_dict()
    return render_template("confirm_details.html", details=details)

@app.route("/goods", methods=["GET", "POST"])
def goods():
    goods = request.form.to_dict()
    return render_template("goods.html", goods=goods)

@app.route("/confirm_goods", methods=["POST"])
def confirm_goods():
    goods = request.form.to_dict()
    return render_template("confirm_goods.html", goods=goods)

if __name__ == "__main__":
    app.run(debug=True)
