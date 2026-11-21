
# the arrival rates and and service rate should be non-negative and the number of servers should be a positive integer. 
# The utilisation is calculated as rho = arrival_rate / (servers * service_rate).
# Arrival and service rates must use the same time unit, so W and Wq are returned in that unit.
# If the utilisation is greater than or equal to 1, it indicates that the system is overloaded and cannot handle the incoming traffic efficiently.

"""Supply chain model: queueing theory (M/M/1 and M/M/c) for predicted waiting times.

Queuing theory is used to predict waiting times. Two formulas are used: M/M/1 (single server queueing) abd M/M/c (multi-server queueing).
The formulas are given in the functions below.

Assumptions for both models:
    - The trucks that arrive form a poisson distribution.
    - Service times are exponentially distributed.
    - The queue has unlimited capacity and trucks are served on a first come first serve basis.
    - Utilisation is <1 as system is in a steady-state
"""
import math


def utilisation(arrival_rate, service_rate, servers=1):
    """Calculate the utilisation (rho) of the servers.

    Formula used in utilisation :
        rho = arrival_rate / (servers * service_rate)

    Inputs that the function takes :

        arrival_rate: average number of trucks arriving per time unit, should be more than 0 .

        service_rate: average number of trucks one server can process per time, should be a positive number 
        servers: number of servers working in parallel , atleast 1.

    Stuff that the function returns :
        The utilisation as a fraction 

    """
    if arrival_rate < 0 or service_rate <= 0 or servers < 1:
        raise ValueError("Arrival rate must be >= 0, service rate > 0 and servers >= 1")
    utilisation = arrival_rate / (servers * service_rate)
    return utilisation

#Define steady state mm1 metrics for a single lane 
def mm1_metrics(arrival_rate, service_rate):   
    """Function: steady state M/M/1 metrics for a single lane of traffic at the border bost.

    variables used by this function 
       lambda = arrival_rate
       mu = service_rate


    Formulas that this function uses:
    
       
        rho = lambda / mu
        L   = lambda / (mu - lambda)
        Lq  = lambda**2 / (mu * (mu - lambda))
        W   = 1 / (mu - lambda)
        Wq  = lambda / (mu * (mu - lambda))

    Inputs:
        arrival_rate: average number of trucks arriving per time, should be larger than or equal to 0
        service_rate: average number of trucks the lane can process per time unit, should also be larger than or equal to 0(need to come back and check this)




    """
    rho = utilisation(arrival_rate, service_rate)
    if rho >= 1:
        raise ValueError("System is unstable (utilisation >= 1)")
    lam, mu = arrival_rate, service_rate
    return {
        "rho": rho,
        "L": lam / (mu - lam),  # Average number of trucks in the system
        "Lq": lam**2 / (mu * (mu - lam)),  # Average number of trucks in the queue
        "W": 1 / (mu - lam),  # Average time a truck spends in the system
        "Wq": lam / (mu * (mu - lam)),  # Average time a truck spends waiting in the queue
    }

#Define steady state mmc metrics for multiple admin windows sharing a queue
def mmc_metrics(arrival_rate, service_rate, servers):
    """Function: steady state mmc metrics for multiple admin windows sharing a single queue.

    Formulas (lambda = arrival_rate, mu = service_rate, c = servers):
        a = lambda / mu               
        P0 = 1 /( sum(a**n / n! for n = 0 to c-1) + a^c/ (c!*(1 - rho)))
        P_wait = a^c / (c! * (1 - rho)) * P0 
        Wq  = P_wait / (c * mu - lambda)
        W  = Wq + 1 / mu
        Lq = lambda * Wq              
        L = lambda * W                 

    inputs:
        arrival_rate: average number of trucks arriving pe minute and needs to be greater or equal to zero.
        service_rate: average number of trucks processed per window per minute (also greater than zero)
        servers: number of avaiable admin windows (greater or equal to 1)



    """
    rho = utilisation(arrival_rate, service_rate, servers)
    if rho >= 1:
        raise ValueError("System is unstable (utilisation >= 1)")
    c = servers
    a = arrival_rate / service_rate
    tail = a ** c / (math.factorial(c) * (1 - rho))
    p0 = 1 / (sum(a ** n / math.factorial(n) for n in range(c)) + tail)
    p_wait = tail * p0
    wq = p_wait / (c * service_rate - arrival_rate)
    w = wq + 1 / service_rate
    return {
        "rho": rho,
        "P_wait": p_wait,
        "Lq": arrival_rate * wq,  # Average number of trucks in the queue
        "Wq": wq,  # Average time a truck spends waiting in the queue
        "W": w,  # Average time a truck spends in the system
        "L": arrival_rate * w,  # Average number of trucks in the system
    }

#Test the models
if __name__ == "__main__":

# Test 1: mm1
# Hand calculation: arrival rate = 2, service rate = 3
# rho = 2 / 3           = 0.667
# L   = 2 / (3 - 2)     = 2
# Lq  = 2^2 / (3 * 1)   = 1.333
# W   = 1 / (3 - 2)     = 1
# Wq  = 2 / (3 * 1)     = 0.667
    result = mm1_metrics(2, 3)

    if abs(result["L"] - 2) < 0.001 and abs(result["Lq"] - 1.333) < 0.001 \
            and abs(result["W"] - 1) < 0.001 and abs(result["Wq"] - 0.667) < 0.001:
        print("Test 1 (M/M/1) passed")
    else:
        print("Test 1 (M/M/1) FAILED:", result)

# Test 2: mmc
# Hand calculation: arrival rate = 10, service rate = 4, servers = 3
# a      = 10 / 4                            = 2.5
# rho    = 10 / (3 * 4)                      = 0.833
# P0     = 1 / (1 + 2.5 + 3.125 + 15.625)    = 0.0449
# P_wait = 15.625 * 0.0449                   = 0.702
# Wq     = 0.702 / (12 - 10)                 = 0.351
# Lq     = 10 * 0.351                        = 3.511
    result = mmc_metrics(10, 4, 3)

    if abs(result["P_wait"] - 0.702) < 0.001 and abs(result["Wq"] - 0.351) < 0.001 \
            and abs(result["Lq"] - 3.511) < 0.001:
        print("Test 2 (M/M/c) passed")
    else:
        print("Test 2 (M/M/c) FAILED:", result)

# Test 3: unstable system ----------
# Hand calculation: rho = 3 / 3 = 1, so the model should raise an error
    try:
        mm1_metrics(3, 3)
        print("Test 3 (unstable) FAILED: no error raised")
    except ValueError:
        print("Test 3 (unstable) passed")
