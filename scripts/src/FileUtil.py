import json

import pandas as pd
import os
from pathlib import Path


class FileUtil:
    CODESHOVEL_CLEAN_HIST_PATH = "../data/cleanHistory/"
    CODESHOVEL_HIST_PATH = "../data/Metrics"
   
    STATS_FILE = "../data/stats.txt"

    @staticmethod
    def save_json(save_path, data):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump(data, f)
            f.close()

    @staticmethod
    def load_csv(filename):
        return pd.read_csv(filename, sep='\t')

    @staticmethod
    def load_json(filename):
        with open(filename) as f:
            return json.load(f)


    @staticmethod
    def write_stats(value):
        stats_file = open(FileUtil.STATS_FILE, "a")
        stats_file.write(value)
        stats_file.close()

    @staticmethod
    def write_to_file(filename, value):
        f = open(filename, 'a')
        f.write(value)
        f.close()
