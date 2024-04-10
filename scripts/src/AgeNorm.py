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

class AgeNorm:
    def __init__(self):
        self.all_age = []
        # 0, 183, 365, 730, 1095, 1460, 1825
        self.AGES = [0, 183, 365, 730, 1095, 1460]
       

    def process(self):
        for json_file in Path(Constants.PROCESSED_DATA).rglob('*'):
            repo = json_file.name.replace(".json", "")
            print("Processing {0}...".format(repo))
            data = FileUtil.load_json(json_file)
            bugdata = FileUtil.load_json(Constants.BASE_PATH + "bugData/" + repo + ".json")
            for m in data:
                method = data[m]
                mtdBugData = bugdata[m]
                self.all_age.append({
                    "age": method["changeDates"][-1],
                    "rev": len(method["changeDates"]) - 1,
                    "bug": mtdBugData["exactBug0Match"][1:].count(True),
                    "repo": method["repo"]
                })
        FileUtil.save_json(Constants.BASE_PATH + "age/all_age_bug_rev.json", self.all_age)
        print("Saved all_age_bug_rev.json.....")
        self.age_vs_bug_and_rev()

    def age_vs_bug_and_rev(self):
        if not self.all_age:
            self.all_age = FileUtil.load_json(Constants.BASE_PATH + "age/all_age_bug_rev.json")

        df = pd.DataFrame.from_dict(self.all_age)
        result = []

        result.append(
            self.apply_stats(df["age"], df["rev"], "Age_vs_Revisions", "all", stats_to_apply="kendall", age_threshold=0))

        result.append(
            self.apply_stats(df["age"], df["bug"], "Age_vs_Bug", "all", stats_to_apply="kendall", age_threshold=0))

        result_df = pd.DataFrame.from_dict(result)
        print("Corr of age with revisions and bugs:")
        print(result_df)
        result_df.to_csv(Constants.BASE_PATH + "age/all_age_bug_rev.csv")
        print("Done process age vs bug vs rev........")

    def age_with_versioning(self, AGE_THRESHOLD, apply_change_filter=False):
        result = {
            "Age_threshold": AGE_THRESHOLD,
            "data": []
        }
        if apply_change_filter:
            outFile = Constants.BASE_PATH + "age/age_norm_onlyChangedM_" + str(AGE_THRESHOLD) + ".json"
        else:
            outFile = Constants.BASE_PATH + "age/age_norm_" + str(AGE_THRESHOLD) + ".json"

        for json_file in Path(Constants.PROCESSED_DATA).rglob('*'):
            repo = json_file.name.replace(".json", "")
            data = FileUtil.load_json(json_file)
            bugdata = FileUtil.load_json(Constants.BASE_PATH + "bugData/" + repo + ".json")
            negCount = 0
            for method in data:
                method_details = data[method]
                mtdBugData = bugdata[method]
               
                if method_details["Age"] <= AGE_THRESHOLD and method_details["Age"] > 0:
                    shouldSkipXmethods = True
                else:
                    shouldSkipXmethods = False

                if apply_change_filter:
                    if len(method_details["changeDates"]) == 1:
                        continue

                sloc_version = {}
                track = 0
                for i in range(1, len(method_details["diffSizes"])):
                    track = 1
                    if method_details["changeDates"][i] > AGE_THRESHOLD:
                        if AGE_THRESHOLD != 0:
                            break

                    prevSLOC = method_details["sloc"][i - 1]
                    if prevSLOC not in sloc_version:
                        sloc_version[prevSLOC] = {
                            "allChanges": 1,
                            "essentialChanges": 1 if method_details["isEssentialChange"][i] else 0,
                            "bodychanges": 1 if Util.is_body_change(method_details["changeTypes"][i]) else 0,
                            "minorchanges": 1 if not method_details["isEssentialChange"][i] else 0,
                            "diffSizes": method_details["diffSizes"][i],
                            "newAdditions": method_details["newAdditions"][i],
                            "isGetterOrSetter": method_details["isGetter"][i] or method_details["isSetter"][i],
                            "editDistance": method_details["editDistance"][i],
                            "repo": method_details["repo"],
                            "shouldSkipXMethods": shouldSkipXmethods
                        }
                        if mtdBugData["exactBug0Match"][i]:
                            sloc_version[prevSLOC]["bugCount"] = 1
                        else:
                            sloc_version[prevSLOC]["bugCount"] = 0
                    else:
                        sloc_version[prevSLOC]["allChanges"] += 1

                        essentialChanges = 1 if method_details["isEssentialChange"][i] else 0
                        bodychanges = 1 if Util.is_body_change(method_details["changeTypes"][i]) else 0
                        minorchanges = 1 if not method_details["isEssentialChange"][i] else 0

                        sloc_version[prevSLOC]["essentialChanges"] += essentialChanges
                        sloc_version[prevSLOC]["bodychanges"] += bodychanges
                        sloc_version[prevSLOC]["minorchanges"] += minorchanges

                        sloc_version[prevSLOC]["diffSizes"] += method_details["diffSizes"][i]
                        sloc_version[prevSLOC]["newAdditions"] += method_details["newAdditions"][i]
                        sloc_version[prevSLOC]["editDistance"] += method_details["editDistance"][i]
                        if mtdBugData["exactBug0Match"][i]:
                            sloc_version[prevSLOC]["bugCount"] += 1

                if track == 0:
                    sloc_version[method_details["sloc"][0]] = {
                        "allChanges": 0,
                        "essentialChanges": 0,
                        "bodychanges": 0,
                        "minorchanges": 0,
                        "diffSizes": 0,
                        "newAdditions": 0,
                        "bugCount": 0,
                        "editDistance": 0,
                        "shouldSkipXMethods": shouldSkipXmethods,
                        "isGetterOrSetter": method_details["isGetter"][0] or method_details["isSetter"][0],
                        "repo": method_details["repo"]
                    }

                for sloc in sloc_version:
                    result["data"].append({
                        "sloc": int(sloc),
                        "allChanges": sloc_version[sloc]["allChanges"],
                        "essentialChanges": sloc_version[sloc]["essentialChanges"],
                        "bodychanges": sloc_version[sloc]["bodychanges"],
                        "minorchanges": sloc_version[sloc]["minorchanges"],
                        "diffSizes": sloc_version[sloc]["diffSizes"],
                        "newAdditions": sloc_version[sloc]["newAdditions"],
                        "editDistance": sloc_version[sloc]["editDistance"],
                        "change_by_sloc": round(sloc_version[sloc]["essentialChanges"] / int(sloc), 4),
                        "bugCount": sloc_version[sloc]["bugCount"],
                        "repo": sloc_version[sloc]["repo"],
                        "shouldSkipXMethods": sloc_version[sloc]["shouldSkipXMethods"],
                        "isGetterOrSetter": sloc_version[sloc]["isGetterOrSetter"]
                    })

        FileUtil.save_json(outFile, result)
        print("Done age norm for age threshold {0}".format(AGE_THRESHOLD))

    # interval = [183, 365, 730, 1095, 1460, 5]
    def interval_age_versioning(self, age_interval=[0, 183], exclude_x_methods=False):
        interval_range = str(age_interval[0]) + "-" + str(age_interval[1])
        result = {
            "interval": interval_range,
            "data": []
        }

        if exclude_x_methods:
            outfile = Constants.BASE_PATH + "interval/interval_age_excluded_" + interval_range + ".json"
        else:
            outfile = Constants.BASE_PATH + "interval/interval_age_" + interval_range + ".json"

        for json_file in Path(Constants.PROCESSED_DATA).rglob('*'):
            repo = json_file.name.replace(".json", "")
            data = FileUtil.load_json(json_file)
            bugdata = FileUtil.load_json(Constants.BASE_PATH + "bugData/" + repo + ".json")
            for method in data:
                method_details = data[method]
                mtdBugData = bugdata[method]
                # if method_details["Age"] <= AGE_THRESHOLD:
                #     continue

                if exclude_x_methods:
                    if age_interval[1] != 5:
                        if method_details["Age"] < age_interval[1] and method_details["Age"] > 0:
                            continue
                    elif age_interval[1] == 5:
                        if method_details["Age"] < age_interval[0] and method_details["Age"] > 0:
                            continue

                sloc_version = {}
                track = 0
                for i in range(1, len(method_details["diffSizes"])):
                    track = 1

                    if age_interval[1] != 5:

                        if age_interval[1] >= method_details["changeDates"][i] >= age_interval[0]:
                            interval = interval_range
                        else:
                            continue

                    if age_interval[1] == 5 and not (method_details["changeDates"][i] >= age_interval[0]):
                        continue

                    # if method_details["isEssentialChange"][i]:
                    prevSLOC = str(method_details["sloc"][i - 1])
                    if prevSLOC not in sloc_version:
                        sloc_version[prevSLOC] = {
                            "allChanges": 1,
                            "essentialChanges": 1 if method_details["isEssentialChange"][i] else 0,
                            "bodychanges": 1 if Util.is_body_change(method_details["changeTypes"][i]) else 0,
                            "minorchanges": 1 if not method_details["isEssentialChange"][i] else 0,
                            "diffSizes": method_details["diffSizes"][i],
                            "newAdditions": method_details["newAdditions"][i],
                            "isGetterOrSetter": method_details["isGetter"][i] or method_details["isSetter"][i],
                            "editDistance": method_details["editDistance"][i],
                            "repo": method_details["repo"],
                            "interval": interval_range
                        }
                        if mtdBugData["exactBug0Match"][i]:
                            sloc_version[prevSLOC]["bugCount"] = 1
                        else:
                            sloc_version[prevSLOC]["bugCount"] = 0
                    else:
                        sloc_version[prevSLOC]["allChanges"] += 1

                        essentialChanges = 1 if method_details["isEssentialChange"][i] else 0
                        bodychanges = 1 if Util.is_body_change(method_details["changeTypes"][i]) else 0
                        minorchanges = 1 if not method_details["isEssentialChange"][i] else 0

                        sloc_version[prevSLOC]["essentialChanges"] += essentialChanges
                        sloc_version[prevSLOC]["bodychanges"] += bodychanges
                        sloc_version[prevSLOC]["minorchanges"] += minorchanges

                        sloc_version[prevSLOC]["diffSizes"] += method_details["diffSizes"][i]
                        sloc_version[prevSLOC]["newAdditions"] += method_details["newAdditions"][i]
                        sloc_version[prevSLOC]["editDistance"] += method_details["editDistance"][i]
                        if mtdBugData["exactBug0Match"][i]:
                            sloc_version[prevSLOC]["bugCount"] += 1

                if track == 0:
                    if age_interval[0] == 0:
                        sloc_version[method_details["sloc"][0]] = {
                            "allChanges": 0,
                            "essentialChanges": 0,
                            "bodychanges": 0,
                            "minorchanges": 0,
                            "diffSizes": 0,
                            "newAdditions": 0,
                            "bugCount": 0,
                            "editDistance": 0,
                            "isGetterOrSetter": method_details["isGetter"][0] or method_details["isSetter"][0],
                            "interval": interval_range,
                            "repo": method_details["repo"]
                        }

                for sc in sloc_version:
                    sloc = int(sc)
                    # interval = int(sloc_interval[1])
                    result["data"].append({
                        "sloc": int(sloc),
                        "allChanges": sloc_version[sc]["allChanges"],
                        "essentialChanges": sloc_version[sc]["essentialChanges"],
                        "bodychanges": sloc_version[sc]["bodychanges"],
                        "minorchanges": sloc_version[sc]["minorchanges"],
                        "diffSizes": sloc_version[sc]["diffSizes"],
                        "newAdditions": sloc_version[sc]["newAdditions"],
                        "editDistance": sloc_version[sc]["editDistance"],
                        "bugCount": sloc_version[sc]["bugCount"],
                        "repo": sloc_version[sc]["repo"],
                        "interval": interval_range,
                        "isGetterOrSetter": sloc_version[sc]["isGetterOrSetter"]
                    })

        FileUtil.save_json(outfile, result)
        print("Done preparing data in interval {0} and {1}".format(age_interval[0], age_interval[1]))

    def calc_interval_corr(self, exclude_x_methods=False):
        result = []
        for json_file in Path(Constants.BASE_PATH + "interval/").rglob('*'):
            data = FileUtil.load_json(json_file)
            interval_range = data["interval"]
            print("Processing interval {0}".format(interval_range))
            df = pd.DataFrame.from_dict(data["data"])
            for repo in Constants.ALL_MINED_REPOS:
                repo_data = df[df["repo"] == repo]
                if not repo_data.empty:
                    result.append(
                        self.apply_stats(
                            repo_data["sloc"],
                            repo_data["allChanges"],
                            "sloc-allChanges-" + interval_range,
                            repo,
                            stats_to_apply="kendall",
                            age_threshold=interval_range
                        )
                    )

                    result.append(
                        self.apply_stats(
                            repo_data["sloc"],
                            repo_data["bugCount"],
                            "sloc-bugCount-" + interval_range,
                            repo,
                            stats_to_apply="kendall",
                            age_threshold=interval_range
                        )
                    )

        pd.DataFrame.from_dict(result).to_csv(Constants.BASE_PATH + "age/all_corr_interval_age_data.csv")
        print("Done calculating corr....")

    # def calc_cliff_delta_for_age_interval(self, grp, intervals=[183, 365, 730, 1095, 1825, 6]):
    #     df = pd.read_csv(Constants.BASE_PATH + "age/all_corr_interval_age_data.csv")

    #     # intervals = [365, 730, 1095, 1825, 6]
    #     yearHalf = df[(df["age_threshold"] == intervals[0]) & (df["group"] == grp)]
    #     year1 = df[(df["age_threshold"] == intervals[1]) & (df["group"] == grp)]
    #     year2 = df[(df["age_threshold"] == intervals[2]) & (df["group"] == grp)]
    #     year3 = df[(df["age_threshold"] == intervals[3]) & (df["group"] == grp)]
    #     year5 = df[(df["age_threshold"] == intervals[4]) & (df["group"] == grp)]
    #     after5 = df[(df["age_threshold"] == intervals[5]) & (df["group"] == grp)]
    #     result = []

    #     result.append(self.apply_cliff_delta(yearHalf["corr"], year1["corr"], "0.5yr", "1yr"))
    #     result.append(self.apply_cliff_delta(yearHalf["corr"], year2["corr"], "0.5yr", "2yr"))
    #     result.append(self.apply_cliff_delta(yearHalf["corr"], year3["corr"], "0.5yr", "3yr"))
    #     # result.append(self.apply_cliff_delta(yearHalf["corr"], year5["corr"], "0.5yr", "5yr"))
    #     result.append(self.apply_cliff_delta(yearHalf["corr"], after5["corr"], "0.5yr", "after5yr"))

    #     result.append(self.apply_cliff_delta(year1["corr"], year2["corr"], "1yr", "2yr"))
    #     result.append(self.apply_cliff_delta(year1["corr"], year3["corr"], "1yr", "3yr"))
    #     # result.append(self.apply_cliff_delta(year1["corr"], year5["corr"], "1yr", "5yr"))
    #     result.append(self.apply_cliff_delta(year1["corr"], after5["corr"], "1yr", "after5yr"))

    #     result.append(self.apply_cliff_delta(year2["corr"], year3["corr"], "2yr", "3yr"))
    #     # result.append(self.apply_cliff_delta(year2["corr"], year5["corr"], "2yr", "5yr"))
    #     result.append(self.apply_cliff_delta(year2["corr"], after5["corr"], "2yr", "after5yr"))

    #     # result.append(self.apply_cliff_delta(year3["corr"], year5["corr"], "3yr", "5yr"))
    #     result.append(self.apply_cliff_delta(year3["corr"], after5["corr"], "3yr", "after5yr"))
    #     # result.append(self.apply_cliff_delta(year5["corr"], after5["corr"], "5yr", "after5yr"))

    #     pd.DataFrame.from_dict(result).to_csv(Constants.BASE_PATH + "age/interval_wise_corr_" + grp + ".csv")
    #     print("Done.......")
    #     print("Plotting graph....")
    #     sns.ecdfplot(yearHalf, x=yearHalf["corr"], linewidth=1.0, marker="o", markersize=5)
    #     sns.ecdfplot(year1, x=year1["corr"], linewidth=1.0, marker="o", markersize=5)
    #     sns.ecdfplot(year2, x=year2["corr"], linewidth=1.0, marker="*", markersize=5)
    #     sns.ecdfplot(year3, x=year3["corr"], linewidth=1.0, marker="v", markersize=5)
    #     sns.ecdfplot(year5, x=year5["corr"], linewidth=1.0, marker="d", markersize=5)
    #     sns.ecdfplot(after5, x=after5["corr"], linewidth=1.0, marker="3", markersize=5)
    #     plt.legend(["0-0.5yr" , "0.5-1yr", "1-2yr", "2-3yr", "3-5yr", "after 5 yr"])
    #     plt.savefig(
    #         Constants.BASE_PATH + "age/" + grp + "_interval_change_cdf.png",
    #         bbox_inches='tight')
    #     plt.show()

    def apply_stats(self, x1, x2, label, repo, stats_to_apply="kendall", age_threshold=0):
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
            "type": stats_to_apply,
            "age_threshold": age_threshold
        }

    def calculate_corr(self, AGES=[0, 183, 365, 730, 1095, 1460], should_exclued_less_than_x_years=False, apply_change_filter=False):
        if should_exclued_less_than_x_years:
            filename_to_save = "age/all_age_norm_data_without_x_years_methods"
        else:
            filename_to_save = "age/all_age_norm_data"

        if apply_change_filter:
            filename_to_save = filename_to_save + "_onlyChangedM.csv"
        elif should_exclued_less_than_x_years:
            filename_to_save = filename_to_save + ".csv"
        else:
            filename_to_save = filename_to_save + ".csv"


        print("Start processing....")
        result = []
        for age in AGES:
            print("Processing age {0}".format(age))
            if apply_change_filter:
                inFile = Constants.BASE_PATH + "age/age_norm_onlyChangedM_" + str(age) + ".json"
            else:
                inFile = Constants.BASE_PATH + "age/age_norm_" + str(age) + ".json"
            data = FileUtil.load_json(inFile)
            if data["Age_threshold"] == age:
                df = pd.DataFrame.from_dict(data['data'])
                if should_exclued_less_than_x_years:
                    df = df[df["shouldSkipXMethods"] == False]

                # print("Number of methods {0} for age {1}...".format(df.shape[0], age))
                for repo in Constants.ALL_MINED_REPOS:
                    repo_data = df[df["repo"] == repo]
                    print("Processing for repo {0}".format(repo))
                    # print("Number of methods {0} for age {1} in repo {2}...".format(repo_data.shape[0], age, repo))
                    try:
                        if not repo_data.empty:
                          
                            result.append(
                                self.apply_stats(repo_data["sloc"], repo_data["allChanges"],
                                                 "sloc_vs_all_changes", repo,
                                                 stats_to_apply="kendall", age_threshold=age))

                            result.append(
                                self.apply_stats(repo_data["sloc"], repo_data["essentialChanges"],
                                                 "sloc_vs_essential_changes", repo,
                                                 stats_to_apply="kendall", age_threshold=age))

                            result.append(
                                self.apply_stats(repo_data["sloc"], repo_data["bodychanges"],
                                                 "sloc_vs_bodychanges", repo,
                                                 stats_to_apply="kendall", age_threshold=age))

                            result.append(
                                self.apply_stats(repo_data["sloc"], repo_data["minorchanges"],
                                                 "sloc_vs_minorchanges", repo,
                                                 stats_to_apply="kendall", age_threshold=age))

                            result.append(
                                self.apply_stats(repo_data["sloc"], repo_data["bugCount"], "sloc_vs_bugCount", repo,
                                                 stats_to_apply="kendall", age_threshold=age))
                            
                            result.append(
                                self.apply_stats(repo_data["sloc"], repo_data["newAdditions"], "sloc_vs_newAdditions", repo,
                                                 stats_to_apply="kendall", age_threshold=age))
                            
                            result.append(
                                self.apply_stats(repo_data["sloc"], repo_data["diffSizes"], "sloc_vs_diffSizes", repo,
                                                 stats_to_apply="kendall", age_threshold=age))
                            
                            result.append(
                                self.apply_stats(repo_data["sloc"], repo_data["editDistance"], "sloc_vs_editDistance", repo,
                                                 stats_to_apply="kendall", age_threshold=age))
                    except Exception as e:
                        print(e)
            else:
                print("File does not exist. Create files first")
                break

        pd.DataFrame.from_dict(result).to_csv(Constants.BASE_PATH + filename_to_save)
     
        print("Done processing age norm csv.....")


    def plot_corr_cdf(self, stats_to_use, filter_less_than_x_age=False):
        # 0, 183, 365, 730, 1825
        if filter_less_than_x_age:
            data = pd.read_csv(Constants.BASE_PATH + "age/all_age_norm_data_without_x_years_methods.csv")
        else:
            data = pd.read_csv(Constants.BASE_PATH + "age/all_age_norm_data.csv")

        not_sig_data = data[(data["significant"] == "no") & (data["type"] == stats_to_use)]
        not_sig_data.to_csv(Constants.BASE_PATH + "age/not_sig_age_data.csv")

        data = data[data["type"] == stats_to_use]
      
        all_change_filename = 'sloc_vs_all_changes_age'
        bug_filename = "sloc_vs_bug_age"
       
        if filter_less_than_x_age:
            all_change_filename = "rq3_" + all_change_filename
            bug_filename = "rq3_" + bug_filename
            
        self.render_graph(data, 'sloc_vs_all_changes', all_change_filename + ".pdf", self.AGES)
        self.render_graph(data, 'sloc_vs_bugCount', bug_filename + ".pdf", self.AGES)


    def render_graph(self, data, grp, filename, ages):
        age0 = data[(data["age_threshold"] == ages[0]) & (data["group"] == grp)]
        self.print_repo_not_in_list(age0, ages[0], grp)

        age183 = data[(data["age_threshold"] == ages[1]) & (data["group"] == grp)]
        self.print_repo_not_in_list(age183, ages[1], grp)

        age365 = data[(data["age_threshold"] == ages[2]) & (data["group"] == grp)]
        self.print_repo_not_in_list(age365, ages[2], grp)

        age730 = data[(data["age_threshold"] == ages[3]) & (data["group"] == grp)]
        self.print_repo_not_in_list(age730, ages[3], grp)

        age1095 = data[(data["age_threshold"] == ages[4]) & (data["group"] == grp)]
        self.print_repo_not_in_list(age1095, ages[4], grp)

        age1460 = data[(data["age_threshold"] == ages[5]) & (data["group"] == grp)]
        self.print_repo_not_in_list(age1095, ages[5], grp)

    
        result = []
        result.append(self.apply_cliff_delta(age0["corr"], age183["corr"], "age0", "age183"))
        result.append(self.apply_cliff_delta(age0["corr"], age365["corr"], "age0", "age365"))
        result.append(self.apply_cliff_delta(age0["corr"], age730["corr"], "age0", "age730"))
        result.append(self.apply_cliff_delta(age0["corr"], age1095["corr"], "age0", "age1095"))
        result.append(self.apply_cliff_delta(age0["corr"], age1460["corr"], "age0", "age1460"))

        result.append(self.apply_cliff_delta(age183["corr"], age365["corr"], "age183", "age365"))
        result.append(self.apply_cliff_delta(age183["corr"], age730["corr"], "age183", "age730"))
        result.append(self.apply_cliff_delta(age183["corr"], age1095["corr"], "age183", "age1095"))
        result.append(self.apply_cliff_delta(age183["corr"], age1460["corr"], "age183", "age1460"))

        result.append(self.apply_cliff_delta(age365["corr"], age730["corr"], "age365", "age730"))
        result.append(self.apply_cliff_delta(age365["corr"], age1095["corr"], "age365", "age1095"))
        result.append(self.apply_cliff_delta(age365["corr"], age1460["corr"], "age365", "age1460"))

        result.append(self.apply_cliff_delta(age730["corr"], age1095["corr"], "age730", "age1095"))
        result.append(self.apply_cliff_delta(age730["corr"], age1460["corr"], "age730", "age1460"))

        result.append(self.apply_cliff_delta(age1095["corr"], age1460["corr"], "age1095", "age1460"))

        tmp_df = pd.DataFrame.from_dict(result)
        tmp_df.to_csv(Constants.BASE_PATH + "stats/rq3_cliff_delta_age_norm_"  + filename +".csv")

        sns.set_style("whitegrid")
        sns.set_context(font_scale=3)
        plt.figure(figsize=(7.5, 6))

        sns.ecdfplot(age183, x=age183["corr"], linewidth=2, marker="X", markersize=15, markevery=5)
        sns.ecdfplot(age365, x=age365["corr"], linewidth=2, marker=">", markersize=15, markevery=5)
        sns.ecdfplot(age730, x=age730["corr"], linewidth=2, marker="<", markersize=15, markevery=5)
        sns.ecdfplot(age1095, x=age1095["corr"], linewidth=2, marker="D", markersize=15, markevery=5)
        sns.ecdfplot(age1460, x=age1460["corr"], linewidth=2, marker="o", markersize=15, markevery=5)
        sns.ecdfplot(age0, x=age0["corr"], linewidth=2, marker="*", markersize=15, markevery=5, color='hotpink', mec='hotpink', mfc='hotpink')
       
        legend_props = {"weight": "bold", "size": 18, "family": "monospace"}
        plt.legend(["0.5 yr", "1 yr", "2 yrs", "3 yrs", "4 yrs", "NoAgeCtrl."], prop=legend_props, loc="upper left",  frameon=False)
        plt.xlabel("Correlation Values", fontsize=18, weight="bold")
        plt.xticks(fontsize=18, weight="bold")
        plt.yticks(fontsize=18, weight="bold")
        plt.ylabel("CDF", fontsize=18, weight="bold")
        plt.savefig(
            Constants.BASE_PATH +"plots/" +filename,
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

    def print_repo_not_in_list(self, ageData, threshold, grp):
        if ageData.shape[0] != 53:
            not_in_list = list(set(Constants.ALL_MINED_REPOS) - set(ageData["repo"]))
            print("Age {0} not in list: {1} for grp {2}".format(threshold, not_in_list, grp))

    def process_interval_data_and_plot(self):
        df = pd.read_csv(Constants.BASE_PATH + "age/all_corr_interval_age_data.csv")
        intervals = ["0-183", "183-365", "365-730", "730-1095", "1095-1460", "1460-5"]
        r = []
        for i in range(len(intervals)):
            d1 = df[df["age_threshold"] == intervals[i]]
            for j in range(i+1, len(intervals)):
                d2 = df[df["age_threshold"] == intervals[j]]
                try:
                    for g in ["sloc-allChanges-", "sloc-bugCount-"]:
                        grp1 = g + intervals[i]
                        grp2 = g + intervals[j]
                        x1 = d1[d1["group"] == grp1]
                        x2 = d2[d2["group"] == grp2]
                        r.append(self.apply_cliff_delta(x1["corr"], x2["corr"], grp1, grp2))
                except Exception as e:
                    continue

        pd.DataFrame.from_dict(r).to_csv(Constants.BASE_PATH + "stats/rq3_interval_cliff_delta.csv")

        self.render_all_interval_for("sloc-allChanges-", df, "rq3_corr-sloc-allChanges-interval.pdf")
        self.render_all_interval_for("sloc-bugCount-", df, "rq3_corr-sloc-bugCount-interval.pdf")
        print("done...")

    def render_all_interval_for(self, grp, df, filename):
        intervals = ["0-183", "183-365", "365-730", "730-1095", "1095-1460", "1460-5"]
        ax = None
        sns.set_style("whitegrid")
        sns.set_context(font_scale=3)
        plt.figure(figsize=(7.5, 6))
        m = 0
        markers_list = ["X", ">", "<", "D", "o", "^", "*"]
        for i in intervals:
            data = df[(df["age_threshold"] == i) & (df["group"] == grp + i)]
            if not ax:
                ax = sns.ecdfplot(data, x=data["corr"], linewidth=2.0, marker=markers_list[m], markersize=15, markevery=5)
                m +=1
            else:
                sns.ecdfplot(data, x=data["corr"], linewidth=2.0, marker=markers_list[m], markersize=15, ax=ax, markevery=5)
                m += 1

        legend_props = {"weight": "bold", "size": 18, "family": "monospace"}
        plt.legend(["0-0.5 yrs", "0.5-1 yr", "1-2 yrs", "2-3 yrs", "3-4 yrs", "4+ yrs"], prop=legend_props)

        plt.xlabel("Correlation Values", fontsize=18, weight="bold")
        ax.set_xlim(-0.4, 0.4)
        plt.xticks(fontsize=18, weight="bold")
        plt.yticks(fontsize=18, weight="bold")
        plt.ylabel("CDF", fontsize=18, weight="bold")
        plt.savefig(
            Constants.BASE_PATH + "plots/" + filename,
            bbox_inches='tight')
        plt.show()

# a = AgeNorm()
# a.process() # process overall json for calculating corr
# a.age_vs_bug_and_rev() # # overall relation between age vs bug vs rev (essential changes)
#  Age threshold: 0, 183, 365, 730, 1095, 1460, 1825
# a.age_with_versioning(0)  # age data per repo
# a.age_with_versioning(183)  # age data per repo
# a.age_with_versioning(365)
# a.age_with_versioning(730)
# a.age_with_versioning(1095)

# a.age_with_versioning(0, apply_change_filter=False)
# a.age_with_versioning(90, apply_change_filter=False)
# a.age_with_versioning(120, apply_change_filter=False)
# a.age_with_versioning(183, apply_change_filter=False)
# a.age_with_versioning(365, apply_change_filter=False)
# a.age_with_versioning(730, apply_change_filter=False)
# a.age_with_versioning(1095, apply_change_filter=False)
# a.age_with_versioning(1460, apply_change_filter=False)
# a.age_with_versioning(1825, apply_change_filter=False)

# a.age_with_versioning(0, apply_change_filter=True)
# a.age_with_versioning(183, apply_change_filter=True)
# a.age_with_versioning(365, apply_change_filter=True)
# a.age_with_versioning(730, apply_change_filter=True)
# a.age_with_versioning(1095, apply_change_filter=True)
# a.age_with_versioning(1460, apply_change_filter=True)
# a.age_with_versioning(1825, apply_change_filter=True)

# a.age_with_versioning(1825)
# a.age_with_versioning(2555)

# a.calculate_corr(AGES=[0, 183, 365, 730, 1095, 1460], should_exclued_less_than_x_years=False, apply_change_filter=False) # all corr per repo
# a.plot_corr_cdf("kendall", filter_less_than_x_age=True)
# a.calculate_corr(AGES=[0, 183, 365, 730, 1095, 1460, 1825], should_exclued_less_than_x_years=True) # all corr per repo
# a.calculate_corr(AGES=[0, 183, 365, 730, 1095, 1460, 1825], should_exclued_less_than_x_years=False) # all corr per repo
# a.plot_corr_cdf("kendall", filter_less_than_x_age=True) # all cdf per repo
# a.plot_corr_cdf("kendall", filter_less_than_x_age=False) # all cdf per repo
# [365, 730, 1095, 1825]
# a.analyze_sml_grp()
# a.interval_age_versioning(age_interval=[0, 183], exclude_x_methods=True)
# a.interval_age_versioning(age_interval=[183, 365], exclude_x_methods=True)
# a.interval_age_versioning(age_interval=[365, 730], exclude_x_methods=True)
# a.interval_age_versioning(age_interval=[730, 1095], exclude_x_methods=True)
# a.interval_age_versioning(age_interval=[1095, 1460], exclude_x_methods=True)
# a.interval_age_versioning(age_interval=[1460, 5], exclude_x_methods=True)
# a.interval_age_versioning(age_interval=[0, 365], exclude_x_methods=True)
# a.interval_age_versioning([183, 365, 730, 1095, 1825], exclude_x_methods=True) # for interval analysis
# a.calc_interval_corr()
# a.process_interval_data_and_plot()

# a.calc_cliff_delta_for_age_interval("sloc_vs_essential_changes", intervals=[183, 365, 730, 1095, 1825, 6])
# a.calc_cliff_delta_for_age_interval("sloc_vs_all_changes", intervals=[183, 365, 730, 1095, 1825, 6])
# a.calc_cliff_delta_for_age_interval("sloc_vs_bugCount", intervals=[183, 365, 730, 1095, 1825, 6])
# a.explore("sloc_vs_all_changes", [0, 183, 365, 730, 1095, 1825])
# a.explore("sloc_vs_bugCount", [0, 183, 365, 730, 1095, 1825])
# a.calculate_corr(AGES=[0, 183, 365, 730, 1095, 1460], should_exclued_less_than_x_years=True, apply_change_filter=True)