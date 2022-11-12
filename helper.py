def apr(origination, service, duration, rfr, profit, CST, CSB, lease_months):
    # Sum the unchanging components of the loan
    i = origination + service + rfr + profit

    #Define the probability of tenant default(TD)
    TD = 1 - (CST-300)/(850-300) 
    #Define the probability of Borrower default(BD)
    BD = 1 - (CSB-300)/(850-300) 

    #Calculate the probability of double default with current tenant
    D = (1 - ((TD)*(BD)))*550 + 300

    #Use double default probability to create a combined credit score of landlord + current tenant 
    if D > 740:
        rate = 0.0194
    elif D > 650:
        rate = 0.0497
    elif D > 590:
        rate = 0.0847
    elif D > 500:
        rate = .1228
    elif D >= 300:
        rate = .1452

    #Use double default probability to create a combined credit score of landlord + average tenant (avg tenant (AT) = 620)
    AT = 620

    A = (1 - ((BD)*(1 - (AT-300)/(850-300))))*550 + 300

    if A > 740:
        rrate = 0.0194
    elif A > 650:
        rrate = 0.0497
    elif A > 590:
        rrate = 0.0847
    elif A > 500:
        rrate = .1228
    elif A >= 300:
        rrate = .1452

    #Weighted rate based on current tenant lease and duration of the loan
    final_rate = rrate*(1-lease_months/duration) + rate*(lease_months/duration) + i

    return final_rate

    


    

