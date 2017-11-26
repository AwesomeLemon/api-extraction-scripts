from langdetect import detect
from peewee import *

import method_name_dataset

db_path = '/media/jet/HDD/hubic/DeepApi# (4)'#'D:\DeepApiReps\DeepApi#'
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
    api_calls = CharField(db_column='ApiCalls', null=True)  # varchar
    comment_is_xml = BooleanField(db_column='CommentIsXml', null=True)
    first_summary_sentence = CharField(db_column='FirstSummarySentence', null=True)  # varchar
    full_comment = CharField(db_column='FullComment', null=True)  # varchar
    id = PrimaryKeyField(db_column='Id')
    name = CharField(db_column='Name', null=True)  # varchar
    sampled_at = BigIntegerField(db_column='SampledAt', null=True)
    solution_id = ForeignKeyField(Solution, db_column='SolutionId', index=True, null=True)
    lang = CharField(db_column='Lang', null=True)
    name_tokenized = CharField(db_column='NameTokenized', null=True)

    class Meta:
        db_table = 'Method'


class Methodparameter(BaseModel):
    id = PrimaryKeyField(db_column='Id')
    method_id = ForeignKeyField(Method, db_column='MethodId', index=True, null=True)
    name = CharField(db_column='Name', null=True)  # varchar
    type = CharField(db_column='Type', null=True)  # varchar

    class Meta:
        db_table = 'MethodParameter'


class SqliteSequence(BaseModel):
    name = UnknownField(null=True)  #
    seq = UnknownField(null=True)  #

    class Meta:
        db_table = 'sqlite_sequence'
        primary_key = False


def parse_database_to_eng_and_api():
    database.connect()
    bad_langs = {'zh-cn', 'ja', 'ru', 'pl', 'de'}
    methods = Method.select(Method.first_summary_sentence, Method.api_calls, Method.lang)
        # .where((Method.first_summary_sentence.is_null(False))  &
        # (Method.lang != 'zh-cn') & (Method.lang != 'ja')
        # & (Method.lang != 'ru') & (Method.lang != 'pl') & (Method.lang != 'de'))#.limit(1000)
    eng_api = [(method.first_summary_sentence, method.api_calls) for method in methods
               if method.first_summary_sentence is not None and method.lang not in bad_langs]
    # eng_api_with_empties = [(method.first_summary_sentence, method.api_calls) for method in methods]
    database.close()
    print('Extracted from database: '+ str(len(eng_api)))
    return eng_api

def parse_database_to_names_and_api():
    database.connect()
    bad_langs = {'zh-cn', 'ja', 'ru', 'pl', 'de'}
    methods = Method.select(Method.name_tokenized, Method.api_calls, Method.lang)
    eng_api = [(method.name_tokenized, method.api_calls) for method in methods
               if method.name_tokenized is not None and method.lang not in bad_langs]
    database.close()
    print('Extracted names from database: '+ str(len(eng_api)))
    return eng_api

def store_repos(repo_urls):
    database.connect()
    for repo_url in repo_urls:
        RepoFromFiles.create(url=repo_url)
    database.close()

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

def store_tokenized_names():
    database.connect()
    for i in range(1100):
        with database.atomic():
            methods = Method.select().where(Method.name_tokenized.is_null(True)).limit(10000).execute()
            for method in methods:
                try:
                    tokens = method_name_dataset.name_to_tokens(method.name)
                    if tokens is None:
                        continue
                    method.name_tokenized = ' '.join(tokens)
                    method.save()
                except:
                    pass
    database.close()

if __name__ == "__main__":
    store_tokenized_names()
    # parse_database_to_eng_and_api()
    # store_method_langs()
    # database.connect()
    # x = Method.select().where(Method.first_summary_sentence is not None and Method.solution_id == 2).get()
    # database.close()
