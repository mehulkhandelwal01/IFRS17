import pandas as pd
import numpy as np

def missing_fields(file):
    #Dealing with NA's 
    file = fillna(file)
    print("inputs have been checked for missing fields and replaced with 0's")
    
    
def validating_signs(file):
    for i in file.loc[file['Key'] == 'MAP003',"Gross_BECFPV"]:
        if i > 1:
            print("Correct Sign for Expected Premiums (MAP003)")
        else:
            print("incorrect Sign for Expected Premiums (MAP003)")
    for i in file.loc[file['Key'] == 'MAP002',"Gross_Actual"]:
        if i > 1:
            print("Correct Sign for Actual Premiums (MAP002)")
        else:
            print("incorrect Sign for Actual Premiums (MAP002)")
    for i in file.loc[file['Key'] == 'MAP012',"Gross_Actual"]:
        if i < 1:
            print("Correct Sign for Actual Cash Outflows (MAP012)")
        else:
            print("Correct Sign for Actual Cash Outflows (MAP012)")
    for i in file.loc[file['Key'] == 'MAP013',"Gross_BECFPV"]:
        if i < 1:
            print("Correct Sign for Expected Cash Outflows (MAP013)")
        else:
            print("incorrect Sign for Expected Cash Outflows (MAP013)")
    for i in file.loc[file['Key'] == 'MAP013',"Gross_RACFPV"]:
        if i < 1:
            print("Correct Sign for Expected Cash Outflows (MAP013)")
        else:
            print("incorrect Sign for Expected Cash Outflows (MAP013)")
    for i in file.loc[file['Key'] == 'MAP015',"Gross_Actual"]:
        if i < 1:
            print("Correct Sign for Actual Insurance Acquisistion CashFlows (MAP015)")
        else:
            print("incorrect Sign for Actual Insurance Acquisistion CashFlows (MAP015)")
    for i in file.loc[file['Key'] == 'MAP016',"Gross_BECFPV"]:
        if i < 1:
            print("Correct Sign for Expected Insurance Acquisistion CashFlows (MAP016)")
        else:
            print("incorrect Sign for Expected Insurance Acquisistion CashFlows (MAP016)")    
    filtered = file.loc[file['Gross_BE'] * file['Gross_RA'] != 0]
    opposite_signs =sum(np.sign(filtered['Gross_BE']) != np.sign(filtered['Gross_RA']))
    print("The dataset has ",opposite_signs,"set of rows where the Gross BE values have opposite signs as compared to Gross RA")

def GWPNBCSM_Check(file):
    data_dict = {
            'assumption_' + str(i): grp
            for i, grp in file.groupby(['Product', 'Sub-Product'])
        }
    for group in data_dict:
        cohort = data_dict[group]
        if parameters.loc[3, "Selection"] == "Input":
            sum = cohort.loc[cohort['Key'] == 'MAP002',"Gross_Actual"].item()+cohort.loc[cohort['Key'] == 'MAP015',"Gross_Actual"].item()+cohort.loc[cohort['Key'] == 'MAP004',"Gross_BE"].item()+cohort.loc[cohort['Key'] == 'MAP004',"Gross_RA"].item()+cohort.loc[cohort['Key'] == 'MAP004',"Gross_LossC_BE"].item()+cohort.loc[cohort['Key'] == 'MAP004',"Gross_LossC_RA"].item()+cohort.loc[cohort['Key'] == 'MAP004',"Gross_CSM"].item()
            if sum == 0:
                print("New business CSM is correct")
            else:
                print("New business CSM is incorrect")
                
        elif parameters.loc[3, "Selection"] == "Calculation":
            print("New Business CSM will be validated after running the model")    