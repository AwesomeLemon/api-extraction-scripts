import langid as langid
from peewee import *

database = SqliteDatabase('D:\DeepApiReps\DeepApi#', **{})


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


def store_method_langs():
    database.connect()
    Method.update(lang = langid.classify(str(Method.first_summary_sentence))[0]).where(Method.first_summary_sentence is not None).execute()
    Method.update(lang=langid.classify(str(Method.full_comment).strip())[0]).where(Method.comment_is_xml is False).execute()
    database.close()


store_method_langs()
# database.connect()
# x = Method.select().where(Method.first_summary_sentence is not None and Method.solution_id == 2).get()
# database.close()
