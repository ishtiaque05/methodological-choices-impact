from re import search
import os

import dateparser
import stats.CliffDelta as cld
from scipy import stats

class Util:
    # M/D/Y

    @staticmethod
    def getCommitDate(datetime):
        try:
            return dateparser.parse(datetime, settings={'DATE_ORDER': 'DMY'}).strftime('%d/%m/%Y')
        except Exception as e:
            return dateparser.parse(datetime).date().strftime('%d/%m/%Y')

    @staticmethod
    def getCommitTimeStamp(datetime):
        return dateparser.parse(datetime).timestamp()

    @staticmethod
    def getNumOfDays(date1, date2):
        try:
            days = abs((dateparser.parse(date2, settings={'DATE_ORDER': 'DMY'}) - dateparser.parse(date1, settings={'DATE_ORDER': 'DMY'})).days)
            return days
        except Exception as e:
            days = abs((dateparser.parse(date2) - dateparser.parse(date1)).days)
            return days

        # return abs((dateparser.parse(date2) - dateparser.parse(date1)).days)

    @staticmethod
    def get_changes(change):
        if Util.is_multichange(change):
            ops = change[change.find("(") + 1:change.find(")")]
            return ops.split(',')
        else:
            return change

    @staticmethod
    def is_multichange(type):
        return search('Ymultichange', type)

    @staticmethod
    def is_body_change(type):
        return search('Ybodychange', type)

    @staticmethod
    def getIntroCommit(changeHistoryShort):
        for commit, changeType in changeHistoryShort.items():
            if changeType == 'Yintroduced':
                return commit
        return None

    @staticmethod
    def intro_count(changeHistoryShort):
        count = 0
        for commit, changeType in changeHistoryShort.items():
            if changeType == 'Yintroduced':
                count = count + 1
        return count

    @staticmethod
    def should_discard_methods(changeHistoryShort):
        hist = list(changeHistoryShort.items())
        hist_len = len(hist)
        intro = hist[hist_len - 1][1]

        if intro != "Yintroduced":
            return True

        count = 0
        for i in range(hist_len - 1, -1, -1):
            changeType = hist[i][1]
            if changeType == "Yintroduced":
                count += 1

        if count > 1:
            return True
        else:
            return False



    @staticmethod
    def get_type_of_changes():
        return {
            "Yfilerename": 0,
            "Ybodychange": 0,
            "Yintroduced": 0,
            "Ymodifierchange": 0,
            "Yexceptionschange": 0,
            "Ymovefromfile": 0,
            "Yrename": 0,
            "Yparameterchange": 0,
            "Yreturntypechange": 0,
            "Yparametermetachange": 0,
            "Yannotationchange": 0,
            "Ydocchange": 0,
            "Yformatchange": 0
        }

    @staticmethod
    def get_name_path_from_hist(hist):
        if search('Ymultichange', hist["type"]):
            subchange = hist["subchanges"][0]
            return subchange["functionName"], subchange["path"], subchange["functionStartLine"]
        else:
            return hist["functionName"], hist["path"], hist["functionStartLine"]

    @staticmethod
    def get_intro_date_and_commit(method_hist):
        for k, v in method_hist["changeHistoryDetails"].items():
            if v["type"] == "Yintroduced":
                return v["commitDate"], k
        return None, None

    @staticmethod
    def get_method_unique_name(commit_details):
        name, path, startline = Util.get_name_path_from_hist(commit_details)
        return path + "-" + name + "-" + str(startline)

    @staticmethod
    def is_meaningful_change(change):
        if isinstance(change, list) and "Ybodychange" in change:
            return True
        elif change == "Ybodychange":
            return True
        else:
            return False

    @staticmethod
    def is_mechanical_change(change):
        if isinstance(change, list) and "Ybodychange" not in change:
            return True
        elif change != "Ybodychange" and change != "Yintroduced":
            return True
        else:
            return False

    @staticmethod
    def get_number_of_ybodychange(changeHistoryShort):
        Ybodychange = 0
        for commit, val in changeHistoryShort.items():
            change = Util.get_changes(val)
            if isinstance(change, list):
                if "Ybodychange" in change:
                    Ybodychange = Ybodychange + 1
            elif "Ybodychange" == change:
                Ybodychange = Ybodychange + 1
        return Ybodychange

    @staticmethod
    def get_nth_body_change(hist_tuple_list, n):
        bodychange = 0
        for i in range(len(hist_tuple_list) - 1, -1, -1):
            if Util.is_body_change(hist_tuple_list[i][1]["type"]):
                bodychange = bodychange + 1
                if n == bodychange:
                    return 1, hist_tuple_list[i][1]["commitDate"]

        return 0, hist_tuple_list[-1][1]["commitDate"]


    @staticmethod
    def join_str(commit, repo, filepath):
        head, tail = os.path.split(filepath)
        return repo + "-" + commit + "-" + head

    @staticmethod
    def get_index_nth_change(changeHistoryDetailsTuplelst, ith_change):
        return len(changeHistoryDetailsTuplelst) - (len(changeHistoryDetailsTuplelst) + ith_change)
    @staticmethod
    def total_loop(metrics):
        return metrics["forStmts"] + metrics["forEach"] + metrics["WhileStmts"] + metrics["DoStmts"]

    @staticmethod
    def count_all_changes(changeHistoryShort):
        fileops = 0
        minor_changes = 0
        major_changes = 0
        for commit, changeType in changeHistoryShort.items():
            changes = Util.get_changes(changeType)
            if isinstance(changes, list) and not Util.contain_file_ops(changes):
                fileops = fileops + 1
            elif not Util.is_file_ops(changes):
                fileops = fileops + 1

            if Util.is_essential_change(changes):
                major_changes = major_changes + 1
            else:
                minor_changes = minor_changes + 1

        return fileops, major_changes, minor_changes

    @staticmethod
    def contain_file_ops(changes):
        if len(changes) == 2 and "Yfilerename" in changes and "Ymovefromfile" in changes:
            return True
        else:
            return False

    @staticmethod
    def is_file_ops(change):
        if "Yfilerename" in change or "Ymovefromfile" in change:
            return True
        else:
            return False

    @staticmethod
    def contains_minor_changes(change):
        if "Yannotationchange" in change or "Ydocchange" in change or "Yformatchange" in change or "Yfilerename" in change or "Ymovefromfile" in change:
            return True
        else:
            return False

    @staticmethod
    def is_essential_change(change):
        if "Ybodychange" in change or "Ymodifierchange" in change or "Yexceptionschange" in change or "Yrename" in change or "Yparameterchange" in change or "Yreturntypechange" in change or "Yparametermetachange" in change:
            return True
        else:
            return False

    @staticmethod
    def is_test_method(hist):
        annotations = hist["functionAnnotation"].split(',')
        paths = hist["sourceFilePath"].split("/")
        if '@Test' in annotations or 'test' in paths or hist["functionName"].startswith("test"):
            return True
        else:
            return False

    @staticmethod
    def significant_test(x, y, category, repo="all"):
        d, size = cld.cliffsDelta(x, y)
        w, p = stats.wilcoxon(x, y, alternative='two-sided')
        label = 'no'
        if round(p, 3) < 0.05:
            label = "yes"

        return {
            "w_statistic": w,
            "p": round(p, 3),
            'significant': label,
            'd': round(d, 4),
            'size': size,
            'repo': repo,
            'category': category
        }

    @staticmethod
    def is_buggy(commitMsg):
        BUGGY_CODE = ["error", "bug", "fixes", "fixing", "fix", "fixed", "mistake", "incorrect", "fault", "defect", "flaw"]
        # commitMessage
        containsBug = set(commitMsg.lower().split()) & set(BUGGY_CODE)
        if containsBug:
            return True
        else:
            return False

    @staticmethod
    def get_src_code(hist):
        if Util.is_multichange(hist["type"]):
            subchange = hist["subchanges"][0]
            return subchange["actualSource"]
        else:
            return hist["actualSource"]