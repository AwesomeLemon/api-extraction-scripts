import sqlite3
import traceback

from langdetect import detect
from peewee import *

import Java.java_dataset_utils as java_dataset_utils

db_path = '/media/jet/HDD/DeepApiJava (1).sqlite'  # '/media/jet/HDD/hubic/DeepApi# (4)'#'D:\DeepApiReps\DeepApi#'
database = SqliteDatabase(db_path, **{})


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class RepoFromFiles(BaseModel):
    url = CharField(db_column='Url', null=True)  # varchar

    class Meta:
        db_table = 'RepoFromFiles'


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
    id = PrimaryKeyField(db_column='id')
    name = CharField(db_column='name', null=True)  # varchar
    comment = CharField(db_column='comment', null=True)  # varchar
    calls = CharField(db_column='calls', null=True)
    solution_id = ForeignKeyField(Solution, db_column='solution_id', index=True, null=True)
    first_sentence = CharField(db_column='first_sentence', null=True)  # varchar
    lang = CharField(db_column='lang', null=True)

    class Meta:
        db_table = 'Method'


class SqliteSequence(BaseModel):
    name = UnknownField(null=True)  #
    seq = UnknownField(null=True)  #

    class Meta:
        db_table = 'sqlite_sequence'
        primary_key = False


def parse_database_to_eng_and_api(filter_langs=True):
    database.connect()
    bad_langs = {'zh-cn', 'ja', 'ru', 'pl', 'de', 'ko'}
    if filter_langs:
        methods = Method.select(Method.first_sentence, Method.calls, Method.lang).where((Method.lang != '-') &
         (Method.lang != 'zh-cn') & (Method.lang != 'ja') & (Method.lang != 'ko') & (Method.lang != 'ru'))

        eng_api = [(method.first_sentence, method.calls) for method in methods
                   if method.first_sentence is not None and method.lang not in bad_langs]
    else:
        methods = Method.select(Method.first_sentence, Method.calls)
        eng_api = [(method.first_sentence, method.calls) for method in methods
                   if method.first_sentence is not None and method.first_sentence != '']
    database.close()
    print('Extracted from database: '+ str(len(eng_api)))
    return eng_api


def parse_database_to_eng_and_api_reps_many_stars(filter_langs=True):
    database.connect()
    bad_langs = {'zh-cn', 'ja', 'ru', 'pl', 'de', 'ko'}
    if filter_langs:
        methods = Method.select(Method.first_sentence, Method.calls, Method.lang)\
            .join(Solution)\
            .join(Repo)\
            .where((Repo.stars > 1) & (Method.lang != '-') & (Method.lang != 'zh-cn') & (Method.lang != 'ja')
                   & (Method.lang != 'ko') & (Method.lang != 'ru'))

        eng_api = [(method.first_sentence, method.calls) for method in methods
                   if method.first_sentence is not None and method.lang not in bad_langs]
    else:
        methods = Method.select(Method.first_sentence, Method.calls, Method.lang)\
            .join(Solution)\
            .join(Repo)\
            .where((Repo.stars > 1) & (Method.lang != '-'))
        eng_api = [(method.first_sentence, method.calls) for method in methods
                   if method.first_sentence is not None]
    database.close()
    print('Extracted from database: '+ str(len(eng_api)))
    return eng_api


def insert_repos(repo_file):
    def get_next_repo_from_file(f):
        cloneUrl = f.readline().strip()
        if cloneUrl == '':
            return None
        full_name = f.readline()
        url = f.readline()
        stars = int(f.readline())
        watchers = int(f.readline())
        forks = int(f.readline())
        return Repo.create(forks=forks, stars=stars, url=cloneUrl, watchers=watchers)

    database.connect()
    i = 0
    with database.atomic():
        with open(repo_file) as f:
            condition = True
            while condition:
                repo = get_next_repo_from_file(f)
                if repo is None:
                    break
                repo.save()
                condition = f.readline() is not None
                print(i)
                i += 1

    database.commit()


def store_first_sentences():
    database.connect()

    transaction_limit = 100000
    methods_count = 21000000
    transcation_count = int(methods_count / transaction_limit) + 1
    for i in range(transcation_count):
        with database.atomic():
            methods = None
            while methods is None:
                try:
                    methods = Method.select().where((Method.first_sentence.is_null(True)) &
                                                    (Method.id > transaction_limit * i)).limit(transaction_limit).execute()
                except sqlite3.OperationalError:
                    print('fail1')
            try:
                for method in methods:
                    print(method.id)
                    try:
                        fst_sentence = java_dataset_utils.extract_cleaned_first_sentence(method.comment)
                        method.first_sentence = fst_sentence
                        method.save()
                    except:
                        traceback.print_exc()
            except sqlite3.OperationalError:
                print('fail2')

        print(i)

def store_first_sentence_langs():
    database.connect()

    transaction_limit = 100000
    methods_count = 11000000
    transcation_count = int(methods_count / transaction_limit) + 1
    for i in range(transcation_count):
        with database.atomic():
            # methods = Method.select().where(Method.first_sentence.is_null(False)& Method.lang.is_null(True)).limit(10000).execute()
            methods = Method.select().where(Method.first_sentence.is_null(False) & Method.lang.is_null(True)).limit(transaction_limit).execute()
            for method in methods:
                try:
                    method.lang = detect(method.first_sentence)
                except:
                    method.lang = '-'
                method.save()
        print(i)


# if __name__ == "__main__":
    # parse_database_to_eng_and_api_reps_many_stars(False)
    # insert_repos('/home/jet/java_reps8_17stars_gt1.txt')
    # insert_repos('/home/jet/java_reps_test.txt')
    # store_first_sentences()
    # store_tokenized_names()
    # parse_database_to_eng_and_api()
    # store_method_langs2()
    # database.connect()
    # x = Method.select().where(Method.first_summary_sentence is not None and Method.solution_id == 2).get()
    # database.close()
