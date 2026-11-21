import os                                                          
from flask import (Flask, flash, redirect, render_template, request, url_for)
import db                                                          
import models                                                      

app = Flask(__name__)                                             
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
db.init_app(app)

# Canopy 1: this is the registration form 
# This is to display the driver and the truck registration forms.
@app.route("/")
def register():                                                    
    return render_template("register.html", form={})               # created an empty form for registration info

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

