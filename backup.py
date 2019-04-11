#!/usr/bin/env python3
# (C) 2019 a.fadeev

"""
Backup script

Creates a backup of the selected directory and stores it
as a zip archive with normal compression

Usage: python3 backup.py <source_folder> [destination_folder]
       source_folder      - what to compress (recursively)
       destination_folder - where to put the compressed backup
"""

import sys
import os
import zipfile
import concurrent.futures
import time


class Archiver:
    """
    Class for adding a file to the backup
    """
    def __init__(self, n=0):
        self.inactiveState = False
        self.n = n

    # Running function, add a file to the backup
    def run(self, fName, archName):
        try:
            archName.write(fName)
        except Exception as e:
            sys.exit("\033[0m" + "Failed to add {}, {}".format(fName, e) + "\033[0;31m")


class ProgressBar:
    """
    Class for a task that implements a status indicator - Spinner
    """
    def __init__(self):
        self.inactiveState = False
        self.clckIndex = 0
        self.clck = ["", " |", " |", " /", " /", " -", " -", " \\", " \\"]

    def nextClck(self):
        # Returns the next state of the spinner, in a loop
        self.clckIndex += 1
        if self.clckIndex > 8:
            self.clckIndex = 0
        return self.clck[self.clckIndex]

    # Running function
    def run(self, fSize):
        # Rotate spinner until the other task is working
        while not self.inactiveState:
            print("{}\r".format(self.nextClck()), end='')
            time.sleep(0.04)
        print("Done:")
        return


if __name__ == '__main__':

    # CLI argument checks
    USAGE = "Usage: python3 backup.py <source_folder> [destination_folder]\n" + \
            "       source_folder      - what to compress (recursively)\n" + \
            "       destination_folder - where to put the compressed backup\n"

    cwd = os.getcwd()
    args = sys.argv

    if len(args) < 2 or len(args) > 3:
        sys.exit(USAGE)

    if len(sys.argv) == 2:
        if not os.path.isdir(os.path.join(cwd, sys.argv[1])):
            sys.exit("Incorrect source_folder\n\n" + USAGE)
        else:
            dst_dir = ""

    else:
        if not os.path.isdir(os.path.join(cwd, sys.argv[2])):
            sys.exit("Incorrect destination_folder\n\n" + USAGE)
        if not os.path.isdir(os.path.join(cwd, sys.argv[1])):
            sys.exit("Incorrect source_folder\n\n" + USAGE)

        dst_dir = args[2]

    src_file = args[1]
    dst_file = zipfile.ZipFile(os.path.join(dst_dir, src_file.split(".")[0]) + ".zip", mode="w")

    # Traverse all files and folders for given source folder
    for (dir_root, dirs, files) in os.walk(src_file):

        # Keep empty directories within the archive structure
        if not files:
            dir_r = dir_root.split("/")
            files = [dir_r.pop()]
            dir_root = "/".join(dir_r)

        # Process all files within the current folder
        for f in files:

            # Delay for correct spinner appearance
            time.sleep(0.2)
            size = os.path.getsize(os.path.join(dir_root, f))
            print("       Adding {} to backup archive {}\r".format(os.path.join(dir_root, f), dst_file.filename), end='')

            # Create two tasks to run in parallel (main - Archiver, indication - ProgressBar)
            t1 = Archiver()
            t2 = ProgressBar()
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            task1_result = executor.submit(t1.run, os.path.join(dir_root, f), dst_file)
            task2_result = executor.submit(t2.run, size)

            # Start both processes, wait until Archiver task is finished
            concurrent.futures.wait([task1_result, task2_result], return_when="FIRST_COMPLETED")

            # Finish the ProgressBar task
            t2.inactiveState = True

    dst_file.close()
