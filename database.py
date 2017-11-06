from langdetect import detect
from peewee import *

db_path = 'D:\DeepApiReps\DeepApi#'
database = SqliteDatabase(db_path, **{})


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
    api_calls = CharField(db_column='ApiCalls', null=True)  # varchar
    comment_is_xml = BooleanField(db_column='CommentIsXml', null=True)
    first_summary_sentence = CharField(db_column='FirstSummarySentence', null=True)  # varchar
    full_comment = CharField(db_column='FullComment', null=True)  # varchar
    id = PrimaryKeyField(db_column='Id')
    name = CharField(db_column='Name', null=True)  # varchar
    sampled_at = BigIntegerField(db_column='SampledAt', null=True)
    solution_id = ForeignKeyField(Solution, db_column='SolutionId', index=True, null=True)
    lang = CharField(db_column='lang', null=True)

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
    methods = Method.select(Method.first_summary_sentence, Method.api_calls).where(
        (Method.first_summary_sentence.is_null(False)) & (Method.lang == 'en')).limit(1000)
    eng_api_with_empties = [(method.first_summary_sentence, method.api_calls) for method in methods]
    # eng_api_with_empties = [(method.first_summary_sentence, method.api_calls) for method in methods]
    designer_comment_start = 'Required method for Designer'
    eng_api = [(eng.split(' '), api.split(' ')) for (eng, api) in eng_api_with_empties if
               not (len(eng) == 0 or len(api) == 0 or eng.startswith(designer_comment_start))]
    database.close()
    return eng_api


def store_method_langs():
    database.connect()
    with database.atomic():
        methods = Method.select().where(Method.first_summary_sentence.is_null(False)).limit(10000).execute()
        # methods = Method.select().where((Method.id == 171608) | (Method.id == 171609)).execute()
        for method in methods:
            # method.lang = langid.classify(str(method.first_summary_sentence))[0]
            method.lang = detect(str(method.first_summary_sentence))
            method.save()
    # Method.update(lang=str(Method.id)).where((Method.id == 171608) | (Method.id == 171609)).execute()
    # method = Method.select().where(Method.id == 171608).get()
    # Method.update(lang=Method.first_summary_sentence).where(Method.id == 171608).execute()
    #171608
    # Method.update(lang=langid.classify(str(Method.full_comment).strip())[0]).where(Method.comment_is_xml is False).execute()
    database.close()

if __name__ == "__main__":
    parse_database_to_eng_and_api()
    # store_method_langs()
    # database.connect()
    # x = Method.select().where(Method.first_summary_sentence is not None and Method.solution_id == 2).get()
    # database.close()
