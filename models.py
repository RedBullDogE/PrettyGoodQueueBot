from peewee import *

from config import storage_name

db = SqliteDatabase(storage_name)


class BaseModel(Model):
    class Meta:
        database = db


class Chat(BaseModel):
    id = PrimaryKeyField(null=False)
    chat_id = IntegerField(unique=True, null=False)
    language = CharField(max_length=20)


class Queue(BaseModel):
    id = PrimaryKeyField(null=False)
    text_representation = CharField(null=False)
    chat_id = ForeignKeyField(Chat, to_field="chat_id")
    name = CharField(null=False)
