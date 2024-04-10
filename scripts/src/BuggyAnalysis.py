import csv

import pandas as pd
from matplotlib import pyplot as plt

from AbstractReader import AbstractReader
from FileUtil import FileUtil
from constants import Constants
import seaborn as sns


class BuggyAnalysis(AbstractReader):
    def __init__(self):
        self.BUGGY_CODE = ["error", "bug", "fix", "mistake", "incorrect", "fault", "defect", "flaw", "type"]
        self.ISSUE = "issue"
        self.result = []
        super(BuggyAnalysis, self).__init__()

    def process(self, method_hist):
        bug_count = 0
        for commit, hist in method_hist["changeHistoryDetails"].items():
            contains_bug = set(hist["commitMessage"].split()) & set(self.BUGGY_CODE)
            if contains_bug:
                bug_count += 1

        self.result.append({
            "bugCount": bug_count,
            "changeCount": len(method_hist["changeHistory"]),
            "repo": self.repo,
            "filename": self.filename
        })


    def save_json(self):
        FileUtil.save_json(Constants.BUGGY_ANALYSIS + 'bug_data.json', self.result)
        print("save json in {0}".format(Constants.BUGGY_ANALYSIS + 'bug_data.json'))

   


b = BuggyAnalysis()
b.read_all_files_in_tar_dir()
