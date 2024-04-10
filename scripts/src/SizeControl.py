import pandas as pd
from matplotlib import pyplot as plt

from FileUtil import FileUtil
from Util import Util
from constants import Constants
import seaborn as sns
import stats.CliffDelta as cld
import seaborn as sns
from scipy import stats
from pathlib import Path

class SizeControl:
    def process(self, age, apply_change_filter=False, should_filter_get_set=False):
        print("Start preparing dataset for size control analysis....")
        if apply_change_filter:
            inFile = Constants.BASE_PATH + "age/age_norm_onlyChangedM_" + age + ".json"
            outFile = Constants.BASE_PATH + "sizeControl/proportion_of_change_corr_age_onlyChangedM_" + age
        else:
            outFile = Constants.BASE_PATH + "sizeControl/proportion_of_change_corr_age" + age
            inFile = Constants.BASE_PATH + "age/age_norm_" + age + ".json"

        age730 = FileUtil.load_json(inFile)
        df = pd.DataFrame.from_dict(age730["data"])
        df = df[df["shouldSkipXMethods"] == False]

        if should_filter_get_set:
            df = df[df["isGetterOrSetter"] == False]
            outFile = outFile + "_no_get_set.csv"
        else:
            outFile = outFile + ".csv"

        df["bug_density"] = df["bugCount"] / df["sloc"]
        df["revision_density"] = df["allChanges"] / df["sloc"]

        result = []
        for repo in Constants.ALL_MINED_REPOS:
            repo_data = df[df["repo"] == repo]
            result.append(self.apply_stats(repo_data["sloc"], repo_data["bug_density"], "sloc_vs_bug_density", repo,
                                           stats_to_apply="kendall"))

            result.append(
                self.apply_stats(repo_data["sloc"], repo_data["revision_density"], "sloc_vs_revision_density", repo,
                                 stats_to_apply="kendall"))

        pd.DataFrame.from_dict(result).to_csv(outFile)
        print("Done calculating correlation of SLOC with bug and revision density.....")

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


    def plot_cdf(self, age, apply_change_filter=False):

        if apply_change_filter:
            inFile = Constants.BASE_PATH + "sizeControl/proportion_of_change_corr_age_onlyChangedM_" + str(age) + ".csv"
            ageInFile = Constants.BASE_PATH + "age/all_age_norm_data_onlyChangedM.csv"
        else:
            ageInFile = Constants.BASE_PATH + "age/all_age_norm_data_without_x_years_methods.csv"
            inFile = Constants.BASE_PATH + "sizeControl/proportion_of_change_corr_age" + str(age) + ".csv"
        data = pd.read_csv(inFile)

        age730 = pd.read_csv(ageInFile)
        
        age730AllRevs = age730[(age730["type"] == "kendall") & (age730["group"] == "sloc_vs_all_changes") & (age730["age_threshold"] == age)]
        age730Bug = age730[(age730["type"] == "kendall") & (age730["group"] == "sloc_vs_bugCount") & (age730["age_threshold"] == age)]

        kendall_data = data[data["type"] == "kendall"]
        not_sig_data = kendall_data[kendall_data["significant"] == "no"]
        not_sig_data.to_csv(
            Constants.BASE_PATH + "sizeControl/proportion_of_change_not_sig_age_" + str(age) + ".csv")

        sig_data = kendall_data

        bug_density = sig_data[sig_data["group"] == "sloc_vs_bug_density"]
        revision_density = sig_data[sig_data["group"] == "sloc_vs_revision_density"]

        r = []
        

        r.append(self.apply_cliff_delta(revision_density["corr"], age730AllRevs["corr"], "revision_density",
                                        "all_change"))
        
        r.append(self.apply_cliff_delta(bug_density["corr"], age730Bug["corr"], "bug_density", "bug"))
        pd.DataFrame.from_dict(r).to_csv(Constants.BASE_PATH + "stats/rq3_cliff_delta_size_control.csv")

        sns.set_style("whitegrid")
        plt.figure(figsize=(8, 6))
        sns.ecdfplot(revision_density, x=revision_density["corr"], linewidth=2.0, marker="<", markersize=15, markevery=5)
        sns.ecdfplot(age730AllRevs, x=age730AllRevs["corr"], linewidth=2.0, marker=">", markersize=15, markevery=5)
        sns.ecdfplot(bug_density, x=bug_density["corr"], linewidth=2.0, marker="*", markersize=15, markevery=5)
        sns.ecdfplot(age730Bug, x=age730Bug["corr"], linewidth=2.0, marker="o", markersize=15, markevery=5)

        plt.xlabel("Correlation Values", fontsize=18, weight="bold")
        plt.xticks(fontsize=18, weight="bold")
        plt.yticks(fontsize=18, weight="bold")
        plt.ylabel("CDF", fontsize=18, weight="bold")
        legend_props = {"weight": "bold", "size": 18, "family": "monospace"}
        plt.legend(["RevisionDensity", "#Revisions", "BugDensity", "#Bugs"], prop=legend_props, frameon=False)
        # plt.legend(["sloc_vs_bug_density", "sloc_vs_revisions_density"])
        plt.savefig(
            Constants.BASE_PATH + "plots/rq3_size_control_cdf" + str(age) + ".pdf",
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

    

    def get_set_vs_no_get_set_diff(self, age_threshold=730):
        print("Cliff delta analysis of bug and revision density with/without get and set methods....")

        withgetset = pd.read_csv(Constants.BASE_PATH + "sizeControl/proportion_of_change_corr_age" + str(age_threshold) + ".csv")
        nogetset = pd.read_csv(Constants.BASE_PATH + "sizeControl/proportion_of_change_corr_age" + str(age_threshold) + "_no_get_set.csv")

        withgetsetchange = withgetset[(withgetset["type"] == "kendall") & (withgetset["group"] == "sloc_vs_revision_density")]
        nogetsetchange = nogetset[(nogetset["type"] == "kendall") & (nogetset["group"] == "sloc_vs_revision_density")]

        withgetsetbug = withgetset[(withgetset["type"] == "kendall") & (withgetset["group"] == "sloc_vs_bug_density")]
        nogetsetbug = nogetset[(nogetset["type"] == "kendall") & (nogetset["group"] == "sloc_vs_bug_density")]

        r = []
        r.append(self.apply_cliff_delta(withgetsetchange["corr"], nogetsetchange["corr"], "revision-density-present", "revision-density-absent"))
        r.append(self.apply_cliff_delta(withgetsetbug["corr"], nogetsetbug["corr"], "bug-density-present", "bug-density-absent"))

        pd.DataFrame.from_dict(r).to_csv(Constants.BASE_PATH + "stats/rq3_cliff_delta_get_set_corr.csv")
        print("Cliff delta analysis done...")
    
    def render_boxplot(self, age, grp, filename, apply_change_filter=False, filter_getter_setter=False):
        print("Start analyzing {0} distribution of different method size...".format(grp))

        if apply_change_filter:
            inFile = Constants.BASE_PATH + "age/age_norm_onlyChangedM_" + age + ".json"
        else:
            inFile = Constants.BASE_PATH + "age/age_norm_" + age + ".json"

        ageData = FileUtil.load_json(inFile)
        df = pd.DataFrame.from_dict(ageData["data"])
        df = df[df["shouldSkipXMethods"] == False]

        if filter_getter_setter:
            df = df[df["isGetterOrSetter"] == False]
        
        df["bug_density"] = df["bugCount"] / df["sloc"] 
        df["revision_density"] = df["allChanges"] / df["sloc"]

        # Considering methods that are defective only
        if grp == "bugCount" or grp == "bug_density":
            notbuggy = int(df[df["bugCount"] == 0].shape[0])
            totalChange = int(df.shape[0])
            df = df[df["bugCount"] > 0]
            print("% of changes that are not buggy {0}".format(notbuggy/totalChange))

        small = df[df["sloc"] < 30]
        medium = df[(df["sloc"] < 60) & (df["sloc"] > 30)]
        large = df[df["sloc"] > 60]

        if filter_getter_setter:
            r = {"s": None, "m": None, "l": None}
            r["s"] = list(small[grp])
            r["m"] = list(medium[grp])
            r["l"] = list(large[grp])
            FileUtil.save_json(Constants.BASE_PATH + "sizeControl/no_get_set_sml_" + grp + ".json", r)
        else:
            r = {"s": None, "m": None, "l": None}
            r["s"] = list(small[grp])
            r["m"] = list(medium[grp])
            r["l"] = list(large[grp])
            FileUtil.save_json(Constants.BASE_PATH + "sizeControl/yes_get_set_sml_" + grp + ".json", r)


        avgS = round(small[grp].mean(),3)
        avgM = round(medium[grp].mean(), 3)
        avgL = round(large[grp].mean(), 3)

        medS = round(small[grp].median(), 3)
        medM = round(medium[grp].median(), 3)
        medL = round(large[grp].median(), 3)
        print("For group {0} \n AvgS = {1} \n AvgM = {2} \n AvgL = {3} \n medS = {4} \n medM = {5} \n medL = {6}".format(
            grp,
            avgS,
            avgM,
            avgL,
            medS,
            medM,
            medL
        ))
        sns.set_style("whitegrid")
        # sns.set_context(font_scale=1.3)
        ax = sns.boxplot(
            data=[small[grp], medium[grp], large[grp]],
            palette=[sns.xkcd_rgb["pale red"], sns.xkcd_rgb["yellow"], sns.xkcd_rgb["blue"]],
            showmeans=True,
            showfliers=False
        )

        ax.set_xticklabels(['small','medium','large'], fontsize=18, weight="bold")
        # ax.set_yticklabels(ax.get_yticks(), size=16)
        # ax.set_yscale("log")
        plt.yticks(fontsize=18, weight="bold")

        plt.savefig(
            Constants.BASE_PATH + "plots/rq2_boxplot_" + filename + "_" + grp + "age_" + age + ".pdf",
            bbox_inches='tight')
        plt.show()
        print("Done...")
    
    def size_ctrl_cliff_delta_analysis(self, grp):
        print("Start analysis of with/without get and set methods...")
        no = FileUtil.load_json(Constants.BASE_PATH + "sizeControl/no_get_set_sml_" + grp + ".json")
        yes = FileUtil.load_json(Constants.BASE_PATH + "sizeControl/yes_get_set_sml_" + grp + ".json")
        r = []
        r.append(self.apply_cliff_delta(no["s"], yes["s"], "small-filter-getset-no", "small-filter-getset-yes"))
        r.append(self.apply_cliff_delta(no["m"], yes["m"], "medium-filter-getset-no", "medium-filter-getset-yes"))
        r.append(self.apply_cliff_delta(no["l"], yes["l"], "large-filter-getset-no", "large-filter-getset-yes"))

        pd.DataFrame.from_dict(r).to_csv(Constants.BASE_PATH + "stats/rq2_get_set_no_get_set_" + grp + ".csv")
        print("done")

        t = []
        t.append(self.apply_cliff_delta(yes["l"], yes["s"], "large-getSet-present", "small-getSet-present"))
        t.append(self.apply_cliff_delta(yes["l"], yes["m"], "large-getSet-present", "medium-getSet-present"))
        t.append(self.apply_cliff_delta(yes["m"], yes["s"], "medium-getSet-present", "small-getSet-present"))
        pd.DataFrame.from_dict(t).to_csv(
            Constants.BASE_PATH + "stats/rq2_between_groups_get_set_present_" + grp + ".csv")
        print("done...")
        



# p = ProportionOfChange()
# p.process("0")
# p.process("183")
# p.process("365")
# p.process("730", apply_change_filter=False, should_filter_get_set=True)
# p.get_set_vs_no_get_set_diff(730)
# p.process("1095")
# p.plot_cdf("183")
# p.plot_cdf("730")
# p.plot_cdf("1095")
# p.plot_cdf("183")
# p.plot_cdf("183")
# p.plot_cdf("365")
# p.process("730")
# p.process("1460")
# p.plot_cdf(730, apply_change_filter=False)

# p.plot_cdf(183, apply_change_filter=False)

# p.version_with_label(1460)
# p.process("1460", apply_change_filter=False)
# p.plot_cdf(1460, apply_change_filter=False)
