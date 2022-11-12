import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy_financial as npf
import numpy as np
import helper

st.set_option('deprecation.showPyplotGlobalUse', False)
#Title
st.title('Liquid XYZ Data Model V1')

#configs
originationFee = .01
servicingFee = .005
profit = .015

#Fed Funds Rate
#https://fred.stlouisfed.org/series/DFF
#jimmy to add scraping functionality

riskFreeRate = .0233
risk = .035

#Data Inputs
mortgagePayment = []
propertyTaxes = []
propertyInsurance = []
rent = []
tenantLeaseMonths = []
tenantCreditScore = []
tenantIncome = []
lease = []
submit_button = []
property = []
zipCode = []


with st.sidebar:
    st.subheader('Enter Data Below. \n Liquid Loan options will populate')
    with st.form(key='landlord_data'):
        propertyCount = st.number_input('Number of Properties', min_value = 0, value = 0)
        totalLoan = st.number_input('Total Loan Amount', min_value = 5000.00, max_value = 150000.00)
        landlordCreditScore = st.number_input('Landlord Credit Score', value = 0)
        landlordExperience = st.number_input('Months as a Landlord', value = 0)
        ll_submit = st.form_submit_button(label='Submit Borrower Info')

    for i in range(propertyCount):
        with st.form(key='property_data'+str(i)):

            st.write("Property " + str(i+1))
            property = property + [i+1]

            zipCode = zipCode + [st.text_input('Zip Code', value = 00000)]

            mortgagePayment = mortgagePayment + [st.number_input('Total Mortgage Payment', value = 0.00)]

            propertyTaxes = propertyTaxes + [st.number_input('Monthly Property Taxes', value = 0.00)]

            #Add HOA / CONDO Fees

            propertyInsurance = propertyInsurance + [st.number_input('Property Insurance', value = 0.00)]

            rent = rent + [st.number_input('Rental Amount', value = 0.00)]

            tenantLeaseMonths = tenantLeaseMonths + [st.number_input('Month Remaining on Lease', value = 0)]

            tenantCreditScore = tenantCreditScore + [st.number_input('Tenant Credit Score', value = 0)]

            #tenantIncome = tenantIncome + [st.number_input('Monthly Tenant Income', value = 0.00)]

            #lease = lease + [{i,st.file_uploader('Lease(s) Upload', accept_multiple_files=True)}]

            submit_button = submit_button + [st.form_submit_button(label='Submit Property ' + str(i+1))]


#Need the expected value to equal riskFreeRate + service + profit + origination

st.header("Your Info")

df = pd.DataFrame({
    'Property Number': property,
    'Mortgage': mortgagePayment,
    'Taxes': propertyTaxes,
    'Insurance': propertyInsurance,
    'Rent': rent,
    'Lease Months': tenantLeaseMonths,
    'Tenant Credit Score': tenantCreditScore,
    #'Tenant Income': tenantIncome
    })

st.table(df)

#Expense = PITI for now
expenses = sum(df.Mortgage) + sum(df.Taxes) + sum(df.Insurance)

#Revenue
revenues = sum(df.Rent)

#NOI
noi = revenues - expenses


st.header("Liquid Loan Options")
if ll_submit or any(submit_button):
    st.markdown("#### Seeking a \${:,.2f} loan with a current monthly NOI of \${:,.2f}".format(totalLoan, noi))

annual_payments = 12
interest_rate = originationFee + servicingFee + profit + riskFreeRate + risk


#Creating loan products that fit NOI contrainsts
options = []
if all(submit_button):
    for term in [1,1.5,2,2.5,3,3.5,4,4.5,5,5.5]:
        rate = helper.apr(originationFee, servicingFee, term*annual_payments, riskFreeRate, profit, max(df['Tenant Credit Score'],default=600), landlordCreditScore, max(df['Lease Months'],default = 0)) + term*.00833
        pmt = round((npf.pmt(rate/annual_payments, term*annual_payments, totalLoan))*-1,2)
        if pmt < noi:
            options = options + [[term*annual_payments, pmt, rate, totalLoan]]


#Displaying Liquid Loan options
counter = []




for i in options:
    counter = counter + [i]
    col1, col2 = st.columns(2)
    if len(counter) == 0:
        st.write("We do not have any liquid loan options for you due to a low projected NOI")
        st.write("If you are interested in improving your NOI, please condiser our rental portfolio auditing service.")
    
    else:
        with col1:
            st.header("## Option {}".format(len(counter)))
            st.markdown("**Term:** {} months".format(int(i[0])))
            st.markdown("**Rate:** {}%".format(round(i[2]*100,2)))
            st.markdown("**Payments:** ${:,.2f}".format(i[1]))
            st.markdown("**New Estimated NOI:** ${:,.2f}".format(noi - i[1]))
            st.markdown("**Total Interest:** ${:,.2f}".format((i[1]*i[0] - totalLoan)))

        balance = [i[3]]
        month = [0]
        pmt = i[1]
        principal_payment = [0]
        interest_payment = [0]

        for z in range(int(i[0])):
            
            month = month + [z+1]
            
            interest_subcalc = round(balance[-1] * (i[2]/annual_payments),2)
            principal_subcalc = round(pmt - interest_subcalc,2)
            new_balance = round(balance[-1] - principal_subcalc,2)
    
            balance = balance + [new_balance]
            principal_payment = principal_payment + [principal_subcalc]
            interest_payment = interest_payment + [interest_subcalc]

        #fig = plt.plot(month, balance)
        with col2:
            st.header("")
            plt.bar(month, principal_payment, color = '#2b4742ff', label = 'Principal')
            plt.bar(month, interest_payment, bottom=principal_payment, color = 'grey', label = 'Interest')
            plt.xlabel('Month')
            plt.ylabel('$')
            plt.title('Principal and Interest Payments by Month')
            plt.legend(loc='lower right', frameon = True)
            print(interest_payment)
            print(principal_payment)
            st.pyplot()