import pandas as pd
import numpy as np
from functools import reduce
import os
from os import path
from datetime import datetime
from dateutil import relativedelta
from csv import writer


class GMM:

    def __init__(self, assumptions, parameters):
        data = pd.pivot_table(
            assumptions,
            index=['Cohort', 'Product', 'Sub-Product', 'Key'],
            aggfunc={
                'Gross_BE': 'sum',
                'Gross_LossC_BE': 'sum',
                'Gross_RA': 'sum',
                'Gross_LossC_RA': 'sum',
                'Gross_CSM': 'sum',
                'Gross_BECFPV': 'sum',
                'Gross_RACFPV': 'sum',
                'Gross_Actual': 'sum'
            })

        data = data.reset_index()

        data_dict = {
            'assumption_' + str(i): grp
            for i, grp in data.groupby(['Product', 'Sub-Product'])
        }

        def iferror(y):
            if len(y.index) == 0:
                return 0
            else:
                return y.item()

        self.Parameters = parameters

        inception = datetime.strptime(self.Parameters.loc[0, "Selection"],
                                      '%d/%m/%Y').year
        start = datetime.strptime(self.Parameters.loc[1, "Selection"],
                                  '%d/%m/%Y').year
        end = datetime.strptime(self.Parameters.loc[2, "Selection"],
                                '%d/%m/%Y').year
        self.BEL = []
        self.RA = []
        self.CSM = []
        self.TCL = []     
        self.AMC = []
        self.ARC = []

        count = 0
        for group in data_dict:
            cohort1 = data_dict[group]
            product_name = cohort1['Product'].unique().item()
            subproduct_name = cohort1['Sub-Product'].unique().item()

            self.Assumptions = cohort1

            self.Liability_on_Initial_Recognition = pd.DataFrame(
                data=0,
                index=range(start, end + 1),
                columns=[
                    "PV Premium", "PV Claims", "PV Risk Adjustment",
                    "PV Acquisition Expense", "CSM at Initial Recognition",
                    "LIABILITY ON INITIAL RECOGNITION-BE",
                    "LIABILITY ON INITIAL RECOGNITION-RA"
                ])
            self.Reconciliation_of_Best_Estimate_Liability = pd.DataFrame(
                data=0,
                index=range(start, end + 1),
                columns=[
                    "Product", "Sub-Product", "Opening Balance",
                    "Changes Related to Future Service: New Business",
                    "Changes Related to Future Service: Assumptions",
                    "Insurance Service Expense",
                    "Changes Related to Current Service: Experience",
                    "Changes Related to Current Service: Release",
                    "Changes Related to Past Service", "Closing Balance"
                ])
            self.Reconciliation_of_Best_Estimate_Liability.index.name = 'Period'
            self.Reconciliation_of_Risk_Adjustment = self.Reconciliation_of_Best_Estimate_Liability.copy(
            )
            self.Reconciliation_of_Total_Contract_Liability = self.Reconciliation_of_Best_Estimate_Liability.copy(
            )
            self.Reconciliation_of_Contractual_Service_Margin = self.Reconciliation_of_Best_Estimate_Liability.copy(
            )

            measure_abmc = [
                "Present value of future cash flows", "Risk Adjustment",
                "Contractual Service Margin", "Total"
            ]

            self.Analysis_by_measurement_component = pd.DataFrame(
                data=0,
                index=[0],
                columns=[
                    "Period",
                    "Product",
                    "Sub-Product",
                    "Measure",
                    'Net balance at 1 January',
                    'CSM recognised in profit or loss for the services provided',
                    'Risk Adjustment recognised for the risk expired',
                    'Experience adjustments',
                    'Changes that relate to current service',
                    'Changes in estimates that adjust the CSM',
                    'Changes in estimates that result in onerous contract losses or reversal of losses',
                    'Contracts initially recognised in the period',
                    'Changes that relate to future service',
                    'Adjustments to liabilities for incurred claims',
                    'Changes that relate to past service',
                    'Insurance service result',
                    'Finance expenses from insurance contracts issued',
                    'Effects of movements in exchange rates',
                    'Investment Component and Premium Refund',
                    'Total recognised in comprehensive income',
                    'Premiums received',
                    'Claims and other directly attributable expenses paid',
                    'Insurance acquisition cash flows',
                    'Total cash flows',
                    'Net balance at 31 December',
                ])
            measure_abrc = [
                "Liabilities for remaining coverage - Excluding loss component",
                "Liabilities for remaining coverage - Only Loss Component",
                "Liabilities for incurred claims", "Total"
            ]

            self.Analysis_by_remaining_coverage = pd.DataFrame(
                data=0,
                index=[0],
                columns=[
                    "Period", "Product", "Sub-Product", "Measure",
                    'Net balance at 1 January',
                    'Changes in the statement of profit and loss and OCI',
                    'Contracts under the modified retrospective transition approach',
                    'Contracts under the fair value transition approach',
                    'Other contracts',
                    'Expected incurred claims and other insurance services expenses',
                    'Amortisation of insurance acquisition cash flows',
                    'Losses and reversals of losses on onerous contracts',
                    'Adjustments to liabilities for incurred claims',
                    'Insurance service result',
                    'Net finance expenses from insurance contracts',
                    'Effect of movement in exchange rates',
                    'Investment components and premium refunds',
                    'Total changes in the statement of profit and loss and OCI',
                    'Premiums received',
                    'Claims and other insurance services expenses paid, including investment components',
                    'Insurance acquisition cash flows', 'Total cash flows',
                    'Transfer to other items in the statement of financial position',
                    'Net balance at 31 December'
                ])

            # Liability on Initial Recognition

            if self.Parameters.loc[3, "Selection"] == "Input":

                self.Liability_on_Initial_Recognition.loc[
                    inception, "CSM at Initial Recognition"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP004') &
                            (self.Assumptions['Cohort'] == inception),
                            'Gross_CSM'])
                self.Liability_on_Initial_Recognition.loc[
                    inception,
                    "LIABILITY ON INITIAL RECOGNITION-BE"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP004') &
                            (self.Assumptions['Cohort'] == inception),
                            'Gross_LossC_BE'])
                self.Liability_on_Initial_Recognition.loc[
                    inception,
                    "LIABILITY ON INITIAL RECOGNITION-RA"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP004') &
                            (self.Assumptions['Cohort'] == inception),
                            'Gross_LossC_RA'])

            elif self.Parameters.loc[3, "Selection"] == "Calculation":

                self.Liability_on_Initial_Recognition.loc[
                    inception, "PV Premium"] = iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP003') &
                        (self.Assumptions['Cohort'] == inception),
                        'Gross_BECFPV'])
                self.Liability_on_Initial_Recognition.loc[
                    inception, "PV Claims"] = iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == inception),
                        'Gross_BECFPV'])
                self.Liability_on_Initial_Recognition.loc[
                    inception,
                    "PV Risk Adjustment"] = iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == inception),
                        'Gross_RACFPV'])
                self.Liability_on_Initial_Recognition.loc[
                    inception,
                    "PV Acquisition Expense"] = iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP016') &
                        (self.Assumptions['Cohort'] == inception),
                        'Gross_BECFPV'])
                Total = self.Liability_on_Initial_Recognition.loc[
                    inception,
                    "PV Premium"] + self.Liability_on_Initial_Recognition.loc[
                        inception,
                        "PV Claims"] + self.Liability_on_Initial_Recognition.loc[
                            inception,
                            "PV Risk Adjustment"] + self.Liability_on_Initial_Recognition.loc[
                                inception, "PV Acquisition Expense"]

                if Total > 0:
                    self.Liability_on_Initial_Recognition.loc[
                        inception, "CSM at Initial Recognition"] = Total
                    self.Liability_on_Initial_Recognition.loc[
                        inception, "LIABILITY ON INITIAL RECOGNITION-BE"] = 0
                    self.Liability_on_Initial_Recognition.loc[
                        inception, "LIABILITY ON INITIAL RECOGNITION-RA"] = 0

                else:
                    self.Liability_on_Initial_Recognition.loc[
                        inception, "CSM at Initial Recognition"] = 0
                    self.Liability_on_Initial_Recognition.loc[
                        inception,
                        "LIABILITY ON INITIAL RECOGNITION-BE"] = (Total * (
                            (iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP013') &
                                (self.Assumptions['Cohort'] == inception),
                                'Gross_BECFPV'])) /
                            (iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP013') &
                                (self.Assumptions['Cohort'] == inception),
                                'Gross_BECFPV']) +
                             iferror(self.Assumptions.loc[
                                 (self.Assumptions['Key'] == 'MAP013') &
                                 (self.Assumptions['Cohort'] == inception),
                                 'Gross_RACFPV']))))
                    self.Liability_on_Initial_Recognition.loc[
                        inception,
                        "LIABILITY ON INITIAL RECOGNITION-RA"] = (Total * (
                            (iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP013') &
                                (self.Assumptions['Cohort'] == inception),
                                'Gross_RACFPV'])) /
                            (iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP013') &
                                (self.Assumptions['Cohort'] == inception),
                                'Gross_BECFPV']) +
                             iferror(self.Assumptions.loc[
                                 (self.Assumptions['Key'] == 'MAP013') &
                                 (self.Assumptions['Cohort'] == inception),
                                 'Gross_RACFPV']))))

            # Reconciliation of Best Estimate Liability

            for i in range(start, end + 1):
                if i == inception:
                    self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Opening Balance"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                            i - 1, "Closing Balance"]
                    if self.Liability_on_Initial_Recognition.loc[
                            i, "LIABILITY ON INITIAL RECOGNITION-BE"] == 0:
                        self.Reconciliation_of_Best_Estimate_Liability.loc[
                            i,
                            "Changes Related to Future Service: New Business"] = iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP013') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_BECFPV'])
                    else:
                        self.Reconciliation_of_Best_Estimate_Liability.loc[
                            i,
                            "Changes Related to Future Service: New Business"] = self.Liability_on_Initial_Recognition.loc[
                                inception,
                                "LIABILITY ON INITIAL RECOGNITION-BE"]
                elif i == start:
                    self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i, "Opening Balance"] = 0
                else:
                    self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Opening Balance"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                            i - 1, "Closing Balance"]
                    self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Changes Related to Future Service: New Business"] = 0

                self.Reconciliation_of_Best_Estimate_Liability.loc[
                    i, "Product"] = product_name
                self.Reconciliation_of_Best_Estimate_Liability.loc[
                    i, "Sub-Product"] = subproduct_name

                self.Reconciliation_of_Best_Estimate_Liability.loc[
                    i,
                    "Changes Related to Future Service: Assumptions"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i), 'Gross_BE']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP001') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_LossC_BE']) + iferror(
                            self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i), 'Gross_BE']
                        ) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP005') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP006') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_BE']) + iferror(
                                    self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP006') &
                                        (self.Assumptions['Cohort'] == i),
                                        'Gross_LossC_BE']
                                ) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP008') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_BE']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP008') &
                                            (self.Assumptions['Cohort'] == i),
                                            'Gross_LossC_BE']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP009') &
                                        (self.Assumptions['Cohort'] == i),
                                        'Gross_BE']) + iferror(
                                            self.Assumptions.loc[
                                                (self.Assumptions['Key'] ==
                                                 'MAP009') &
                                                (self.Assumptions['Cohort'] ==
                                                 i), 'Gross_LossC_BE']
                                        ) + iferror(
                                            self.Assumptions.loc[
                                                (self.Assumptions['Key'] ==
                                                 'MAP011') &
                                                (self.Assumptions['Cohort'] ==
                                                 i), 'Gross_BE']
                                        ) + iferror(self.Assumptions.loc[
                                            (self.
                                             Assumptions['Key'] == 'MAP011') &
                                            (self.Assumptions['Cohort'] == i),
                                            'Gross_LossC_BE']) + iferror(
                                                self.Assumptions.loc[
                                                    (self.Assumptions['Key'] ==
                                                     'MAP018') &
                                                    (self.Assumptions['Cohort']
                                                     == i), 'Gross_BE']
                                            ) + iferror(self.Assumptions.loc[
                                                (self.Assumptions['Key'] ==
                                                 'MAP018') &
                                                (self.Assumptions['Cohort'] ==
                                                 i), 'Gross_LossC_BE'])
                self.Reconciliation_of_Best_Estimate_Liability.loc[
                    i, "Insurance Service Expense"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP007') &
                            (self.Assumptions['Cohort'] == i), 'Gross_BE']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP007') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP010') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP010') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_LossC_BE'])
                self.Reconciliation_of_Best_Estimate_Liability.loc[
                    i,
                    "Changes Related to Current Service: Release"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP013') &
                            (self.Assumptions['Cohort'] == i), 'Gross_BE']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP014') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP014') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_LossC_BE'])
                self.Reconciliation_of_Best_Estimate_Liability.loc[
                    i, "Changes Related to Past Service"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP017') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP017') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_LossC_BE'])
                self.Reconciliation_of_Best_Estimate_Liability.loc[
                    i,
                    "Closing Balance"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Opening Balance"] + self.Reconciliation_of_Best_Estimate_Liability.loc[
                            i,
                            "Changes Related to Future Service: New Business"] + self.Reconciliation_of_Best_Estimate_Liability.loc[
                                i,
                                "Changes Related to Future Service: Assumptions"] + self.Reconciliation_of_Best_Estimate_Liability.loc[
                                    i,
                                    "Insurance Service Expense"] + self.Reconciliation_of_Best_Estimate_Liability.loc[
                                        i,
                                        "Changes Related to Current Service: Release"] + self.Reconciliation_of_Best_Estimate_Liability.loc[
                                            i,
                                            "Changes Related to Past Service"] + self.Reconciliation_of_Best_Estimate_Liability.loc[
                                                i,
                                                "Changes Related to Current Service: Experience"]

            # Reconciliation of Risk Adjustment

            for i in range(start, end + 1):
                if i == inception:
                    self.Reconciliation_of_Risk_Adjustment.loc[
                        i,
                        "Opening Balance"] = self.Reconciliation_of_Risk_Adjustment.loc[
                            i - 1, "Closing Balance"]
                    if self.Liability_on_Initial_Recognition.loc[
                            i, "LIABILITY ON INITIAL RECOGNITION-RA"] == 0:
                        self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Changes Related to Future Service: New Business"] = iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP013') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_RACFPV'])
                    else:
                        self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Changes Related to Future Service: New Business"] = self.Liability_on_Initial_Recognition.loc[
                                start, "LIABILITY ON INITIAL RECOGNITION-RA"]
                elif i == start:
                    self.Reconciliation_of_Risk_Adjustment.loc[
                        i, "Opening Balance"] = 0

                else:
                    self.Reconciliation_of_Risk_Adjustment.loc[
                        i,
                        "Opening Balance"] = self.Reconciliation_of_Risk_Adjustment.loc[
                            i - 1, "Closing Balance"]
                    self.Reconciliation_of_Risk_Adjustment.loc[
                        i,
                        "Changes Related to Future Service: New Business"] = 0

                self.Reconciliation_of_Risk_Adjustment.loc[
                    i, "Product"] = product_name
                self.Reconciliation_of_Risk_Adjustment.loc[
                    i, "Sub-Product"] = subproduct_name

                self.Reconciliation_of_Risk_Adjustment.loc[
                    i,
                    "Changes Related to Future Service: Assumptions"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i), 'Gross_RA']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP001') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_LossC_RA']) + iferror(
                            self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i), 'Gross_RA']
                        ) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP005') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_RA']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP006') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_RA']) + iferror(
                                    self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP006') &
                                        (self.Assumptions['Cohort'] == i),
                                        'Gross_LossC_RA']
                                ) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP008') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_RA']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP008') &
                                            (self.Assumptions['Cohort'] == i),
                                            'Gross_LossC_RA']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP009') &
                                        (self.Assumptions['Cohort'] == i),
                                        'Gross_RA']) + iferror(
                                            self.Assumptions.loc[
                                                (self.Assumptions['Key'] ==
                                                 'MAP009') &
                                                (self.Assumptions['Cohort'] ==
                                                 i), 'Gross_LossC_RA']
                                        ) + iferror(
                                            self.Assumptions.loc[
                                                (self.Assumptions['Key'] ==
                                                 'MAP011') &
                                                (self.Assumptions['Cohort'] ==
                                                 i), 'Gross_RA']
                                        ) + iferror(self.Assumptions.loc[
                                            (self.
                                             Assumptions['Key'] == 'MAP011') &
                                            (self.Assumptions['Cohort'] == i),
                                            'Gross_LossC_RA']) + iferror(
                                                self.Assumptions.loc[
                                                    (self.Assumptions['Key'] ==
                                                     'MAP018') &
                                                    (self.Assumptions['Cohort']
                                                     == i), 'Gross_RA']
                                            ) + iferror(self.Assumptions.loc[
                                                (self.Assumptions['Key'] ==
                                                 'MAP018') &
                                                (self.Assumptions['Cohort'] ==
                                                 i), 'Gross_LossC_RA'])
                self.Reconciliation_of_Risk_Adjustment.loc[
                    i, "Insurance Service Expense"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP007') &
                            (self.Assumptions['Cohort'] == i), 'Gross_RA']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP007') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_LossC_RA']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP010') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_RA']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP010') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_LossC_RA'])
                self.Reconciliation_of_Risk_Adjustment.loc[
                    i,
                    "Changes Related to Current Service: Release"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP013') &
                            (self.Assumptions['Cohort'] == i), 'Gross_RA']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_LossC_RA']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP014') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_RA']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP014') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_LossC_RA'])
                self.Reconciliation_of_Risk_Adjustment.loc[
                    i, "Changes Related to Past Service"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP017') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_RA']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP017') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_LossC_RA'])
                self.Reconciliation_of_Risk_Adjustment.loc[
                    i,
                    "Closing Balance"] = self.Reconciliation_of_Risk_Adjustment.loc[
                        i,
                        "Opening Balance"] + self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Changes Related to Future Service: New Business"] + self.Reconciliation_of_Risk_Adjustment.loc[
                                i,
                                "Changes Related to Future Service: Assumptions"] + self.Reconciliation_of_Risk_Adjustment.loc[
                                    i,
                                    "Insurance Service Expense"] + self.Reconciliation_of_Risk_Adjustment.loc[
                                        i,
                                        "Changes Related to Current Service: Release"] + self.Reconciliation_of_Risk_Adjustment.loc[
                                            i,
                                            "Changes Related to Past Service"] + self.Reconciliation_of_Risk_Adjustment.loc[
                                                i,
                                                "Changes Related to Current Service: Experience"]

            # Reconciliation of Contractual Service Margin

            for i in range(start, end + 1):
                if i == inception:
                    self.Reconciliation_of_Contractual_Service_Margin.loc[
                        i,
                        "Opening Balance"] = self.Reconciliation_of_Contractual_Service_Margin.loc[
                            i - 1, "Closing Balance"]
                    self.Reconciliation_of_Contractual_Service_Margin.loc[
                        i,
                        "Changes Related to Future Service: New Business"] = iferror(
                            -(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP004')
                                & (self.Assumptions['Cohort'] == i),
                                'Gross_CSM']))
                elif i == start:
                    self.Reconciliation_of_Contractual_Service_Margin.loc[
                        i, "Opening Balance"] = 0

                else:
                    self.Reconciliation_of_Contractual_Service_Margin.loc[
                        i,
                        "Opening Balance"] = self.Reconciliation_of_Contractual_Service_Margin.loc[
                            i - 1, "Closing Balance"]
                    self.Reconciliation_of_Contractual_Service_Margin.loc[
                        i,
                        "Changes Related to Future Service: New Business"] = 0

                self.Reconciliation_of_Contractual_Service_Margin.loc[
                    i, "Product"] = product_name
                self.Reconciliation_of_Contractual_Service_Margin.loc[
                    i, "Sub-Product"] = subproduct_name

                self.Reconciliation_of_Contractual_Service_Margin.loc[
                    i, "Changes Related to Future Service: Assumptions"] = -(
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP005') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP006') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP008') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP009') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP011') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP018') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']))
                self.Reconciliation_of_Contractual_Service_Margin.loc[
                    i, "Insurance Service Expense"] = -(
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP007') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP010') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']))
                self.Reconciliation_of_Contractual_Service_Margin.loc[
                    i, "Changes Related to Current Service: Release"] = -(
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP013') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP014') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']))
                self.Reconciliation_of_Contractual_Service_Margin.loc[
                    i, "Changes Related to Past Service"] = -(iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP017') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']))
                self.Reconciliation_of_Contractual_Service_Margin.loc[
                    i,
                    "Closing Balance"] = self.Reconciliation_of_Contractual_Service_Margin.loc[
                        i,
                        "Opening Balance"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                            i,
                            "Changes Related to Future Service: New Business"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                i,
                                "Changes Related to Future Service: Assumptions"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                    i,
                                    "Insurance Service Expense"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                        i,
                                        "Changes Related to Current Service: Release"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                            i,
                                            "Changes Related to Past Service"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                                i,
                                                "Changes Related to Current Service: Experience"]

            # Reconciliation of Total Contract Liability

            for i in range(start, end + 1):
                self.Reconciliation_of_Total_Contract_Liability.loc[
                    i, "Product"] = product_name
                self.Reconciliation_of_Total_Contract_Liability.loc[
                    i, "Sub-Product"] = subproduct_name
                self.Reconciliation_of_Total_Contract_Liability.loc[
                    i,
                    "Opening Balance"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Opening Balance"] + self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Opening Balance"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                i, "Opening Balance"]
                self.Reconciliation_of_Total_Contract_Liability.loc[
                    i,
                    "Changes Related to Future Service: New Business"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Changes Related to Future Service: New Business"] + self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Changes Related to Future Service: New Business"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                i,
                                "Changes Related to Future Service: New Business"]
                self.Reconciliation_of_Total_Contract_Liability.loc[
                    i,
                    "Changes Related to Future Service: Assumptions"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Changes Related to Future Service: Assumptions"] + self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Changes Related to Future Service: Assumptions"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                i,
                                "Changes Related to Future Service: Assumptions"]
                self.Reconciliation_of_Total_Contract_Liability.loc[
                    i,
                    "Insurance Service Expense"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Insurance Service Expense"] + self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Insurance Service Expense"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                i, "Insurance Service Expense"]
                self.Reconciliation_of_Total_Contract_Liability.loc[
                    i,
                    "Changes Related to Current Service: Release"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Changes Related to Current Service: Release"] + self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Changes Related to Current Service: Release"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                i,
                                "Changes Related to Current Service: Release"]
                self.Reconciliation_of_Total_Contract_Liability.loc[
                    i,
                    "Changes Related to Past Service"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Changes Related to Past Service"] + self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Changes Related to Past Service"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                i, "Changes Related to Past Service"]
                self.Reconciliation_of_Total_Contract_Liability.loc[
                    i,
                    "CLOSING"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                        i,
                        "Closing Balance"] + self.Reconciliation_of_Risk_Adjustment.loc[
                            i,
                            "Closing Balance"] + self.Reconciliation_of_Contractual_Service_Margin.loc[
                                i, "Closing Balance"]

            # Analysis by measurement Component

            for i in range(start, end + 1):
                for s in measure_abmc:
                    entry = pd.DataFrame(
                        {
                            'Period':
                            i,
                            "Product":
                            product_name,
                            "Sub-Product":
                            subproduct_name,
                            'Measure':
                            s,
                            'Net balance at 1 January':
                            0,
                            'CSM recognised in profit or loss for the services provided':
                            0,
                            'Risk Adjustment recognised for the risk expired':
                            0,
                            'Experience adjustments':
                            0,
                            'Changes that relate to current service':
                            0,
                            'Changes in estimates that adjust the CSM':
                            0,
                            'Changes in estimates that result in onerous contract losses or reversal of losses':
                            0,
                            'Contracts initially recognised in the period':
                            0,
                            'Changes that relate to future service':
                            0,
                            'Adjustments to liabilities for incurred claims':
                            0,
                            'Changes that relate to past service':
                            0,
                            'Insurance service result':
                            0,
                            'Finance expenses from insurance contracts issued':
                            0,
                            'Effects of movements in exchange rates':
                            0,
                            'Investment Component and Premium Refund':
                            0,
                            'Total recognised in comprehensive income':
                            0,
                            'Premiums received':
                            0,
                            'Claims and other directly attributable expenses paid':
                            0,
                            'Insurance acquisition cash flows':
                            0,
                            'Total cash flows':
                            0,
                            'Net balance at 31 December':
                            0
                        },
                        index=[0])
                    if count == 0:
                        self.Analysis_by_measurement_component = entry
                    else:
                        self.Analysis_by_measurement_component = pd.concat(
                            [self.Analysis_by_measurement_component, entry],
                            axis=0)
                    count += 1

                if i == start:
                    self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Present value of future cash flows"),
                        "Net balance at 1 January"] = 0
                    self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"), "Net balance at 1 January"] = 0
                    self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Contractual Service Margin"),
                        "Net balance at 1 January"] = 0
                    self.Analysis_by_measurement_component.loc[(
                        self.Analysis_by_measurement_component['Period'] == i
                    ) & (
                        self.Analysis_by_measurement_component['Measure'] ==
                        "Total"
                    ), "Net balance at 1 January"] = self.Analysis_by_measurement_component.loc[(
                        self.Analysis_by_measurement_component['Period'] == i
                    ) & (
                        self.Analysis_by_measurement_component['Measure'] ==
                        "Present value of future cash flows"
                    ), "Net balance at 1 January"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Net balance at 1 January"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Net balance at 1 January"]
                else:
                    self.Analysis_by_measurement_component.loc[(
                        self.Analysis_by_measurement_component['Period'] == i
                    ) & (
                        self.Analysis_by_measurement_component['Measure'] ==
                        "Present value of future cash flows"
                    ), "Net balance at 1 January"] = self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] ==
                         i - 1) &
                        (self.Analysis_by_measurement_component['Measure'] ==
                         "Present value of future cash flows"),
                        "Net balance at 31 December"]
                    self.Analysis_by_measurement_component.loc[(
                        self.Analysis_by_measurement_component['Period'] == i
                    ) & (
                        self.Analysis_by_measurement_component['Measure'] ==
                        "Risk Adjustment"
                    ), "Net balance at 1 January"] = self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] ==
                         i - 1) &
                        (self.Analysis_by_measurement_component['Measure'] ==
                         "Risk Adjustment"), "Net balance at 31 December"]
                    self.Analysis_by_measurement_component.loc[(
                        self.Analysis_by_measurement_component['Period'] == i
                    ) & (
                        self.Analysis_by_measurement_component['Measure'] ==
                        "Contractual Service Margin"
                    ), "Net balance at 1 January"] = self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] ==
                         i - 1) &
                        (self.Analysis_by_measurement_component['Measure'] ==
                         "Contractual Service Margin"),
                        "Net balance at 31 December"]
                    self.Analysis_by_measurement_component.loc[(
                        self.Analysis_by_measurement_component['Period'] == i
                    ) & (
                        self.Analysis_by_measurement_component['Measure'] ==
                        "Total"
                    ), "Net balance at 1 January"] = self.Analysis_by_measurement_component.loc[(
                        self.Analysis_by_measurement_component['Period'] == i
                    ) & (
                        self.Analysis_by_measurement_component['Measure'] ==
                        "Present value of future cash flows"
                    ), "Net balance at 1 January"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Net balance at 1 January"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Net balance at 1 January"]

                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Experience adjustments"] = iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP013') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP014') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_BE']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP014') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_LossC_BE'])
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Risk Adjustment"
                ), "Risk Adjustment recognised for the risk expired"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_RA']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP013') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_RA']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP014') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_RA']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP014') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_LossC_RA'])
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Contractual Service Margin"
                ), "CSM recognised in profit or loss for the services provided"] = -(
                    iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                    iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP014') &
                        (self.Assumptions['Cohort'] == i), 'Gross_CSM']))
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Changes that relate to current service"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "CSM recognised in profit or loss for the services provided"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i),
                    "Risk Adjustment recognised for the risk expired"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i
                         ), "Experience adjustments"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Experience adjustments"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Present value of future cash flows"
                ), "Experience adjustments"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i)
                    & (self.Analysis_by_measurement_component['Measure'] ==
                       "Risk Adjustment"),
                    "Experience adjustments"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Contractual Service Margin"),
                        "Experience adjustments"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Risk Adjustment recognised for the risk expired"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Risk Adjustment recognised for the risk expired"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Risk Adjustment recognised for the risk expired"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Risk Adjustment recognised for the risk expired"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "CSM recognised in profit or loss for the services provided"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "CSM recognised in profit or loss for the services provided"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "CSM recognised in profit or loss for the services provided"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "CSM recognised in profit or loss for the services provided"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Changes that relate to current service"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Changes that relate to current service"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Changes that relate to current service"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Changes that relate to current service"]

                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Changes in estimates that adjust the CSM"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i), 'Gross_BE']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP001') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_LossC_BE']) + iferror(
                            self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i), 'Gross_BE']
                        ) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP005') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP006') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_BE']) + iferror(
                                    self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP006') &
                                        (self.Assumptions['Cohort'] == i),
                                        'Gross_LossC_BE']
                                ) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP008') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_BE']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP008') &
                                            (self.Assumptions['Cohort'] == i),
                                            'Gross_LossC_BE']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP009') &
                                        (self.Assumptions['Cohort'] == i),
                                        'Gross_BE']) + iferror(
                                            self.Assumptions.loc[
                                                (self.Assumptions['Key'] ==
                                                 'MAP009') &
                                                (self.Assumptions['Cohort'] ==
                                                 i), 'Gross_LossC_BE']
                                        ) + iferror(self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP011') &
                                            (self.Assumptions['Cohort'] == i),
                                            'Gross_BE']) + iferror(
                                                self.Assumptions.loc[
                                                    (self.Assumptions['Key'] ==
                                                     'MAP011') &
                                                    (self.Assumptions['Cohort']
                                                     == i), 'Gross_LossC_BE'])
                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Risk Adjustment"),
                    "Changes in estimates that adjust the CSM"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i), 'Gross_RA']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP001') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_LossC_RA']) + iferror(
                            self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i), 'Gross_RA']
                        ) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP005') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_RA']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP006') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_RA']) + iferror(
                                    self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP006') &
                                        (self.Assumptions['Cohort'] == i),
                                        'Gross_LossC_RA']
                                ) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP008') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_RA']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP008') &
                                            (self.Assumptions['Cohort'] == i),
                                            'Gross_LossC_RA']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP009') &
                                        (self.Assumptions['Cohort'] == i),
                                        'Gross_RA']) + iferror(
                                            self.Assumptions.loc[
                                                (self.Assumptions['Key'] ==
                                                 'MAP009') &
                                                (self.Assumptions['Cohort'] ==
                                                 i), 'Gross_LossC_RA']
                                        ) + iferror(self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP011') &
                                            (self.Assumptions['Cohort'] == i),
                                            'Gross_RA']) + iferror(
                                                self.Assumptions.loc[
                                                    (self.Assumptions['Key'] ==
                                                     'MAP011') &
                                                    (self.Assumptions['Cohort']
                                                     == i), 'Gross_LossC_RA'])
                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Contractual Service Margin"),
                    "Changes in estimates that adjust the CSM"] = -(
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP005') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP006') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP008') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP009') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP011') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']))
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Present value of future cash flows"
                ), "Changes in estimates that result in onerous contract losses or reversal of losses"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP018') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP018') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_BE'])
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Risk Adjustment"
                ), "Changes in estimates that result in onerous contract losses or reversal of losses"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP018') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_RA']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP018') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_RA'])
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Contractual Service Margin"
                ), "Changes in estimates that result in onerous contract losses or reversal of losses"] = iferror(
                    self.Assumptions.loc[(self.Assumptions['Key'] == 'MAP018')
                                         & (self.Assumptions['Cohort'] == i),
                                         'Gross_CSM'])
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Present value of future cash flows"
                ), "Contracts initially recognised in the period"] = self.Reconciliation_of_Best_Estimate_Liability.loc[
                    i, "Changes Related to Future Service: New Business"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Risk Adjustment"
                ), "Contracts initially recognised in the period"] = self.Reconciliation_of_Risk_Adjustment.loc[
                    i, "Changes Related to Future Service: New Business"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Contractual Service Margin"
                ), "Contracts initially recognised in the period"] = self.Reconciliation_of_Contractual_Service_Margin.loc[
                    i, "Changes Related to Future Service: New Business"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Changes that relate to future service"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Changes in estimates that adjust the CSM"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i),
                    "Changes in estimates that result in onerous contract losses or reversal of losses"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i
                         ), "Contracts initially recognised in the period"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Changes in estimates that adjust the CSM"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Changes in estimates that adjust the CSM"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Changes in estimates that adjust the CSM"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Changes in estimates that adjust the CSM"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Changes in estimates that result in onerous contract losses or reversal of losses"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Changes in estimates that result in onerous contract losses or reversal of losses"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Changes in estimates that result in onerous contract losses or reversal of losses"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Changes in estimates that result in onerous contract losses or reversal of losses"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Contracts initially recognised in the period"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Contracts initially recognised in the period"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Contracts initially recognised in the period"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Contracts initially recognised in the period"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Changes that relate to future service"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Changes that relate to future service"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Changes that relate to future service"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Changes that relate to future service"]

                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Adjustments to liabilities for incurred claims"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP017') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP017') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_LossC_BE'])
                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Risk Adjustment"),
                    "Adjustments to liabilities for incurred claims"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP017') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_RA']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP017') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_LossC_RA'])
                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Contractual Service Margin"),
                    "Adjustments to liabilities for incurred claims"] = -(
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP017') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']))
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Changes that relate to past service"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i),
                    "Adjustments to liabilities for incurred claims"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Adjustments to liabilities for incurred claims"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Adjustments to liabilities for incurred claims"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Adjustments to liabilities for incurred claims"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Adjustments to liabilities for incurred claims"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Changes that relate to past service"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Changes that relate to past service"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Changes that relate to past service"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Changes that relate to past service"]

                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Insurance service result"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Changes that relate to current service"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i),
                    "Changes that relate to future service"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i
                         ), "Changes that relate to past service"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Insurance service result"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Present value of future cash flows"
                ), "Insurance service result"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i)
                    & (self.Analysis_by_measurement_component['Measure'] ==
                       "Risk Adjustment"),
                    "Insurance service result"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Contractual Service Margin"),
                        "Insurance service result"]

                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Present value of future cash flows"
                ), "Finance expenses from insurance contracts issued"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP007') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP007') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP010') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_BE']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP010') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_LossC_BE'])
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Risk Adjustment"
                ), "Finance expenses from insurance contracts issued"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP007') &
                        (self.Assumptions['Cohort'] == i),
                        'Gross_RA']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP007') &
                            (self.Assumptions['Cohort'] == i),
                            'Gross_LossC_RA']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP010') &
                                (self.Assumptions['Cohort'] == i),
                                'Gross_RA']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP010') &
                                    (self.Assumptions['Cohort'] == i),
                                    'Gross_LossC_RA'])
                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Contractual Service Margin"),
                    "Finance expenses from insurance contracts issued"] = -(
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP007') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']) +
                        iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP010') &
                            (self.Assumptions['Cohort'] == i), 'Gross_CSM']))
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Investment Component and Premium Refund"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i),
                    "Finance expenses from insurance contracts issued"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i
                         ), "Effects of movements in exchange rates"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Finance expenses from insurance contracts issued"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Finance expenses from insurance contracts issued"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Finance expenses from insurance contracts issued"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Finance expenses from insurance contracts issued"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Investment Component and Premium Refund"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Investment Component and Premium Refund"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Investment Component and Premium Refund"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Investment Component and Premium Refund"]

                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Total recognised in comprehensive income"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i),
                    "Insurance service result"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i
                         ), "Investment Component and Premium Refund"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Total recognised in comprehensive income"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Total recognised in comprehensive income"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Total recognised in comprehensive income"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Total recognised in comprehensive income"]

                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Premiums received"] = iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP002') &
                        (self.Assumptions['Cohort'] == i), 'Gross_Actual'])
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Present value of future cash flows"
                ), "Claims and other directly attributable expenses paid"] = iferror(
                    self.Assumptions.loc[(self.Assumptions['Key'] == 'MAP012')
                                         & (self.Assumptions['Cohort'] == i),
                                         'Gross_Actual'])
                self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Insurance acquisition cash flows"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP015') &
                            (self.Assumptions['Cohort'] == i), 'Gross_Actual'])
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Total cash flows"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Premiums received"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i),
                    "Claims and other directly attributable expenses paid"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i
                         ), "Insurance acquisition cash flows"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Premiums received"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Present value of future cash flows"
                ), "Premiums received"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i)
                    & (self.Analysis_by_measurement_component['Measure'] ==
                       "Risk Adjustment"),
                    "Premiums received"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Contractual Service Margin"), "Premiums received"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Claims and other directly attributable expenses paid"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Claims and other directly attributable expenses paid"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Claims and other directly attributable expenses paid"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Claims and other directly attributable expenses paid"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Insurance acquisition cash flows"] = self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i) &
                    (self.Analysis_by_measurement_component['Measure'] ==
                     "Present value of future cash flows"),
                    "Insurance acquisition cash flows"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Risk Adjustment"),
                        "Insurance acquisition cash flows"] + self.Analysis_by_measurement_component.loc[
                            (self.
                             Analysis_by_measurement_component['Period'] == i)
                            &
                            (self.Analysis_by_measurement_component['Measure']
                             == "Contractual Service Margin"),
                            "Insurance acquisition cash flows"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Total cash flows"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Present value of future cash flows"
                ), "Total cash flows"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i)
                    & (self.Analysis_by_measurement_component['Measure'] ==
                       "Risk Adjustment"),
                    "Total cash flows"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Contractual Service Margin"), "Total cash flows"]

                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Net balance at 31 December"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ), "Net balance at 1 January"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i),
                    "Total recognised in comprehensive income"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i
                         ), "Total cash flows"]
                self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Total"
                ), "Net balance at 31 December"] = self.Analysis_by_measurement_component.loc[(
                    self.Analysis_by_measurement_component['Period'] == i
                ) & (
                    self.Analysis_by_measurement_component['Measure'] ==
                    "Present value of future cash flows"
                ), "Net balance at 31 December"] + self.Analysis_by_measurement_component.loc[
                    (self.Analysis_by_measurement_component['Period'] == i)
                    & (self.Analysis_by_measurement_component['Measure'] ==
                       "Risk Adjustment"),
                    "Net balance at 31 December"] + self.Analysis_by_measurement_component.loc[
                        (self.Analysis_by_measurement_component['Period'] == i)
                        & (self.Analysis_by_measurement_component['Measure'] ==
                           "Contractual Service Margin"),
                        "Net balance at 31 December"]

            self.BEL.append(self.Reconciliation_of_Best_Estimate_Liability)
            self.RA.append(self.Reconciliation_of_Risk_Adjustment)
            self.CSM.append(self.Reconciliation_of_Contractual_Service_Margin)
            self.TCL.append(self.Reconciliation_of_Total_Contract_Liability)
            self.AMC.append(self.Analysis_by_measurement_component)

        self.BEL = pd.concat(self.BEL)
        self.RA = pd.concat(self.RA)
        self.CSM = pd.concat(self.CSM)
        self.TCL = pd.concat(self.TCL)
        self.AMC = pd.concat(self.AMC)
        
        self.BEL = self.BEL.to_csv('Reconciliation_of_Best_Estimate_Liability.csv')
        self.RA = self.RA.to_csv('Reconciliation_of_Best_Estimate_Liability.csv')
        self.CSM = self.CSM.to_csv('Reconciliation_of_Contractual_Service_Margin.csv')
        self.TCL = self.TCL.to_csv('Reconciliation_of_Total_Contract_Liability.csv')
        self.AMC = self.AMC.to_csv('Analysis_by_measurement_component.csv')


        # Analysis by remaining Coverage
        data_2 = pd.pivot_table(
            assumptions,
            index=['Cohort', 'Product', 'Sub-Product', 'BusinessType', 'Key'],
            aggfunc={
                'Gross_BE': 'sum',
                'Gross_LossC_BE': 'sum',
                'Gross_RA': 'sum',
                'Gross_LossC_RA': 'sum',
                'Gross_CSM': 'sum',
                'Gross_BECFPV': 'sum',
                'Gross_RACFPV': 'sum',
                'Gross_Actual': 'sum'
            })

        data_2 = data_2.reset_index()

        data_dict_2 = {
            'assumption_' + str(i): grp
            for i, grp in data_2.groupby(['Product', 'Sub-Product'])
        }

        count = 0
        for group in data_dict_2:
            Cohort_2 = data_dict_2[group]
            product_name = Cohort_2['Product'].unique()
            subproduct_name = Cohort_2['Sub-Product'].unique()

            self.Assumptions = Cohort_2

            # Liability on Initial Recognition

            for i in range(start, end + 1):

                if self.Parameters.loc[3, "Selection"] == "Input":

                    self.Liability_on_Initial_Recognition.loc[
                        inception, "CSM at Initial Recognition"] = iferror(
                            self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP004') &
                                (self.Assumptions['Cohort'] == inception) &
                                (self.Assumptions['BusinessType'] == 'NB') &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_CSM'])
                    self.Liability_on_Initial_Recognition.loc[
                        inception,
                        "LIABILITY ON INITIAL RECOGNITION-BE"] = iferror(
                            self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP004') &
                                (self.Assumptions['Cohort'] == inception) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_LossC_BE'])
                    self.Liability_on_Initial_Recognition.loc[
                        inception,
                        "LIABILITY ON INITIAL RECOGNITION-RA"] = iferror(
                            self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP004') &
                                (self.Assumptions['Cohort'] == inception) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_LossC_RA'])

                elif self.Parameters.loc[3, "Selection"] == "Calculation":

                    self.Liability_on_Initial_Recognition.loc[
                        inception,
                        "PV Premium"] = iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP003') &
                            (self.Assumptions['Cohort'] == inception) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_BECFPV'])
                    self.Liability_on_Initial_Recognition.loc[
                        inception, "PV Claims"] = iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP013') &
                            (self.Assumptions['Cohort'] == inception) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_BECFPV'])
                    self.Liability_on_Initial_Recognition.loc[
                        inception,
                        "PV Risk Adjustment"] = iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP013') &
                            (self.Assumptions['Cohort'] == inception) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_RACFPV'])
                    self.Liability_on_Initial_Recognition.loc[
                        inception, "PV Acquisition Expense"] = iferror(
                            self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP016') &
                                (self.Assumptions['Cohort'] == inception) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_BECFPV'])
                    Total = self.Liability_on_Initial_Recognition.loc[
                        inception,
                        "PV Premium"] + self.Liability_on_Initial_Recognition.loc[
                            inception,
                            "PV Claims"] + self.Liability_on_Initial_Recognition.loc[
                                inception,
                                "PV Risk Adjustment"] + self.Liability_on_Initial_Recognition.loc[
                                    inception, "PV Acquisition Expense"]

                    if Total > 0:
                        self.Liability_on_Initial_Recognition.loc[
                            inception, "CSM at Initial Recognition"] = Total
                        self.Liability_on_Initial_Recognition.loc[
                            inception,
                            "LIABILITY ON INITIAL RECOGNITION-BE"] = 0
                        self.Liability_on_Initial_Recognition.loc[
                            inception,
                            "LIABILITY ON INITIAL RECOGNITION-RA"] = 0

                    else:
                        self.Liability_on_Initial_Recognition.loc[
                            inception, "CSM at Initial Recognition"] = 0
                        self.Liability_on_Initial_Recognition.loc[
                            inception,
                            "LIABILITY ON INITIAL RECOGNITION-BE"] = (Total * (
                                (iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP013') &
                                    (self.Assumptions['Cohort'] == inception) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_BECFPV'])) /
                                (iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP013') &
                                    (self.Assumptions['Cohort'] == inception) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_BECFPV']) +
                                 iferror(self.Assumptions.loc[
                                     (self.Assumptions['Key'] == 'MAP013') &
                                     (self.Assumptions['Cohort'] == inception)
                                     &
                                     (self.Assumptions['BusinessType'] == 'NB'
                                      ), 'Gross_RACFPV']))))
                        self.Liability_on_Initial_Recognition.loc[
                            inception,
                            "LIABILITY ON INITIAL RECOGNITION-RA"] = (Total * (
                                (iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP013') &
                                    (self.Assumptions['Cohort'] == inception) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_RACFPV'])) /
                                (iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP013') &
                                    (self.Assumptions['Cohort'] == inception) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_BECFPV']) +
                                 iferror(self.Assumptions.loc[
                                     (self.Assumptions['Key'] == 'MAP013') &
                                     (self.Assumptions['Cohort'] == inception)
                                     &
                                     (self.Assumptions['BusinessType'] == 'NB'
                                      ), 'Gross_RACFPV']))))

            # Analysis_by_remaining_coverage

            for i in range(start, end + 1):
                for s in measure_abrc:
                    entry = pd.DataFrame(
                        {
                            'Period':
                            i,
                            'Measure':
                            s,
                            "Product":
                            product_name,
                            "Sub-Product":
                            subproduct_name,
                            'Net balance at 1 January':
                            0,
                            'Changes in the statement of profit and loss and OCI':
                            0,
                            'Contracts under the modified retrospective transition approach':
                            0,
                            'Contracts under the fair value transition approach':
                            0,
                            'Other contracts':
                            0,
                            'Expected incurred claims and other insurance services expenses':
                            0,
                            'Amortisation of insurance acquisition cash flows':
                            0,
                            'Losses and reversals of losses on onerous contracts':
                            0,
                            'Adjustments to liabilities for incurred claims':
                            0,
                            'Insurance service result':
                            0,
                            'Net finance expenses from insurance contracts':
                            0,
                            'Effect of movement in exchange rates':
                            0,
                            'Investment components and premium refunds':
                            0,
                            'Total changes in the statement of profit and loss and OCI':
                            0,
                            'Premiums received':
                            0,
                            'Claims and other insurance services expenses paid, including investment components':
                            0,
                            'Insurance acquisition cash flows':
                            0,
                            'Total cash flows':
                            0,
                            'Transfer to other items in the statement of financial position':
                            0,
                            'Net balance at 31 December':
                            0
                        },
                        index=[0])
                    if count == 0:
                        self.Analysis_by_remaining_coverage = entry
                    else:

                        self.Analysis_by_remaining_coverage = pd.concat(
                            [self.Analysis_by_remaining_coverage, entry],
                            axis=0)

                    count += 1

                if i == start:
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Net balance at 1 January"] = 0
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Only Loss Component"
                    ), "Net balance at 1 January"] = 0
                    self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Net balance at 1 January"] = 0
                    self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Total"), "Net balance at 1 January"] = 0
                else:
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Net balance at 1 January"] = self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i -
                         1) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Excluding loss component"
                         ), "Net balance at 31 December"]
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Only Loss Component"
                    ), "Net balance at 1 January"] = self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i -
                         1) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss Component"
                         ), "Net balance at 31 December"]
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for incurred claims"
                    ), "Net balance at 1 January"] = self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i -
                         1) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Net balance at 31 December"]
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Total"
                    ), "Net balance at 1 January"] = self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i -
                         1) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Total"), "Net balance at 31 December"]

                if self.Parameters.loc[
                        6, 'Selection'] == "Modified Retrospective Approach":

                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Contracts under the modified retrospective transition approach"] = self.Liability_on_Initial_Recognition.loc[
                        i, "CSM at Initial Recognition"]
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Only Loss Component"
                    ), "Contracts under the modified retrospective transition approach"] = self.Liability_on_Initial_Recognition.loc[
                        i,
                        "LIABILITY ON INITIAL RECOGNITION-BE"] + self.Liability_on_Initial_Recognition.loc[
                            i, "LIABILITY ON INITIAL RECOGNITION-RA"]
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for incurred claims"
                    ), "Contracts under the modified retrospective transition approach"] = 0
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Total"
                    ), "Contracts under the modified retrospective transition approach"] = self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Excluding loss component"
                         ),
                        "Contracts under the modified retrospective transition approach"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for remaining coverage - Only loss component"
                             ),
                            "Contracts under the modified retrospective transition approach"] + self.Analysis_by_remaining_coverage.loc[
                                (self.
                                 Analysis_by_remaining_coverage['Period'] == i)
                                &
                                (self.Analysis_by_remaining_coverage['Measure']
                                 == "Liabilities for incurred claims"),
                                "Contracts under the modified retrospective transition approach"]
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Other contracts"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_BE']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP001') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_RA']) - iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_CSM']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_BE']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP005') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_RA']) - iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP005') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'NB'), 'Gross_CSM']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP006') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'NB'), 'Gross_BE']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP006') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'NB'), 'Gross_RA']
                                         ) - iferror(self.Assumptions.loc[
                                             (self.Assumptions['Key'] ==
                                              'MAP006') &
                                             (self.Assumptions['Cohort'] == i)
                                             &
                                             (self.Assumptions['BusinessType']
                                              == 'NB'),
                                             'Gross_CSM']) + iferror(
                                                 self.Assumptions.loc[
                                                     (self.Assumptions['Key']
                                                      == 'MAP008') &
                                                     (self.
                                                      Assumptions['Cohort'] ==
                                                      i) & (self.Assumptions[
                                                          'BusinessType'] ==
                                                            'NB'), 'Gross_BE']
                                             ) + iferror(self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP008') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] == 'NB'),
                                                 'Gross_RA']) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM'])
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Only Loss Component"
                    ), "Other contracts"] = iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP001') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_LossC_RA']) + iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP005') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_LossC_BE']
                            ) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_LossC_RA']) + iferror(
                                    self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP006') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'NB'), 'Gross_LossC_BE']
                                ) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP006') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_LossC_RA']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP008') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'NB'), 'Gross_LossC_BE']
                                    ) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP008') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'NB'), 'Gross_LossC_RA']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP009') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'NB'), 'Gross_LossC_BE']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP009') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'NB'), 'Gross_LossC_RA']
                                         ) + iferror(self.Assumptions.loc[
                                             (self.Assumptions['Key'] ==
                                              'MAP011') &
                                             (self.Assumptions['Cohort'] == i)
                                             &
                                             (self.Assumptions['BusinessType']
                                              == 'NB'),
                                             'Gross_LossC_BE']) + iferror(
                                                 self.Assumptions.loc[
                                                     (self.Assumptions['Key']
                                                      == 'MAP011') &
                                                     (self.
                                                      Assumptions['Cohort'] ==
                                                      i) &
                                                     (self.Assumptions[
                                                         'BusinessType'] ==
                                                      'NB'), 'Gross_LossC_RA']
                                             ) + iferror(self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP014') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] == 'NB'),
                                                 'Gross_LossC_BE']) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'),
                                                         'Gross_LossC_RA'])
                    self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Other contracts"] = iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'IF'),
                            'Gross_BE']) + iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP001') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'IF'),
                                    'Gross_RA']
                            ) - iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP001') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'IF'),
                                'Gross_CSM']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP005') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'IF'),
                                    'Gross_BE']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP005') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'IF'), 'Gross_RA']
                                    ) - iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP005') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'IF'), 'Gross_CSM']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP006') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'IF'), 'Gross_BE']
                                         ) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP006') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] ==
                                                        'IF'), 'Gross_RA']
                                         ) - iferror(self.Assumptions.loc[
                                             (self.Assumptions['Key'] ==
                                              'MAP006'
                                              ) &
                                             (self.Assumptions['Cohort'] == i)
                                             &
                                             (self.Assumptions['BusinessType']
                                              == 'IF'),
                                             'Gross_CSM']) + iferror(
                                                 self.Assumptions.loc[
                                                     (self.Assumptions['Key']
                                                      == 'MAP008') &
                                                     (self.Assumptions[
                                                         'Cohort'] == i) & (
                                                             self.Assumptions[
                                                                 'BusinessType']
                                                             ==
                                                             'IF'), 'Gross_BE']
                                             ) + iferror(self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP008')
                                                 &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] == 'IF'),
                                                 'Gross_RA']) - iferror(
                                                     self.Assumptions.
                                                     loc[(self.Assumptions[
                                                         'Key'] == 'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP001') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP001') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP005') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP005') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP006') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP006') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA'])
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Total"
                    ), "Other contracts"] = self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Other contracts"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i)
                        &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only loss component"
                         ),
                        "Other contracts"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Other contracts"]

                elif self.Parameters.loc[6,
                                         'Selection'] == "Fair Value Approach":

                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Contracts under the fair value transition approach"] = self.Liability_on_Initial_Recognition.loc[
                        i, "CSM at Initial Recognition"]
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Only Loss Component"
                    ), "Contracts under the fair value transition approach"] = self.Liability_on_Initial_Recognition.loc[
                        i,
                        "LIABILITY ON INITIAL RECOGNITION-BE"] + self.Liability_on_Initial_Recognition.loc[
                            i, "LIABILITY ON INITIAL RECOGNITION-RA"]
                    self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Contracts under the fair value transition approach"] = 0
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Total"
                    ), "Contracts under the fair value transition approach"] = self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Excluding loss component"
                         ),
                        "Contracts under the fair value transition approach"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for remaining coverage - Only loss component"
                             ),
                            "Contracts under the fair value transition approach"] + self.Analysis_by_remaining_coverage.loc[
                                (self.
                                 Analysis_by_remaining_coverage['Period'] == i)
                                &
                                (self.Analysis_by_remaining_coverage['Measure']
                                 == "Liabilities for incurred claims"),
                                "Contracts under the fair value transition approach"]
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Other contracts"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_BE']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP001') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_RA']) - iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_CSM']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_BE']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP005') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_RA']) - iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP005') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'NB'), 'Gross_CSM']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP006') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'NB'), 'Gross_BE']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP006') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'NB'), 'Gross_RA']
                                         ) - iferror(self.Assumptions.loc[
                                             (self.Assumptions['Key'] ==
                                              'MAP006') &
                                             (self.Assumptions['Cohort'] == i)
                                             &
                                             (self.Assumptions['BusinessType']
                                              == 'NB'),
                                             'Gross_CSM']) + iferror(
                                                 self.Assumptions.loc[
                                                     (self.Assumptions['Key']
                                                      == 'MAP008') &
                                                     (self.
                                                      Assumptions['Cohort'] ==
                                                      i) & (self.Assumptions[
                                                          'BusinessType'] ==
                                                            'NB'), 'Gross_BE']
                                             ) + iferror(self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP008') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] == 'NB'),
                                                 'Gross_RA']) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM'])
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Only Loss Component"
                    ), "Other contracts"] = iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP001') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_LossC_RA']) + iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP005') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_LossC_BE']
                            ) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_LossC_RA']) + iferror(
                                    self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP006') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'NB'), 'Gross_LossC_BE']
                                ) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP006') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_LossC_RA']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP008') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'NB'), 'Gross_LossC_BE']
                                    ) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP008') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'NB'), 'Gross_LossC_RA']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP009') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'NB'), 'Gross_LossC_BE']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP009') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'NB'), 'Gross_LossC_RA']
                                         ) + iferror(self.Assumptions.loc[
                                             (self.Assumptions['Key'] ==
                                              'MAP011') &
                                             (self.Assumptions['Cohort'] == i)
                                             &
                                             (self.Assumptions['BusinessType']
                                              == 'NB'),
                                             'Gross_LossC_BE']) + iferror(
                                                 self.Assumptions.loc[
                                                     (self.Assumptions['Key']
                                                      == 'MAP011') &
                                                     (self.
                                                      Assumptions['Cohort'] ==
                                                      i) &
                                                     (self.Assumptions[
                                                         'BusinessType'] ==
                                                      'NB'), 'Gross_LossC_RA']
                                             ) + iferror(self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP014') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] == 'NB'),
                                                 'Gross_LossC_BE']) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'),
                                                         'Gross_LossC_RA'])
                    self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Other contracts"] = iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'IF'),
                            'Gross_BE']) + iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP001') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'IF'),
                                    'Gross_RA']
                            ) - iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP001') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'IF'),
                                'Gross_CSM']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP005') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'IF'),
                                    'Gross_BE']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP005') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'IF'), 'Gross_RA']
                                    ) - iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP005') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'IF'), 'Gross_CSM']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP006') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'IF'), 'Gross_BE']
                                         ) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP006') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] ==
                                                        'IF'), 'Gross_RA']
                                         ) - iferror(self.Assumptions.loc[
                                             (self.Assumptions['Key'] ==
                                              'MAP006'
                                              ) &
                                             (self.Assumptions['Cohort'] == i)
                                             &
                                             (self.Assumptions['BusinessType']
                                              == 'IF'),
                                             'Gross_CSM']) + iferror(
                                                 self.Assumptions.loc[
                                                     (self.Assumptions['Key']
                                                      == 'MAP008') &
                                                     (self.Assumptions[
                                                         'Cohort'] == i) & (
                                                             self.Assumptions[
                                                                 'BusinessType']
                                                             ==
                                                             'IF'), 'Gross_BE']
                                             ) + iferror(self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP008')
                                                 &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] == 'IF'),
                                                 'Gross_RA']) - iferror(
                                                     self.Assumptions.
                                                     loc[(self.Assumptions[
                                                         'Key'] == 'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP001') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP001') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP005') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP005') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP006') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP006') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA'])
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Total"
                    ), "Other contracts"] = self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Other contracts"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i)
                        &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only loss component"
                         ),
                        "Other contracts"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Other contracts"]

                elif self.Parameters.loc[6, 'Selection'] == "Other":

                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Other contracts"] = self.Liability_on_Initial_Recognition.loc[
                        i, "CSM at Initial Recognition"] + iferror(
                            self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP001') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_BE']
                        ) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_RA']) - iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP001') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_CSM']
                            ) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_BE']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP005') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_RA']) - iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP005') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'NB'), 'Gross_CSM']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP006') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'NB'), 'Gross_BE']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP006') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'NB'), 'Gross_RA']
                                         ) - iferror(self.Assumptions.loc[
                                             (self.Assumptions['Key'] ==
                                              'MAP006') &
                                             (self.Assumptions['Cohort'] == i)
                                             &
                                             (self.Assumptions['BusinessType']
                                              == 'NB'),
                                             'Gross_CSM']) + iferror(
                                                 self.Assumptions.loc[
                                                     (self.Assumptions['Key']
                                                      == 'MAP008') &
                                                     (self.
                                                      Assumptions['Cohort'] ==
                                                      i) & (self.Assumptions[
                                                          'BusinessType'] ==
                                                            'NB'), 'Gross_BE']
                                             ) + iferror(self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP008') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] == 'NB'),
                                                 'Gross_RA']) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'), 'Gross_CSM'])
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Only Loss Component"
                    ), "Other contracts"] = self.Liability_on_Initial_Recognition.loc[
                        i,
                        "LIABILITY ON INITIAL RECOGNITION-BE"] + self.Liability_on_Initial_Recognition.loc[
                            i,
                            "LIABILITY ON INITIAL RECOGNITION-RA"] + iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP001') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_LossC_BE']
                            ) + iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP001') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_LossC_RA']
                            ) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP005') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_LossC_BE']) + iferror(
                                    self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP005') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'NB'), 'Gross_LossC_RA']
                                ) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP006') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_LossC_BE']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP006') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'NB'), 'Gross_LossC_RA']
                                    ) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP008') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'NB'), 'Gross_LossC_BE']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP008') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'NB'), 'Gross_LossC_RA']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP009') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'NB'), 'Gross_LossC_BE']
                                         ) + iferror(self.Assumptions.loc[
                                             (self.Assumptions['Key'] ==
                                              'MAP009') &
                                             (self.Assumptions['Cohort'] == i)
                                             &
                                             (self.Assumptions['BusinessType']
                                              == 'NB'),
                                             'Gross_LossC_RA']) + iferror(
                                                 self.Assumptions.loc[
                                                     (self.Assumptions['Key']
                                                      == 'MAP011') &
                                                     (self.
                                                      Assumptions['Cohort'] ==
                                                      i) &
                                                     (self.Assumptions[
                                                         'BusinessType'] ==
                                                      'NB'), 'Gross_LossC_BE']
                                             ) + iferror(self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP011') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] == 'NB'),
                                                 'Gross_LossC_RA']) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'NB'),
                                                         'Gross_LossC_RA'])
                    self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Other contracts"] = iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP001') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'IF'),
                            'Gross_BE']) + iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP001') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'IF'),
                                    'Gross_RA']
                            ) - iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP001') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'IF'),
                                'Gross_CSM']) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP005') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'IF'),
                                    'Gross_BE']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP005') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'IF'), 'Gross_RA']
                                    ) - iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP005') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'IF'), 'Gross_CSM']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP006') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'IF'), 'Gross_BE']
                                         ) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP006') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] ==
                                                        'IF'), 'Gross_RA']
                                         ) - iferror(self.Assumptions.loc[
                                             (self.Assumptions['Key'] ==
                                              'MAP006'
                                              ) &
                                             (self.Assumptions['Cohort'] == i)
                                             &
                                             (self.Assumptions['BusinessType']
                                              == 'IF'),
                                             'Gross_CSM']) + iferror(
                                                 self.Assumptions.loc[
                                                     (self.Assumptions['Key']
                                                      == 'MAP008') &
                                                     (self.Assumptions[
                                                         'Cohort'] == i) & (
                                                             self.Assumptions[
                                                                 'BusinessType']
                                                             ==
                                                             'IF'), 'Gross_BE']
                                             ) + iferror(self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP008')
                                                 &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) & (self.Assumptions[
                                                      'BusinessType'] == 'IF'),
                                                 'Gross_RA']) - iferror(
                                                     self.Assumptions.
                                                     loc[(self.Assumptions[
                                                         'Key'] == 'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_RA']
                                                 ) - iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'), 'Gross_CSM']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP001') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP001') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP005') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP005') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP006') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP006') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP008') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP009') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP011') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_BE']
                                                 ) + iferror(
                                                     self.Assumptions.loc[
                                                         (self.
                                                          Assumptions['Key'] ==
                                                          'MAP014') &
                                                         (self.Assumptions[
                                                             'Cohort'] == i) &
                                                         (self.Assumptions[
                                                             'BusinessType'] ==
                                                          'IF'),
                                                         'Gross_LossC_RA'])
                    self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Total"
                    ), "Other contracts"] = self.Analysis_by_remaining_coverage.loc[(
                        self.Analysis_by_remaining_coverage['Period'] == i
                    ) & (
                        self.Analysis_by_remaining_coverage['Measure'] ==
                        "Liabilities for remaining coverage - Excluding loss component"
                    ), "Other contracts"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i)
                        &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss Component"
                         ),
                        "Other contracts"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Other contracts"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Expected incurred claims and other insurance services expenses"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'), 'Gross_BE']
                ) + iferror(self.Assumptions.loc[
                    (self.Assumptions['Key'] == 'MAP013') &
                    (self.Assumptions['Cohort'] == i) &
                    (self.Assumptions['BusinessType'] == 'NB'),
                    'Gross_RA']) - (iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_CSM'])) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP014') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP014') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_RA']) - (iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP014') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_CSM']))
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Expected incurred claims and other insurance services expenses"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_LossC_BE']
                ) + iferror(self.Assumptions.loc[
                    (self.Assumptions['Key'] == 'MAP013') &
                    (self.Assumptions['Cohort'] == i) &
                    (self.Assumptions['BusinessType'] == 'NB'),
                    'Gross_LossC_RA']) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP014') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP014') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_LossC_RA'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Expected incurred claims and other insurance services expenses"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'IF'), 'Gross_BE']
                ) + iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP013') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'IF'), 'Gross_RA']
                ) - iferror(self.Assumptions.loc[
                    (self.Assumptions['Key'] == 'MAP013') &
                    (self.Assumptions['Cohort'] == i) &
                    (self.Assumptions['BusinessType'] == 'IF'),
                    'Gross_CSM']) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP014') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'IF'),
                        'Gross_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP014') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'IF'),
                            'Gross_RA']) - iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP014') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'IF'),
                                'Gross_CSM']) + iferror(
                                    self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP013') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'IF'), 'Gross_LossC_BE']
                                ) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP013') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'IF'),
                                    'Gross_LossC_RA']) + iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP014') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'IF'), 'Gross_LossC_BE']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP014') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'IF'), 'Gross_LossC_RA'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Expected incurred claims and other insurance services expenses"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Expected incurred claims and other insurance services expenses"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ),
                        "Expected incurred claims and other insurance services expenses"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Expected incurred claims and other insurance services expenses"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Losses and reversals of losses on onerous contracts"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP018') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP018') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_RA']) - iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP018') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_CSM'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Losses and reversals of losses on onerous contracts"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP018') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP018') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_LossC_RA'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Losses and reversals of losses on onerous contracts"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP018') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'IF'), 'Gross_BE']
                ) + iferror(self.Assumptions.loc[
                    (self.Assumptions['Key'] == 'MAP018') &
                    (self.Assumptions['Cohort'] == i) &
                    (self.Assumptions['BusinessType'] == 'IF'),
                    'Gross_RA']) - iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP018') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'IF'),
                        'Gross_CSM']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP018') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'IF'),
                            'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP018') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'IF'),
                                'Gross_LossC_RA'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Losses and reversals of losses on onerous contracts"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Losses and reversals of losses on onerous contracts"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ),
                        "Losses and reversals of losses on onerous contracts"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Losses and reversals of losses on onerous contracts"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Adjustments to liabilities for incurred claims"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP017') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP017') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_RA']) - iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP017') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_CSM'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Adjustments to liabilities for incurred claims"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP017') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP017') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_LossC_RA'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Adjustments to liabilities for incurred claims"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP017') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'IF'), 'Gross_BE']
                ) + iferror(self.Assumptions.loc[
                    (self.Assumptions['Key'] == 'MAP017') &
                    (self.Assumptions['Cohort'] == i) &
                    (self.Assumptions['BusinessType'] == 'IF'),
                    'Gross_RA']) - iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP017') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'IF'),
                        'Gross_CSM']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP017') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'IF'),
                            'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP017') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'IF'),
                                'Gross_LossC_RA'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Adjustments to liabilities for incurred claims"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Adjustments to liabilities for incurred claims"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ),
                        "Adjustments to liabilities for incurred claims"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Adjustments to liabilities for incurred claims"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Insurance service result"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Contracts under the modified retrospective transition approach"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i)
                    &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Contracts under the fair value transition approach"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Excluding loss component"
                         ),
                        "Other contracts"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for remaining coverage - Excluding loss component"
                             ),
                            "Expected incurred claims and other insurance services expenses"] + self.Analysis_by_remaining_coverage.loc[
                                (self.
                                 Analysis_by_remaining_coverage['Period'] == i)
                                &
                                (self.
                                 Analysis_by_remaining_coverage['Measure'] ==
                                 "Liabilities for remaining coverage - Excluding loss component"
                                 ),
                                "Losses and reversals of losses on onerous contracts"] + self.Analysis_by_remaining_coverage.loc[
                                    (self.Analysis_by_remaining_coverage[
                                        'Period'] == i) &
                                    (self.Analysis_by_remaining_coverage[
                                        'Measure'] ==
                                     "Liabilities for remaining coverage - Excluding loss component"
                                     ),
                                    "Adjustments to liabilities for incurred claims"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Insurance service result"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Contracts under the modified retrospective transition approach"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i)
                    &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Contracts under the fair value transition approach"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ),
                        "Other contracts"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for remaining coverage - Only Loss component"
                             ),
                            "Expected incurred claims and other insurance services expenses"] + self.Analysis_by_remaining_coverage.loc[
                                (self.
                                 Analysis_by_remaining_coverage['Period'] == i)
                                &
                                (self.
                                 Analysis_by_remaining_coverage['Measure'] ==
                                 "Liabilities for remaining coverage - Only Loss component"
                                 ),
                                "Losses and reversals of losses on onerous contracts"] + self.Analysis_by_remaining_coverage.loc[
                                    (self.Analysis_by_remaining_coverage[
                                        'Period'] == i) &
                                    (self.Analysis_by_remaining_coverage[
                                        'Measure'] ==
                                     "Liabilities for remaining coverage - Only Loss component"
                                     ),
                                    "Adjustments to liabilities for incurred claims"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Insurance service result"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Contracts under the modified retrospective transition approach"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i)
                    & (self.Analysis_by_remaining_coverage['Measure'] ==
                       "Liabilities for incurred claims"),
                    "Contracts under the fair value transition approach"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Other contracts"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Expected incurred claims and other insurance services expenses"] + self.Analysis_by_remaining_coverage.loc[
                                (self.
                                 Analysis_by_remaining_coverage['Period'] == i)
                                &
                                (self.Analysis_by_remaining_coverage['Measure']
                                 == "Liabilities for incurred claims"),
                                "Losses and reversals of losses on onerous contracts"] + self.Analysis_by_remaining_coverage.loc[
                                    (self.Analysis_by_remaining_coverage[
                                        'Period'] == i) &
                                    (self.
                                     Analysis_by_remaining_coverage['Measure']
                                     == "Liabilities for incurred claims"),
                                    "Adjustments to liabilities for incurred claims"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Insurance service result"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Insurance service result"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i)
                    &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Insurance service result"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Insurance service result"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Net finance expenses from insurance contracts"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP007') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'), 'Gross_BE']
                ) + iferror(self.Assumptions.loc[
                    (self.Assumptions['Key'] == 'MAP007') &
                    (self.Assumptions['Cohort'] == i) &
                    (self.Assumptions['BusinessType'] == 'NB'),
                    'Gross_RA']) - iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP007') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_CSM']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP010') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP010') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_RA']) - iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP010') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'NB'),
                                    'Gross_CSM'])
                self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Net finance expenses from insurance contracts"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP007') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_LossC_BE']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP007') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_LossC_RA']) + iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP010') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'NB'),
                            'Gross_LossC_BE']) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP010') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'NB'),
                                'Gross_LossC_RA'])
                self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for incurred claims"),
                    "Net finance expenses from insurance contracts"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP007') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'IF'),
                            'Gross_BE']
                    ) + iferror(self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP007') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'IF'),
                        'Gross_RA']) - iferror(self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP007') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'IF'),
                            'Gross_CSM']) + iferror(
                                self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP007') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'IF'),
                                    'Gross_LossC_BE']
                            ) + iferror(self.Assumptions.loc[
                                (self.Assumptions['Key'] == 'MAP007') &
                                (self.Assumptions['Cohort'] == i) &
                                (self.Assumptions['BusinessType'] == 'IF'),
                                'Gross_LossC_RA']) + iferror(
                                    self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP010') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'IF'), 'Gross_BE']
                                ) + iferror(self.Assumptions.loc[
                                    (self.Assumptions['Key'] == 'MAP010') &
                                    (self.Assumptions['Cohort'] == i) &
                                    (self.Assumptions['BusinessType'] == 'IF'),
                                    'Gross_RA']) - iferror(
                                        self.Assumptions.loc[
                                            (self.Assumptions['Key'] ==
                                             'MAP010') &
                                            (self.Assumptions['Cohort'] == i) &
                                            (self.Assumptions['BusinessType']
                                             == 'IF'), 'Gross_CSM']
                                    ) + iferror(self.Assumptions.loc[
                                        (self.Assumptions['Key'] == 'MAP010') &
                                        (self.Assumptions['Cohort'] == i) &
                                        (self.Assumptions['BusinessType'] ==
                                         'IF'), 'Gross_LossC_BE']) + iferror(
                                             self.Assumptions.loc[
                                                 (self.Assumptions['Key'] ==
                                                  'MAP010') &
                                                 (self.Assumptions['Cohort'] ==
                                                  i) &
                                                 (self.
                                                  Assumptions['BusinessType']
                                                  == 'IF'), 'Gross_LossC_RA'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Net finance expenses from insurance contracts"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Net finance expenses from insurance contracts"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ),
                        "Net finance expenses from insurance contracts"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Net finance expenses from insurance contracts"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Investment components and premium refunds"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Net finance expenses from insurance contracts"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Excluding loss component"
                         ), "Effect of movement in exchange rates"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Investment components and premium refunds"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Net finance expenses from insurance contracts"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ), "Effect of movement in exchange rates"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Investment components and premium refunds"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for incurred claims"),
                    "Net finance expenses from insurance contracts"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Effect of movement in exchange rates"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Investment components and premium refunds"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Investment components and premium refunds"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ),
                        "Investment components and premium refunds"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Investment components and premium refunds"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Total changes in the statement of profit and loss and OCI"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Insurance service result"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Excluding loss component"
                         ), "Investment components and premium refunds"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Total changes in the statement of profit and loss and OCI"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Insurance service result"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ), "Investment components and premium refunds"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Total changes in the statement of profit and loss and OCI"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for incurred claims"),
                    "Insurance service result"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Investment components and premium refunds"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Total changes in the statement of profit and loss and OCI"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Total changes in the statement of profit and loss and OCI"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ),
                        "Total changes in the statement of profit and loss and OCI"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Total changes in the statement of profit and loss and OCI"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Premiums received"] = iferror(self.Assumptions.loc[
                    (self.Assumptions['Key'] == 'MAP002') &
                    (self.Assumptions['Cohort'] == i) &
                    (self.Assumptions['BusinessType'] == 'NB'),
                    'Gross_Actual'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Premiums received"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Premiums received"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Premiums received"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Premiums received"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Claims and other insurance services expenses paid, including investment components"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP012') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_Actual'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Claims and other insurance services expenses paid, including investment components"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP012') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'IF'),
                        'Gross_Actual'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Claims and other insurance services expenses paid, including investment components"] = self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Claims and other insurance services expenses paid, including investment components"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ),
                        "Claims and other insurance services expenses paid, including investment components"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Claims and other insurance services expenses paid, including investment components"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Insurance acquisition cash flows"] = iferror(
                    self.Assumptions.loc[
                        (self.Assumptions['Key'] == 'MAP015') &
                        (self.Assumptions['Cohort'] == i) &
                        (self.Assumptions['BusinessType'] == 'NB'),
                        'Gross_Actual'])
                self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for incurred claims"),
                    "Insurance acquisition cash flows"] = iferror(
                        self.Assumptions.loc[
                            (self.Assumptions['Key'] == 'MAP015') &
                            (self.Assumptions['Cohort'] == i) &
                            (self.Assumptions['BusinessType'] == 'IF'),
                            'Gross_Actual'])
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Insurance acquisition cash flows"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Insurance acquisition cash flows"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i)
                    &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Insurance acquisition cash flows"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Insurance acquisition cash flows"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Total cash flows"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Premiums received"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Claims and other insurance services expenses paid, including investment components"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Excluding loss component"
                         ), "Insurance acquisition cash flows"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Total cash flows"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Premiums received"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Claims and other insurance services expenses paid, including investment components"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ), "Insurance acquisition cash flows"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Total cash flows"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Premiums received"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for incurred claims"),
                    "Claims and other insurance services expenses paid, including investment components"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Insurance acquisition cash flows"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Total cash flows"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Total cash flows"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i) &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Total cash flows"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Total cash flows"]

                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Net balance at 31 December"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Net balance at 1 January"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i)
                    &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Excluding loss component"
                     ),
                    "Total changes in the statement of profit and loss and OCI"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Excluding loss component"
                         ),
                        "Total cash flows"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for remaining coverage - Excluding loss component"
                             ),
                            "Transfer to other items in the statement of financial position"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Net balance at 31 December"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Only Loss component"
                ), "Net balance at 1 January"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i)
                    &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Total changes in the statement of profit and loss and OCI"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for remaining coverage - Only Loss component"
                         ),
                        "Total cash flows"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for remaining coverage - Only Loss component"
                             ),
                            "Transfer to other items in the statement of financial position"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Net balance at 31 December"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for incurred claims"
                ), "Net balance at 1 January"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i)
                    & (self.Analysis_by_remaining_coverage['Measure'] ==
                       "Liabilities for incurred claims"),
                    "Total changes in the statement of profit and loss and OCI"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Total cash flows"] + self.Analysis_by_remaining_coverage.loc[
                            (self.Analysis_by_remaining_coverage['Period'] == i
                             ) &
                            (self.Analysis_by_remaining_coverage['Measure'] ==
                             "Liabilities for incurred claims"),
                            "Transfer to other items in the statement of financial position"]
                self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] == "Total"
                ), "Net balance at 31 December"] = self.Analysis_by_remaining_coverage.loc[(
                    self.Analysis_by_remaining_coverage['Period'] == i
                ) & (
                    self.Analysis_by_remaining_coverage['Measure'] ==
                    "Liabilities for remaining coverage - Excluding loss component"
                ), "Net balance at 31 December"] + self.Analysis_by_remaining_coverage.loc[
                    (self.Analysis_by_remaining_coverage['Period'] == i)
                    &
                    (self.Analysis_by_remaining_coverage['Measure'] ==
                     "Liabilities for remaining coverage - Only Loss component"
                     ),
                    "Net balance at 31 December"] + self.Analysis_by_remaining_coverage.loc[
                        (self.Analysis_by_remaining_coverage['Period'] == i) &
                        (self.Analysis_by_remaining_coverage['Measure'] ==
                         "Liabilities for incurred claims"),
                        "Net balance at 31 December"]

            self.ARC.append(self.Analysis_by_remaining_coverage)

        self.ARC = pd.concat(self.ARC)
        self.ARC = self.ARC.to_csv('Analysis_by_remaining_coverage.csv')
