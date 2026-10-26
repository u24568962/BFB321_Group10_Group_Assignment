# Supply chain model: queueing theory (M/M/1 and M/M/c) for predicted waiting times
# M/M/1: Single server queueing model
# M/M/c: Multi-server queueing model with c servers working in parallel

# the arrival rates and and service rate should be non-negative and the number of servers should be a positive integer. 
# The utilisation is calculated as rho = arrival_rate / (servers * service_rate).
# Arrival and service rates must use the same time unit, so W and Wq are returned in that unit.
# If the utilisation is greater than or equal to 1, it indicates that the system is overloaded and cannot handle the incoming traffic efficiently.
import math


def utilisation(arrival_rate, service_rate, servers=1):
    if arrival_rate < 0 or service_rate <= 0 or not isinstance(servers, int) or servers < 1:
        raise ValueError("Arrival rate must be >= 0, service rate > 0 and servers a whole number >= 1")
    return arrival_rate / (servers * service_rate)

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
