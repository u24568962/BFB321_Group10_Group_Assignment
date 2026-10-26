# Supply chain model: queueing theory (M/M/1 and M/M/c) for predicted waiting times
# M/M/1: Single server queueing model
# M/M/c: Multi-server queueing model with c servers working in parallel

# the arrival rates and and service rate should be non-negative and the number of servers should be a positive integer. 
# The utilisation is calculated as rho = arrival_rate / (servers * service_rate).
# Arrival and service rates must use the same time unit, so W and Wq are returned in that unit.
# If the utilisation is greater than or equal to 1, it indicates that the system is overloaded and cannot handle the incoming traffic efficiently.
import math


def utilisation(arrival_rate, service_rate, servers=1):
    if arrival_rate < 0 or service_rate <= 0 or servers < 1:
        raise ValueError("Arrival rate must be >= 0, service rate > 0 and servers >= 1")
    utilisation = arrival_rate / (servers * service_rate)
    return utilisation

#Define steady state mm1 metrics for a single lane 
def mm1_metrics(arrival_rate, service_rate):   
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
