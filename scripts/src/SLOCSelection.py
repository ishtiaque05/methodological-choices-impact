import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from FileUtil import FileUtil
from Util import Util
from constants import Constants
from pathlib import Path
import scipy.stats as stats
import seaborn as sns
import stats.CliffDelta as cld
from scipy import stats


class SLOCSelection:
    def __init__(self, apply_change_filter=False):
        self.apply_change_filter = apply_change_filter

    def process(self, refAge, age_threshold, apply_change_filter=False, exclude_method=True):
        result = []
        print("Start creating sloc selection dataset ....")
        if apply_change_filter:
            outFile = Constants.BASE_PATH + "sloc/sloc_design_onlyChangedM_" + str(
                age_threshold) + ".json"
        else:
            outFile = Constants.BASE_PATH + "sloc/sloc_design_" + str(
                age_threshold) + ".json"
        for json_file in Path(Constants.PROCESSED_DATA).rglob('*'):
            repo = json_file.name.replace(".json", "")
            data = FileUtil.load_json(json_file)
            bugdata = FileUtil.load_json(Constants.BASE_PATH + "bugData/" + repo + ".json")

            for m in data:
                method = data[m]
                # consider method with atleast one revisions
                if apply_change_filter:
                    if len(method["changeDates"]) == 1:
                        continue

                if exclude_method:
                    if method["Age"] < refAge:
                        continue

                introSLOC = method["sloc"][0]
                slocs = []
                lastSLOC = None
                mtdBugData = bugdata[m]
                bugs = 0
                total = 0

                track = 0
                for i in range(1, len(method["changeDates"])):
                    track = 1
                    total += 1

                    if mtdBugData["exactBug0Match"][i] == True:
                        bugs += 1
                    if method["changeDates"][i] > age_threshold:
                        lastSLOC = method["sloc"][i - 1]
                        break
                    slocs.append(method["sloc"][i])

                if lastSLOC == None:
                    lastSLOC = method["sloc"][-1]


                if track == 0 or len(slocs) == 0:
                    slocs = [method["sloc"][0]]

                intro = introSLOC
                last = lastSLOC
                slocs = np.array(slocs)
                avg = np.mean(slocs)
                median = np.median(slocs)
                std = np.std(slocs)

                result.append({
                    "intro": int(intro),
                    "last": int(last),
                    "avg": float(avg),
                    "median": float(median),
                    "std": float(std),
                    "bug": int(bugs),
                    "totalChange": int(total),
                    "isGetterSetter": method["isGetter"][0] or method["isSetter"][0],
                    "repo": method['repo']
                })

        FileUtil.save_json(outFile, result)
        print("Done preparing dataset for sloc selection....")

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

    def calculate_corr(self, age_threshold, apply_change_filter=False):
        print("Start computing corr for sloc selection....")
        if apply_change_filter:
            result = FileUtil.load_json(
                Constants.BASE_PATH + "sloc/sloc_design_onlyChangedM_" + str(age_threshold) + ".json")
            outFile = Constants.BASE_PATH + "sloc/sloc_design_corr_onlyChangedM_" + str(
                age_threshold) + ".csv"
        else:
            result = FileUtil.load_json(
                Constants.BASE_PATH + "sloc/sloc_design_" + str(age_threshold) + ".json")
            outFile = Constants.BASE_PATH + "sloc/sloc_design_corr_" + str(age_threshold) + ".csv"

        df = pd.DataFrame.from_dict(result)
        data = []
        for repo in Constants.ALL_MINED_REPOS:
            repo_data = df[df["repo"] == repo]

            self.append_corr_data(data, "intro", "totalChange", repo_data, repo)
            self.append_corr_data(data, "last", "totalChange", repo_data, repo)
            self.append_corr_data(data, "avg", "totalChange", repo_data, repo)
            self.append_corr_data(data, "median", "totalChange", repo_data, repo)
            self.append_corr_data(data, "std", "totalChange", repo_data, repo)
            
            self.append_corr_data(data, "intro", "bug", repo_data, repo)
            self.append_corr_data(data, "last", "bug", repo_data, repo)
            self.append_corr_data(data, "avg", "bug", repo_data, repo)
            self.append_corr_data(data, "median", "bug", repo_data, repo)
            self.append_corr_data(data, "std", "bug", repo_data, repo)

        pd.DataFrame.from_dict(data).to_csv(outFile)
        print("Done computing corr for sloc selection....")

    def append_corr_data(self, data, grp1, grp2, repo_data, repo):
        between = grp1 + "SLOC_vs_" + grp2
        data.append(self.apply_stats(repo_data[grp1], repo_data[grp2], between, repo, stats_to_apply="kendall"))
        

    def plot_cdf(self, age_threshold, apply_change_filter=False):
        if apply_change_filter:
            inFile = Constants.BASE_PATH + "sloc/sloc_design_corr_onlyChangedM_" + str(
                age_threshold) + ".csv"
            filename_suffix = "_onlyChange.pdf"
        else:
            filename_suffix = ".pdf"
            inFile = Constants.BASE_PATH + "sloc/sloc_design_corr_" + str(age_threshold) + ".csv"

        data = pd.read_csv(inFile)
        data = data[data["type"] == "kendall"]
        not_significant_data = data[data["significant"] == 'no']
        not_significant_data.to_csv(Constants.BASE_PATH + "sloc/sloc_design_not_sig_kendall.csv")

        self.render_graph(data, "totalChange", "rq1_sloc_measures_vs_revisions" + filename_suffix, "sloc_vs_all_changes",
                          age_threshold)
    
        self.render_graph(data, "bug", "rq1_sloc_measures_vs_bugs" + filename_suffix, "sloc_vs_bugCount", age_threshold)

    def render_graph(self, data, lbl, filename, versioning_grp, age_threshold):
        # Read age 730 data here
        if versioning_grp and self.apply_change_filter == False:
            age730 = pd.read_csv(
                Constants.BASE_PATH + "age/all_age_norm_data_without_x_years_methods.csv")
            age730 = age730[(age730["type"] == "kendall") & (age730["group"] == versioning_grp) & (age730["age_threshold"] == age_threshold)]
            age730.to_csv(Constants.BASE_PATH + "sloc/versioning_730_all_" + versioning_grp + ".csv")
            outFile = Constants.BASE_PATH + "stats/rq1_cliff_delta_all_corr_between_diff_sloc_vs_" + lbl + ".csv"
        elif self.apply_change_filter:
            age730 = pd.read_csv(
                Constants.BASE_PATH + "age/all_age_norm_data_without_x_years_methods_onlyChangedM.csv")
            age730 = age730[(age730["type"] == "kendall") & (age730["group"] == versioning_grp) & (age730["age_threshold"] == age_threshold)]
            age730.to_csv(Constants.BASE_PATH + "sloc/versioning_730_modified_once_" + versioning_grp + ".csv")
            outFile = Constants.BASE_PATH + "stats/rq1_cliff_delta_onlychangedM_all_corr_between_diff_sloc_vs_" + lbl + ".csv"

        introGrp = "introSLOC_vs_" + lbl
        lastGrp = "lastSLOC_vs_" + lbl
        medianGrp = "medianSLOC_vs_" + lbl
        avgGrp = "avgSLOC_vs_" + lbl
        stdGrp = "stdSLOC_vs_" + lbl

        introRev = data[data["group"] == introGrp]
        lastRev = data[data["group"] == lastGrp]
        avgRev = data[data["group"] == avgGrp]
        medianRev = data[data["group"] == medianGrp]
        stdRev = data[data["group"] == stdGrp]
       

        result = []
        result.append(self.apply_cliff_delta(introRev["corr"], lastRev["corr"], introGrp, lastGrp))
        result.append(self.apply_cliff_delta(introRev["corr"], avgRev["corr"], introGrp, avgGrp))
        result.append(self.apply_cliff_delta(introRev["corr"], medianRev["corr"], introGrp, medianGrp))
        result.append(self.apply_cliff_delta(introRev["corr"], stdRev["corr"], introGrp, stdGrp))
       
        result.append(self.apply_cliff_delta(lastRev["corr"], avgRev["corr"], lastGrp, avgGrp))
        result.append(self.apply_cliff_delta(lastRev["corr"], medianRev["corr"], lastGrp, medianGrp))
        result.append(self.apply_cliff_delta(lastRev["corr"], stdRev["corr"], lastGrp, stdGrp))
        

        result.append(self.apply_cliff_delta(avgRev["corr"], medianRev["corr"], avgGrp, medianGrp))
        result.append(self.apply_cliff_delta(avgRev["corr"], stdRev["corr"], avgGrp, stdGrp))
        
        result.append(self.apply_cliff_delta(medianRev["corr"], stdRev["corr"], medianGrp, stdGrp))

        if versioning_grp:
            result.append(
                self.apply_cliff_delta(introRev["corr"], age730["corr"], introGrp, "versioned_" + versioning_grp))
            result.append(
                self.apply_cliff_delta(lastRev["corr"], age730["corr"], lastGrp, "versioned_" + versioning_grp))
            result.append(
                self.apply_cliff_delta(medianRev["corr"], age730["corr"], medianGrp, "versioned_" + versioning_grp))
            result.append(self.apply_cliff_delta(avgRev["corr"], age730["corr"], avgGrp, "versioned_" + versioning_grp))
            result.append(self.apply_cliff_delta(stdRev["corr"], age730["corr"], stdGrp, "versioned_" + versioning_grp))
            
        pd.DataFrame.from_dict(result).to_csv(outFile)

        print("Save corr in {0}".format(outFile))

        sns.set_style("whitegrid")
        # sns.set_context(font_scale=1.2)
        plt.figure(figsize=(7.5, 6))
        ax = sns.ecdfplot(introRev, x=introRev["corr"], linewidth=2, marker="1", markersize=15, markevery=5)
        sns.ecdfplot(lastRev, x=lastRev["corr"], linewidth=2, marker="*", markersize=15, ax=ax, markevery=5)
        sns.ecdfplot(avgRev, x=avgRev["corr"], linewidth=2, marker=">", markersize=15, ax=ax, markevery=5)
        sns.ecdfplot(medianRev, x=medianRev["corr"], linewidth=2, marker=".", markersize=15, ax=ax, markevery=5)
        sns.ecdfplot(stdRev, x=stdRev["corr"], linewidth=2, marker="x", markersize=15, ax=ax, markevery=5)
        
        if versioning_grp:
            sns.ecdfplot(age730, x=age730["corr"], linewidth=2, marker="h", markersize=15, ax=ax, markevery=5)
            lgnds = ["Intro", "Last", "Mean", "Median", "Std. Dev", "SLOCVersion"]
            # lgnds = ["Intro", "Last", "Mean", "Median", "Std. Dev", "SumDiff", "SumEdit", "SLOCVersion"]
        else:
            lgnds = ["Intro", "Last", "Mean", "Median", "Std. Dev"]

        # plt.legend(lgnds, bbox_to_anchor=(0.5, 1.15), borderaxespad=0, ncol=3, loc="upper center", fontsize=12)
        legend_properties = {'weight': 'bold', 'size': 18, 'family': "monospace"}
        plt.legend(lgnds, prop=legend_properties, loc="lower right")
        # plt.legend(lgnds, fontsize=18, prop=legend_properties)
        plt.xlabel("Correlation Values", fontsize=18, weight="bold")
        ax.set_xlim(-0.18, 0.6)
        plt.xticks(fontsize=18, weight='bold')
        plt.yticks(fontsize=18, weight='bold')
        plt.ylabel("CDF", fontsize=18, weight="bold")
        plt.savefig(
            Constants.BASE_PATH + "plots/" + filename,
            bbox_inches='tight')
        plt.show()

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

    
# s = SLOCSelection(apply_change_filter=False)
# s.process(730, 730, apply_change_filter=False, exclude_method=True)  # creating sloc design json with all the data
# s.calculate_corr(730, apply_change_filter=False) # calculating corr
# s.plot_cdf(730, apply_change_filter=False)
# s.plot_cdf(730, apply_change_filter=False)

# s.explore("totalChange", ["introSLOC", "lastSLOC", "avgSLOC", "medianSLOC", "stdSLOC", "sumSLOC"])
# s.explore("rev", ["introSLOC", "lastSLOC", "avgSLOC", "medianSLOC", "stdSLOC", "sumSLOC"])
# s.explore("bug", ["introSLOC", "lastSLOC", "avgSLOC", "medianSLOC", "stdSLOC", "sumSLOC"])

# s.compare_with_versioning_sloc(730)
