import math
from urllib.parse import SplitResult 
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import skewnorm
import matplotlib.pyplot as plt
from scipy.stats import bernoulli
import numpy_financial as npf


#define applicant size (about 45% will get approval so # of loans = .45* n)

st.title('Liquid Loan Book Simulation')

n=st.number_input('Total Loan Applicants', value = 20000)

#Run Sim Function

#Landlord Credit Score Function
def ll_cs():
    maxValue = 850
    minValue = 350
    skewness = -2.5
    random = skewnorm.rvs(a = skewness,loc=maxValue, size=100)

    random = random - min(random)    
    random = random / max(random)    
    random = random * minValue     
    random = random + (maxValue-minValue)      

    return int(random[20])

# Number of Tenants per landlord
def tenants():
    return math.ceil(np.random.gamma(1.25, .5))


#Credit Score or each tenant
def tenant_credit(n):
    tc = []
    for i in range(n):
        tc = tc + [math.floor(np.random.lognormal(6.35, .107))]
    return tc

#Tenant's rental payment history
def tc_history(tc):
    hist = []
    for f in tc:
        if f < 599:
            r = bernoulli.rvs(.35)
        elif f < 699:
            r = bernoulli.rvs(.50)
        elif f < 799:
            r = bernoulli.rvs(.75)
        else:
            r = bernoulli.rvs(.95)
        hist = hist + [r]
    return hist


#Tenant Probability of Default on 1 year lease
def tpd(th,tcs):
# Good Rental History 
    ten_df = []
    for x,y in zip(th,tcs):
        if x == 1:
            if y < 599:
                pd = .1496
            elif y < 699:
                pd = .0592
            elif y < 799:
                pd = .0176
            else:
                pd = .0065
    #Bad Rental History 
        else:
            if y < 599:
                pd = .2923
            elif y < 699:
                pd = .1822
            elif y < 799:
                pd = .0731
            else:
                pd = .0370
        ten_df = ten_df + [pd]
    return ten_df


#Landlord Probability default on 24 month loan
def lpd(lcs):
    
    if lcs < 550:
        pd = .351
    elif lcs < 599:
        pd = .277
    elif lcs < 699:
        pd = .141
    elif lcs < 799:
        pd = .052
    else:
        pd = .012
    
    return pd

def flatten(l):
    flat_avg = []
    for i in l:
        flat_avg = flat_avg + [(np.array(i).mean())]

def loan():
    return int(np.random.gamma(9,2300)/100) *100

def NOI():
    return round(np.random.gamma(3, 190),2)

def apr(origination_fee, servicing_fee, capital_cost, profit):
    return ((origination_fee +  servicing_fee + capital_cost + profit))

def monthly_payment(rate,term,loan):
    return(round((npf.pmt(rate/12, term*12, loan))*-1,2))

def duration():
    return(round(np.random.gamma(2.8, 1.2),0))

def vacancy():
    return(np.random.lognormal(1.2, .5)/100)

#Landlords and Tenants 
tenant_count = []
landlord_credit_score = []
tenant_cs = []
tenant_default = []
landlord_default = []
hist = []
landlordid = list(range(1,n+1))
all_tenant_default = []
noi = []
lldf = []
loanamount = []
loan_duration = []
payment = []
mpmt = []
vacancy_rate = []
st.header('Configs')
origination_fee = st.number_input('Origination Fee', .015)
servicing_fee = st.number_input('Servicing Fee', .015)
capital_cost = st.number_input('Capital Costs', .025)
#BAse and Margin
profit = st.number_input('Profit', .015)
default_multiplier = st.number_input('Landlord Default Multiplier', 2.85)



b = st.button('Run Simulation')


if b:
    print('Simulation starting for {} applicants'.format(n))
    st.write('Simulation starting for {} applicants'.format(n))
    for i in range(n):
        
        tenant_count = tenant_count + [tenants()]
        landlord_credit_score = landlord_credit_score + [ll_cs()]
        noi = noi + [NOI()]
        loanamount = loanamount + [loan()]
        loan_duration = loan_duration + [duration()]
        vacancy_rate = vacancy_rate + [vacancy()]
        

    for i in tenant_count:
        tenant_cs = tenant_cs + [tenant_credit(i)]
        
    for i in tenant_cs:
        hist = hist + [tc_history(i)]

    for i in landlord_credit_score:
        lldf = lldf + [lpd(i)]

    for i,z in zip(hist,tenant_cs):
        tenant_default = tenant_default + [tpd(i,z)]

    for i in tenant_default:
        all_tenant_default = all_tenant_default + [np.prod(np.array(i))]

    for i,z in zip(loan_duration,loanamount):
        rate = apr(origination_fee, servicing_fee, capital_cost, profit)
        mpmt = mpmt + [monthly_payment(rate,i,z)]


    df = pd.DataFrame({
        'LandlordID': landlordid,
        'Tenants': tenant_count,
        'Tenant Credit': tenant_cs,
        'Tenant History': hist, 
        'Tenant Default': tenant_default,
        'Tenant Combined Default': all_tenant_default,
        'Landlord Credit Score': landlord_credit_score,
        'Landlord Default': lldf,
        'NOI': noi,
        'Loan': loanamount,
        'Duration': loan_duration,
        'Vacancy Rate': vacancy_rate,
        'Monthly Payment': mpmt
        #'Tenant Income': tenantIncome
        })
    #Format everything to whole numbers where applicable, group important columns together. 

    df['Eligibility'] = np.where(df['NOI'] - df['Monthly Payment'] >= 0, 1,0)

    #Filter to applicants who have NOI greater than monthly payment
    data = df[df['Eligibility'] ==1]

    data['Monthly PD vw'] = (((data['Tenant Combined Default']/12) * (data['Landlord Default']*default_multiplier) / 24)*(1-data['Vacancy Rate'])) + (data['Landlord Default'] / 24 * data['Vacancy Rate']) 

    data['Monthly LL PD'] = data['Landlord Default'] / 24

    data['Month Duration'] = data['Duration']*12


    #Liquid Loan
    payments = []
    total_payments = []
    for x,y,z in zip(data['Monthly PD vw'],data['Monthly Payment'],data['Month Duration']):
        payment = []
        total_payment=0
        for i in range(int(z)):
            p = bernoulli.rvs(1-(x))*y
            if p==0:break
            else:
                payment = payment + [p]
                total_payment += p
        payments = payments + [payment]
        total_payments = total_payments + [total_payment]
        
        
    paymentsll = []
    total_paymentsll = []

    #Personal Loan
    for x,y,z in zip(data['Monthly LL PD'],data['Monthly Payment'],data['Month Duration']):
        paymentll = []
        total_paymentll=0
        for i in range(int(z)):
            p = bernoulli.rvs(1-(x))*y
            if p==0:break
            else:
                paymentll = paymentll + [p]
                total_paymentll += p
        paymentsll = paymentsll + [paymentll]
        total_paymentsll = total_paymentsll + [total_paymentll]


        
        
    data['liquid loan payments'] = payments
    data['total_payments'] = total_payments
    data['expected payment'] = data['Month Duration'] * data['Monthly Payment']

    data['payments_personal_loan'] = paymentsll
    data['total_payments_personal_loan'] = total_paymentsll

    data['Liquid Loan Repayment Percentage'] = data['total_payments']/data['expected payment']
    data['Personal Loan Repayment Percentage'] = data['total_payments_personal_loan']/data['expected payment']
    data['Expected Loss LL'] = (data['total_payments'] - data['expected payment'])/data['expected payment']
    data['Expected Loss PL'] = (data['total_payments_personal_loan'] - data['expected payment'])/data['expected payment']
    data['credit_score_groups'] = pd.cut(df['Landlord Credit Score'],bins=[0,550,599,699,799,850],labels=['<550','550-599','600-699','700-799','800+'],ordered=True)
   
    LLIRR = []
    for x,y in zip(data.Loan, data['liquid loan payments']):
        c = [-x] + y
        irr = round(npf.irr(c),4)*1200
        LLIRR = LLIRR + [irr]

    data['LLIRR'] = LLIRR
    
    PLIRR = []
    for x,y in zip(data.Loan, data['payments_personal_loan']):
        c = [-x] + y
        irr = round(npf.irr(c),4)*1200
        PLIRR = PLIRR + [irr]

    data['PLIRR'] = PLIRR



    st.write('Simulation Finished')
    st.subheader('Summary Output')
    st.write('Loan Book: ${:,.2f}'.format(round(data.Loan.sum(),2)))
    st.write('Average Applicant Credit Score: {}'.format(int(data['Landlord Credit Score'].mean())))
    st.write('Average Loan Amount: ${:,.2f}'.format(data.Loan.mean()))
    st.write('Average Number of Tenants per Landlord: {}'.format(round(data.Tenants.mean(),4)))
    st.subheader('Risk Differentiation')
    st.write('Liquid Loans Expected Loss: {}%'.format(round(1-(data['total_payments'].sum()/data['expected payment'].sum()),4)*100))
    st.write('Personal Loans Expected Loss: {}%'.format(round(1-(data['total_payments_personal_loan'].sum()/data['expected payment'].sum()),4)*100))

    

    fig, ax = plt.subplots()
    polyline = np.linspace(500, 850, 100)
    ax.scatter(data.groupby(by = ['Landlord Credit Score']).mean().reset_index()['Landlord Credit Score'], data.groupby(by = ['Landlord Credit Score']).mean().reset_index()['Expected Loss LL'], alpha = .15, color = 'darkblue', label = 'Liquid Loan')
    a = np.poly1d(np.polyfit(data.groupby(by = ['Landlord Credit Score']).mean().reset_index()['Landlord Credit Score'], data.groupby(by = ['Landlord Credit Score']).mean().reset_index()['Expected Loss LL'], 2))
    plt.plot(polyline, a(polyline), color='blue')
    ax.scatter(data.groupby(by = ['Landlord Credit Score']).mean().reset_index()['Landlord Credit Score'], data.groupby(by = ['Landlord Credit Score']).mean().reset_index()['Expected Loss PL'], alpha = .15, color = 'darkgreen', label = 'Personal Loan')
    c = np.poly1d(np.polyfit(data.groupby(by = ['Landlord Credit Score']).mean().reset_index()['Landlord Credit Score'], data.groupby(by = ['Landlord Credit Score']).mean().reset_index()['Expected Loss PL'], 2))
    plt.plot(polyline, c(polyline), color='green')
    plt.fill_between(polyline,a(polyline), c(polyline), color='grey', alpha=0.2, label = 'Risk Difference')
    ax.legend()
    ax.title.set_text('Expected Loss % Comparison: Liquid Loans vs Personal Loans')
    ax.set_xlabel('Applicant Credit Score')
    ax.set_ylabel('Expect Loss as % of Expected Payment')
    st.pyplot(fig)


    st.table(data)