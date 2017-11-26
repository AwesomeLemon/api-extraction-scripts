import os
import logging

import shutil
import sqlite3
import traceback

import git
import time

# logging.basicConfig(level=logging.DEBUG)

db_path = '/media/jet/HDD/DeepApiJava.sqlite'  # /media/jet/HDD/hubic/DeepApi# (4)'#'D:\DeepApiReps\DeepApi#'

def download_reps(path_for_clone='/media/jet/HDD/DeepApiJava/'):
    def extract_name_and_owner_from_url(url):
        lastSlash = url.rfind('/')
        secondToLastSlash = url.rfind('/', 0, lastSlash - 1)
        ownerNameAndDotGit = url[secondToLastSlash + 1:]
        return ownerNameAndDotGit[:len(ownerNameAndDotGit) - 4]

    # database.pragma('busy_timeout', 60000)
    database = sqlite3.connect(db_path, 30000000)

    cursor = database.cursor()
    cursor.execute('''SELECT id, url from Repo where ProcessedTime ISNULL ''')
    repos = cursor.fetchall()
    # repos = Repo.select(Repo.id, Repo.url).where(Repo.processed_time.is_null(True))
    for repo in repos:
        print(repo[1])
        cur_url = repo[1]
        owner_and_name = extract_name_and_owner_from_url(cur_url)
        rep_path = path_for_clone + owner_and_name
        if os.path.isdir(rep_path):
            shutil.rmtree(rep_path, ignore_errors=True)
        try:
            git.Repo().clone_from(cur_url, rep_path, depth=1)
        except (git.exc.GitCommandError, UnicodeDecodeError):
            cursor.execute('''UPDATE Repo set ProcessedTime = 0 where Id = ?''',
                           (repo[0],))
            database.commit()
            continue
        cursor.execute('''insert into main.Solution(path, RepoId) VALUES (?,?)''', (rep_path, repo[0]))
        cursor.execute('''UPDATE Repo set ProcessedTime = ? where Id = ?''',
                       (int(time.time()), repo[0]))
        database.commit()
        # time.sleep(3)

    database.close()


if __name__ == "__main__":
    # download_reps()
    while True:
        try:
            download_reps()
        except:
            traceback.print_exc()
