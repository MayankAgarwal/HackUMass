''' MongoDB interface '''

import json
import os
from pymongo import MongoClient


def log_message(message, severity="INFO"):
    ''' Logs error message '''

    temp = "[" + severity + "] :: [MONGODB] :: " + message
    print temp

class MongoDB(object):
    ''' MongoDB interface '''

    def __init__(self, db_name="HackUMass"):


        self.host = "localhost"
        self.port = 27017
        self.db_name = db_name

        self.database = self.connect_to_db()


    def connect_to_db(self):
        ''' Connects to DB. Returns a connection object '''

        connection = MongoClient(self.host, self.port)
        database = connection[self.db_name]

        return database


    def insert_document_in_collection(self, collection, document, main_key):
        ''' Inserts a document in a collection 

        Args: 
            collection (str) : name of the collection
            document (dict) : Data to be inserted in the document
            main_key (str) : Primary key apart from the default "_id" value.
                             Used to prevent duplicate record entry.
                             Search the db for existing entry. If present, overwrite it.
                             Else, enter a new document
            '''

        if isinstance(main_key, str) and main_key not in document:
            raise StandardError(main_key + ' not present in passed document')

        if isinstance(main_key, list):
           if not filter(lambda x: x in document, main_key):
             raise StandardError('All composite keys should be present in the')

        if isinstance(main_key, list):
            filter_val = {}
            for key in main_key:
                filter_val[key] = document[key]

        elif isinstance(main_key, str):
            filter_val={
                main_key: document[main_key]
            }

        db_collection = self.database[collection]
        db_collection.replace_one(filter_val, document, upsert=True)



    def findRecordsForDicts(self, collection, dictList, one_record=False):
        ''' Finds records in a collection
        Args:
            1. collection (str) : collection name
            2. query (dict) : query parameters
            3. one_record (bool) (optional) : Whether to return one record or many
        '''

        db_collection = self.database[collection]

        return db_collection.find( { '$or': dictList } )


    def find(self, collection, query, one_record=False, projection=None, limit=0):
        ''' Finds records in a collection
        Args:
            1. collection (str) : collection name
            2. query (dict) : query parameters
            3. one_record (bool) (optional) : Whether to return one record or many
        '''

        db_collection = self.database[collection]

        if one_record:
            return db_collection.find_one(filter=query, projection=projection, limit=limit)
        else:
            return db_collection.find(filter=query, projection=projection, limit=limit)


    @classmethod
    def sort_find_results(cls, cursor, sort_key):
        ''' Sorts results on sort_keys '''

        return cursor.sort(sort_key)


    def aggregate(self, collection, pipeline, allow_disk_usage=False):
        ''' Performs aggregate operation on collection '''

        db_collection = self.database[collection]

        return db_collection.aggregate(pipeline=pipeline, allowDiskUse=allow_disk_usage)

    def update_collection(self, collection, spec, pipeline, upsert=True, update_one=False):
        '''
        Updates an existing item in collection
        :param collection:
        :param pipeline:
        :return:
        '''

        db_collection = self.database[collection]

        if update_one:
            db_collection.update_one(spec, pipeline, upsert)
        else:
            db_collection.update_many(spec, pipeline, upsert)


    def delete_entry(self, collection, filter, one_record=False):
        '''
        Deletes record from 'collection' based on 'filter'
        :param collection:
        :param query:
        :param one_record:
        :return:
        '''

        db_collection = self.database[collection]

        if one_record:
            db_collection.delete_one(filter)
        else:
            db_collection.delete_many(filter)


    def drop_collection(self, collection):
        ''' Drops a collection from database '''

        self.database.drop_collection(collection)


    def drop_database(self):
        ''' Drops a database '''

        connection = MongoClient(self.host, self.port)
        connection.drop_database(self.db_name)