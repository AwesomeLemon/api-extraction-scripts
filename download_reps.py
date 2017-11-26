import os
from langdetect import detect
from peewee import *
import logging

from playhouse.apsw_ext import APSWDatabase
from playhouse.sqlite_ext import SqliteExtDatabase
import shutil

import git
import time
logging.basicConfig(level=logging.DEBUG)

db_path = '/media/jet/HDD/DeepApiJava.sqlite'  # /media/jet/HDD/hubic/DeepApi# (4)'#'D:\DeepApiReps\DeepApi#'
# database = SqliteExtDatabase(db_path, autocommit=False,# timeout=30000)
#                            pragmas=(('journal_mode', 'DELETE'), ('busy_timeout', 60000)))
database = APSWDatabase(db_path, timeout=600000)
                           # pragmas=(('journal_mode', 'DELETE'), ('busy_timeout', 60000)))

class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class Repo(BaseModel):
    forks = IntegerField(db_column='Forks', null=True)
    id = PrimaryKeyField(db_column='Id')
    processed_time = BigIntegerField(db_column='ProcessedTime', null=True)
    stars = IntegerField(db_column='Stars', null=True)
    url = CharField(db_column='Url', null=True)  # varchar
    watchers = IntegerField(db_column='Watchers', null=True)

    class Meta:
        db_table = 'Repo'


class Solution(BaseModel):
    id = PrimaryKeyField(db_column='Id')
    path = CharField(db_column='Path', null=True)  # varchar
    processed_time = BigIntegerField(db_column='ProcessedTime', null=True)
    repo_id = ForeignKeyField(Repo, db_column='RepoId', index=True, null=True)
    was_compiled = IntegerField(db_column='WasCompiled', null=True)

    class Meta:
        db_table = 'Solution'


class Method(BaseModel):
    id = PrimaryKeyField(db_column='Id')
    name = CharField(db_column='Name', null=True)  # varchar
    comment = CharField(db_column='Comment', null=True)  # varchar
    calls = CharField(db_column='Calls', null=True)  # varchar
    solution_id = ForeignKeyField(Solution, db_column='SolutionId', index=True, null=True)

    class Meta:
        db_table = 'Method'


class SqliteSequence(BaseModel):
    name = UnknownField(null=True)  #
    seq = UnknownField(null=True)  #

    class Meta:
        db_table = 'sqlite_sequence'
        primary_key = False


def download_reps(path_for_clone='/media/jet/HDD/DeepApiJava/'):
    def extract_name_and_owner_from_url(url):
        lastSlash = url.rfind('/')
        secondToLastSlash = url.rfind('/', 0, lastSlash - 1)
        ownerNameAndDotGit = url[secondToLastSlash + 1:]
        return ownerNameAndDotGit[:len(ownerNameAndDotGit) - 4]

    # database.connect()
    # database.pragma('busy_timeout', 60000)
    repos = Repo.select(Repo.id, Repo.url).where(Repo.processed_time.is_null(True))
    for repo in repos:
        print(repo.url)
        cur_url = repo.url
        owner_and_name = extract_name_and_owner_from_url(cur_url)
        rep_path = path_for_clone + owner_and_name
        if os.path.isdir(rep_path):
            shutil.rmtree(rep_path, ignore_errors=True)
        git.Repo().clone_from(cur_url, rep_path, depth=1)
        Solution(path=rep_path, repo_id=repo.id).save()
        repo.processed_time = int(time.time())
        repo.save()
        # database.commit()

    # database.close()


def store_method_langs():
    database.connect()
    with database.atomic():
        # methods = Method.select().where(Method.first_summary_sentence.is_null(False)).limit(10000).execute()
        methods = Method.select().where(Method.first_summary_sentence.is_null(False)).execute()
        for method in methods:
            try:
                method.lang = detect(str(method.first_summary_sentence))
                method.save()
            except:
                pass

    # with database.atomic():
    #     methods = Method.select().where(Method.first_summary_sentence.is_null(True)).limit(10000).execute()
    #     for method in methods:
    #         try:
    #             method.lang = detect(str(method.full_comment))
    #             method.save()
    #         except:
    #             pass
    # Method.update(lang=langid.classify(str(Method.full_comment).strip())[0]).where(Method.comment_is_xml is False).execute()
    database.close()


if __name__ == "__main__":
    download_reps()
