import matplotlib.pyplot as plt
import pandas as pd

from FileUtil import FileUtil
from Util import Util
from constants import Constants
from pathlib import Path
import scipy.stats as stats
import seaborn as sns
import stats.CliffDelta as cld
from scipy import stats
import numpy as np


class ChangeKindAnalysis:
    
    def apply_cliff_delta(self, x1, x2, grp1, grp2):
        d, size = cld.cliffsDelta(x1, x2)
        w, p = stats.mannwhitneyu(x1, x2, alternative='two-sided')

        return {
            "d": d,
            "size": size,
            "w": w,
            "p_value": p,
            "significant": "yes" if p < 0.05 else "no",
            "between": grp1 + "_and_" + grp2,
            "grp1": grp1,
            "grp2": grp2
        }

    def print_repo_not_in_list(self, ageData, threshold, grp):
        if ageData.shape[0] != 53:
            not_in_list = list(set(Constants.ALL_MINED_REPOS) - set(ageData["repo"]))
            print("Age {0} not in list: {1} for grp {2}".format(threshold, not_in_list, grp))



    def compare_different_changes_age730(self, age_threshold, filename):
        ageData = pd.read_csv(Constants.BASE_PATH + "age/all_age_norm_data_without_x_years_methods.csv")
        ageData = ageData[
            (ageData["type"] == "kendall")  & (ageData["age_threshold"] == age_threshold)
        ]

        allChanges = ageData[ageData["group"] == "sloc_vs_all_changes"]
        essentialChanges = ageData[ageData["group"] == "sloc_vs_essential_changes"]
        bodychanges = ageData[ageData["group"] == "sloc_vs_bodychanges"]
        minorchanges = ageData[ageData["group"] == "sloc_vs_minorchanges"]

        allChanges.to_csv(Constants.BASE_PATH + "changeKind/revisions.csv")
        essentialChanges.to_csv(Constants.BASE_PATH + "changeKind/essentialChanges.csv")
        bodychanges.to_csv(Constants.BASE_PATH + "changeKind/bodychanges.csv")
        minorchanges.to_csv(Constants.BASE_PATH + "changeKind/minorchanges.csv")

        r = []

        r.append(self.apply_cliff_delta(allChanges["corr"], essentialChanges["corr"], "all_changes", "essential_changes"))
        r.append(self.apply_cliff_delta(allChanges["corr"], bodychanges["corr"], "all_changes", "bodychanges"))
        r.append(self.apply_cliff_delta(allChanges["corr"], minorchanges["corr"], "all_changes", "minorchanges"))

        r.append(self.apply_cliff_delta(essentialChanges["corr"], bodychanges["corr"], "essential_changes", "bodychanges"))
        r.append(self.apply_cliff_delta(essentialChanges["corr"], minorchanges["corr"], "essential_changes", "minorchanges"))

        r.append(
            self.apply_cliff_delta(bodychanges["corr"], minorchanges["corr"], "bodychanges", "minorchanges"))

        pd.DataFrame.from_dict(r).to_csv(Constants.BASE_PATH + "changeKind/rq4_cliff_delta_change_kind.csv")

        sns.set_style("whitegrid")
        plt.figure(figsize=(7.5, 6))
        sns.ecdfplot(allChanges, x=allChanges["corr"], linewidth=2.0, marker="o", markersize=15, markevery=5)
        sns.ecdfplot(essentialChanges, x=essentialChanges["corr"], linewidth=2.0, marker="d", markersize=15, markevery=5)
        sns.ecdfplot(bodychanges, x=bodychanges["corr"], linewidth=2.0, marker="*", markersize=15, markevery=5)
        ax= sns.ecdfplot(minorchanges, x=minorchanges["corr"], linewidth=2.0, marker="X", markersize=15, markevery=5)
        ax.set_xlim(-0.2, 0.7)

        plt.xlabel("Correlation Values", fontsize=18, weight="bold")
        plt.xticks(fontsize=18, weight="bold")
        plt.yticks(fontsize=18, weight="bold")
        plt.ylabel("CDF", fontsize=18, weight="bold")

        legend_props = {"weight": "bold", "size": 16, "family": "monospace"}
        plt.legend(["#Revisions", "#Essential", "#Body", "#NonEssential"], prop=legend_props, loc="lower right")
        plt.savefig(
            Constants.BASE_PATH + "plots/rq4_" + filename,
            bbox_inches='tight')
        plt.show()

    def compare_different_size_changes_age730(self, age_threshold, filename):
        ageData = pd.read_csv(Constants.BASE_PATH + "age/all_age_norm_data_without_x_years_methods.csv")
        ageData = ageData[
            (ageData["type"] == "kendall")  & (ageData["age_threshold"] == age_threshold)
        ]

        allChanges = ageData[ageData["group"] == "sloc_vs_all_changes"]
        newAdditions = ageData[ageData["group"] == "sloc_vs_newAdditions"]
        diffSizes = ageData[ageData["group"] == "sloc_vs_diffSizes"]
        editDistance = ageData[ageData["group"] == "sloc_vs_editDistance"]

        
        newAdditions.to_csv(Constants.BASE_PATH + "changeKind/newAdditionsChanges.csv")
        diffSizes.to_csv(Constants.BASE_PATH + "changeKind/diffSizesChanges.csv")
        editDistance.to_csv(Constants.BASE_PATH + "changeKind/editDistanceChanges.csv")

        r = []

        r.append(self.apply_cliff_delta(allChanges["corr"], newAdditions["corr"], "all_changes", "newAdditions"))
        r.append(self.apply_cliff_delta(allChanges["corr"], diffSizes["corr"], "all_changes", "diffSizes"))
        r.append(self.apply_cliff_delta(allChanges["corr"], editDistance["corr"], "all_changes", "editDistance"))

        r.append(self.apply_cliff_delta(newAdditions["corr"], diffSizes["corr"], "newAdditions", "diffSizes"))
        r.append(self.apply_cliff_delta(newAdditions["corr"], editDistance["corr"], "newAdditions", "editDistance"))

        r.append(
            self.apply_cliff_delta(diffSizes["corr"], editDistance["corr"], "diffSizes", "editDistance"))

        pd.DataFrame.from_dict(r).to_csv(Constants.BASE_PATH + "changeKind/rq4_cliff_delta_newaddition_diffsize_editdistance.csv")

        sns.set_style("whitegrid")
        plt.figure(figsize=(7.5, 6))
        sns.ecdfplot(allChanges, x=allChanges["corr"], linewidth=2.0, marker="o", markersize=15, markevery=5)
        sns.ecdfplot(newAdditions, x=newAdditions["corr"], linewidth=2.0, marker="d", markersize=15, markevery=5)
        sns.ecdfplot(diffSizes, x=diffSizes["corr"], linewidth=2.0, marker="*", markersize=15, markevery=5)
        ax= sns.ecdfplot(editDistance, x=editDistance["corr"], linewidth=2.0, marker="X", markersize=15, markevery=5)
        ax.set_xlim(-0.2, 0.7)

        plt.xlabel("Correlation Values", fontsize=18, weight="bold")
        plt.xticks(fontsize=18, weight="bold")
        plt.yticks(fontsize=18, weight="bold")
        plt.ylabel("CDF", fontsize=18, weight="bold")

        legend_props = {"weight": "bold", "size": 16, "family": "monospace"}
        plt.legend(["#Revisions", "NewAdditions", "DiffSizes", "EditDistance"], prop=legend_props, loc="lower right")
        plt.savefig(
            Constants.BASE_PATH + "plots/rq4_" + filename,
            bbox_inches='tight')
        plt.show()

# c = ChangeKindAnalysis()
# c.process(0)
# c.process(730)
# c.different_age_norm_compare("all_age_norm_data.csv", "ageNorm")
# c.different_age_norm_compare("all_corr_interval_age_data.csv", "interval")
# c.compare_different_changes_age730(730, "change_kind_corr_cdf.pdf")