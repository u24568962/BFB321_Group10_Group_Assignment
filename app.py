import os                                                          
from flask import (Flask, flash, redirect, render_template, request, url_for)
import db                                                          
import models                                                      
from api import api 
app = Flask(__name__)                                             
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
db.init_app(app)
app.register_blueprint(api)
@app.route("/")
def index():
    return render_template("index.html",
                           stats=models.dashboard_stats(),
                           hours=models.hourly_flow(12),
                           queue=models.queue_prediction())

# Canopy 1: this is the registration form 
# This is to display the driver and the truck registration forms.
@app.route("/register")
def register():                                                    
    return render_template("register.html", form={})               # created an empty form for registration info
#Editing the canopy truck dreiver d4tails
@app.route("/crossings/<int:crossing_id>/edit", methods=["GET", "POST"])
def edit_crossing(crossing_id):
    crossing = models.get_crossing(crossing_id)
    if crossing is None:
        flash("Crossing not found.", "error")
        return redirect(url_for("register"))

    if request.method == "POST":
        values, errors = models.validate_registration(request.form)
        if not errors:
            ok, message = models.update_crossing(crossing_id, values)
            flash(message, "success" if ok else "error")
            if ok:
                return redirect(url_for("confirm_details", crossing_id=crossing_id))
        for e in errors:
            flash(e, "error")
        crossing = request.form          # keep everyhting that the user typed. 

    return render_template("register.html", form=crossing,
                           editing=True, crossing_id=crossing_id)

@app.route("/confirm", methods=["POST"])  
# now this validates the submitted information in the field before saving                         
def confirm():  
    values, errors = models.validate_registration(request.form)    
    if not errors:
        ok, message, crossing_id = models.register_crossing(values) 
        #save the truck's registration info and get its ID                                                   
  
        if ok:                                                     
            flash(message, "success")
            return redirect(url_for("confirm_details",             
                                    crossing_id=crossing_id))
        errors.append(message)                                     
    # go through every problem found and queue each error message for display

    for e in errors:
        flash(e, "error")
    return render_template("register.html",                        
        form=request.form)  

# Canopy 1: this part is to review the saved details of the truck driver and the truck 
@app.route("/crossings/<int:crossing_id>")                         
def confirm_details(crossing_id):   
    # get the relevant details using the crossing_ID to call that information                               
    crossing = models.get_crossing(crossing_id)  

    # if not found it must return an error and go back to the registration page                
    if crossing is None:
        flash("Crossing not found.", "error")                      
        return redirect(url_for("register"))    
    # show the previously entered details on the confirmation page                   
    return render_template("confirm_details.html", details=crossing)   


# Canopy 1: this section declares the goods carried by the truck
@app.route("/crossings/<int:crossing_id>/goods")                   
def goods(crossing_id):                                            
    if models.get_crossing(crossing_id) is None:                   
        flash("Crossing not found.", "error")
        return redirect(url_for("register"))
    return render_template("goods.html", crossing_id=crossing_id)  

# confirm the goods that were declared
@app.route("/crossings/<int:crossing_id>/goods/confirm",           
           methods=["GET", "POST"])                                
def confirm_goods(crossing_id):   
    # get the crossing ID and first check that is exists                               
    crossing = models.get_crossing(crossing_id)                    
    if crossing is None:
        flash("Crossing not found.", "error")
        return redirect(url_for("register"))
    # get the selected goods if the form was submitted
    if request.method == "POST":                                   
        form = request.form                                        
        goods_label = {g["code"]: g["label"]                       
                       for g in models.list_goods_categories()}    

        # check which of the goods categories were selected
        def ticked(goods_key):                                     
            return goods_key in form                               

        ticked_keys = list(filter(ticked, goods_label))            

        # get any additional goods that was entered by the user that was not part of the common goods
        other_goods = form.get("other_goods", "").strip()          

        # this makes sure that at least one of the types of goods was selected
        if not ticked_keys and not other_goods:                    
            flash("Declare at least one item.", "error")
            return redirect(url_for("goods", crossing_id=crossing_id))

        # save declared goods
        ok, message = models.declare_goods(crossing_id, ticked_keys, other_goods)   
        flash(message, "success" if ok else "error")               
        return redirect(url_for("confirm_goods",                   
                                crossing_id=crossing_id))
    
    # display all the confirmed goods on the confirmation page
    return render_template(                                       
        "confirm_goods.html",                                      
        selected=models.list_crossing_goods(crossing_id),          
        other_goods=crossing["other_goods"],                       
        crossing_id=crossing_id,                                   
    )

# Canopy 1: allocate a truck to the lane (this is done using our model)
@app.route("/crossings/<int:crossing_id>/allocate", methods=["POST"])   
def allocate(crossing_id):
    # run the allocation model and get the result
    ok, message = models.allocate_crossing(crossing_id)            
    flash(message, "success" if ok else "error")   
    # show the lane allocation but if it is not successful return to goods confirmation                
    if ok:
        return redirect(url_for("lane_allocation", crossing_id=crossing_id))
    return redirect(url_for("confirm_goods", crossing_id=crossing_id))

# Canopy 1: this part shows the allocated lane and window 
@app.route("/crossings/<int:crossing_id>/lane")                    
def lane_allocation(crossing_id):  
    # get the details and check if a lane has already been allocated                                
    crossing = models.get_crossing(crossing_id)                    
    if crossing is None or crossing["lane_number"] is None:
        flash("This truck has not been allocated a lane yet.", "error")
        return redirect(url_for("register"))
    # display the allocated lane and the predicted waiting time that was calculated from the model
    return render_template("lane_allocation.html",                 
        lane=crossing["lane_number"],                              
        wait=crossing["predicted_wait_minutes"],                   
        crossing_id=crossing_id)                                   

# Canopy 1: this part shows the admin window that was allocated
@app.route("/crossings/<int:crossing_id>/window")                  
def admin_allocation(crossing_id): 
    # get the details and see if a window has been allocated already                                
    crossing = models.get_crossing(crossing_id)                    
    if crossing is None or crossing["window_number"] is None:
        flash("This truck has not been allocated a window yet.", "error")
        return redirect(url_for("register"))
    # display the allocated window
    return render_template("admin_allocation.html",                
        window=crossing["window_number"],                          
        crossing_id=crossing_id)                                   


# Imm office:truck queue for admin window
@app.route("/immigration")
def immigration():
    return render_template("immigration.html",
                           crossings=models.list_immigration_queue())

# Canopy 2: cleared trucks that can exit  
@app.route("/canopy2")
def canopy2():
    return render_template("canopy2.html",
                           crossings=models.list_ready_to_exit())

#move truck to next steop with one button per row psts
@app.route("/crossings/<int:crossing_id>/advance", methods=["POST"])
def advance(crossing_id):
    expected = request.form.get("expected_status", "")
    ok, message = models.advance_crossing(crossing_id, expected)
    flash(message, "success" if ok else "error")
    # go back to board the button was on
    return redirect(url_for("canopy2" if expected == "cleared" else "immigration"))

if __name__ == "__main__":                                         
    app.run(debug=True)                                            

