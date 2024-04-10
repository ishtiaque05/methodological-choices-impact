import json
import tarfile
from abc import ABC, abstractmethod
from pathlib import Path

from constants import Constants
from FileUtil import FileUtil
from DupsTracker import DupsTracker
import gc
import signal
from os import path


def handler(signum, frame):
    print("Forever is over!")
    raise Exception("end of time")

class AbstractReader(ABC):
    def __init__(self):
        self.file_path = Constants.CODESHOVEL_HIST_PATH
        self.repo = None
        self.parsing_problems = 0
        self.filename = None
        self.dups_tracker = None
        self.is_test_method = None
        if path.exists(Constants.ALL_SINGLE_FILES_OF_REPO + "tracker.json"):
            self.all_processed_methods = FileUtil.load_json(Constants.ALL_SINGLE_FILES_OF_REPO + "tracker.json")
        else:
            self.all_processed_methods = []
        super().__init__()

    def read_all_files_in_tar_dir(self):
        signal.signal(signal.SIGTERM, handler)
        for tar_file in Path(self.file_path).rglob('*'):
            t = tarfile.open(tar_file, mode="r:*")
            count = 0
            self.repo = t.name.split("/")[-1].replace(".tar.gz", "")

            self.dups_tracker = DupsTracker()
            print("Reading tar file {0}...".format(tar_file.name))

            for mem in t.getmembers():
                try:
                    if not mem.name == self.repo:
                        fileId = mem.name.split('/')[-1]
                        tmpfile = self.repo + "-" + fileId

                        f = t.extractfile(mem)
                        method_hist = json.loads(f.read())

                        self.filename = method_hist["repositoryName"] + "-" + fileId
                        fileId = int(fileId.replace(".json", ""))
                        self.is_test_method = Util.is_test_method(method_hist)
                        # signal.alarm(5)
                        self.process(method_hist)
                        count = count + 1
                        f.close()
                        del f, method_hist
                        gc.collect()
                except Exception as e:
                    self.parsing_problems = self.parsing_problems + 1
                    print(e)
            t.close()
            del t
            gc.collect()
            self.save_repo_data()

            print("Total file read....{0}".format(count))
            print("Done processing tar....")
            print("Saving output for {0}".format(tar_file.name))
            self.dups_tracker.reset_tracker()
        print("%%%%%%%%%%% Done processing %%%%%%%%%%")
        self.save_json()

    @abstractmethod
    def process(self, method_hist):
        pass

    @abstractmethod
    def save_json(self):
        pass

    @abstractmethod
    def save_repo_data(self):
        pass

