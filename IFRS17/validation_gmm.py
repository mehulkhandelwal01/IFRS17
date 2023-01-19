import pandas as pd
import numpy as np

class validation:
    def __init__(self, file):
        
    
        def missing_fields(file):
            #Dealing with NA's 
            check = file.drop(file.columns[[3,4]], axis=1, inplace=True)
            count_missing = file.isnull().sum().sum()
            if count_missing == 0:
                print("No Missing Value -- Checked")
            else:
                print(count_missing," Missing Values -- Re-check Inputs")


        def validating_signs(file):
            for i in file.loc[file['Key'] == 'MAP003',"Gross_BECFPV"]:
                if i > 1:
                    print("Correct Sign for Expected Premiums (MAP003) -- Checked")
                else:
                    print("Incorrect Sign for Expected Premiums (MAP003) -- Re-check Inputs")
            for i in file.loc[file['Key'] == 'MAP002',"Gross_Actual"]:
                if i > 1:
                    print("Correct Sign for Actual Premiums (MAP002) -- Checked")
                else:
                    print("Incorrect Sign for Actual Premiums (MAP002) -- Re-check Inputs")
            for i in file.loc[file['Key'] == 'MAP012',"Gross_Actual"]:
                if i < 1:
                    print("Correct Sign for Actual Cash Outflows (MAP012) -- Checked")
                else:
                    print("Incorrect Sign for Actual Cash Outflows (MAP012) -- Re-check Inputs")
            for i in file.loc[file['Key'] == 'MAP013',"Gross_BECFPV"]:
                if i < 1:
                    print("Correct Sign for Expected Cash Outflows (MAP013) -- Checked")
                else:
                    print("Incorrect Sign for Expected Cash Outflows (MAP013) -- Re-check Inputs")
            for i in file.loc[file['Key'] == 'MAP013',"Gross_RACFPV"]:
                if i < 1:
                    print("Correct Sign for Expected Cash Outflows (MAP013) -- Checked")
                else:
                    print("Incorrect Sign for Expected Cash Outflows (MAP013) -- Re-check Inputs")
            for i in file.loc[file['Key'] == 'MAP015',"Gross_Actual"]:
                if i < 1:
                    print("Correct Sign for Actual Insurance Acquisistion CashFlows (MAP015) -- Checked")
                else:
                    print("Incorrect Sign for Actual Insurance Acquisistion CashFlows (MAP015) -- Re-check Inputs")
            for i in file.loc[file['Key'] == 'MAP016',"Gross_BECFPV"]:
                if i < 1:
                    print("Correct Sign for Expected Insurance Acquisistion CashFlows (MAP016) -- Checked")
                else:
                    print("Incorrect Sign for Expected Insurance Acquisistion CashFlows (MAP016) -- Re-check Inputs")    
            filtered = file.loc[file['Gross_BE'] * file['Gross_RA'] != 0]
            opposite_signs =sum(np.sign(filtered['Gross_BE']) != np.sign(filtered['Gross_RA']))
            if opposite_signs == 0:
                print("Correct BEL and RA signage -- Checked")
            else:
                print("The dataset has ",opposite_signs,"set of rows where the Gross BE values have opposite signs as compared to Gross RA -- Re-check Inputs")

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
                        print("New business CSM is correct -- Checked")
                    else:
                        print("New business CSM is incorrect -- Re-Check Inputs")

                elif parameters.loc[3, "Selection"] == "Calculation":
                    print("New Business CSM will be validated after running the model. -- Checked")
        
        missing_fields(file)
        validating_signs(file)
        GWPNBCSM_Check(file)
        
    