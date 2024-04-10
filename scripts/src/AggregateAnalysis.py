import collections

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from FileUtil import FileUtil
from constants import Constants
import seaborn as sns
import stats.CliffDelta as cld
from scipy import stats


class AggregateAnalysis:

    def process(self, age):
        print("start calculating aggregated project corr values of SLOC with revisions and bugs.......")
        age730 = FileUtil.load_json(Constants.BASE_PATH + "age/age_norm_" + str(age) +".json")
        df = pd.DataFrame.from_dict(age730["data"])
        # considering all methods that are at least 2 years of age
        df = df[df["shouldSkipXMethods"] == False]

        result = []
        self.append_to_result(result, df, "sloc", "allChanges")
        self.append_to_result(result, df, "sloc", "bugCount")
        
        pd.DataFrame.from_dict(result).to_csv(Constants.BASE_PATH + "Aggregate/aggregated_analysis_metrics.csv")

        self.render_corr_sloc_with_revision_bugs(age)
        print("Done aggregated analysis.....")

    def append_to_result(self, result, df, grp1, grp2):
        label = grp1 + "_vs_" + grp2
        result.append(self.apply_stats(df[grp1], df[grp2], label, 'all', stats_to_apply="kendall"))
       

    def apply_stats(self, x1, x2, label, repo, stats_to_apply="kendall"):
        if stats_to_apply == "kendall":
            corr, p_value = stats.kendalltau(x1, x2)
        elif stats_to_apply == 'spearman':
            corr, p_value = stats.spearmanr(x1, x2)
        else:
            corr, p_value = stats.pearsonr(x1, x2)

        return {
            "corr": round(corr, 2),
            "p_value": p_value,
            "significant": 'yes' if p_value < 0.05 else "no",
            "group": label,
            "repo": repo,
            "type": stats_to_apply
        }

    
    def render_corr_sloc_with_revision_bugs(self, age_threshold=730):
        data = pd.read_csv(Constants.BASE_PATH + "age/all_age_norm_data_without_x_years_methods.csv")
        sloc_with_revisions = data[(data["age_threshold"] == age_threshold) & (data["group"] == "sloc_vs_all_changes")]
        sloc_with_bugs = data[(data["age_threshold"] == age_threshold) & (data["group"] == "sloc_vs_bugCount")]

        sns.set_style("whitegrid")
        sns.set_context(font_scale=3)
        plt.figure(figsize=(7.5, 6))

        sns.ecdfplot(sloc_with_revisions, x=sloc_with_revisions["corr"], linewidth=2, marker=">", markersize=15)
        sns.ecdfplot(sloc_with_bugs, x=sloc_with_bugs["corr"], linewidth=2, marker="o", markersize=15)
        
       
        legend_props = {"weight": "bold", "size": 18, "family": "monospace"}

        plt.legend(["#Revisions", "#Bugs"], prop=legend_props, loc="upper left",  frameon=False)
        plt.xlabel("Correlation Values", fontsize=18, weight="bold")
        plt.xticks(fontsize=18, weight="bold")
        plt.yticks(fontsize=18, weight="bold")
        plt.ylabel("CDF", fontsize=18, weight="bold")
        plt.savefig(
            Constants.BASE_PATH +"plots/" + "aggregate_project_analysis.pdf",
            bbox_inches='tight')
        plt.show()


    

    


# a = AggregateAnalysis()
# a.process()