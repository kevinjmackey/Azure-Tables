import datetime
import logging as log
import os
import sys
import pprint
import pypyodbc
import pyratemp
import random, config, string
import azure.cosmosdb.table
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
from azure.cosmosdb.table.tablebatch import TableBatch

my_account_name = "dvcodegeneration"
my_account_key = "7fl0rjn5ajtEBMg30n3jAnzdhMKFuE0MMqqae7Pv5AJAl47XYjNxZ8Ig8gvgvdKOUAGF7oGLz+TUXMcM0fLeVg=="

class M204Legacy:
    version = ""
    filesource = ""
    schema = ""
    recordtype = ""
    itemname = ""
    atttributename = ""
    datatype = ""
    length = ""
    precision = None
    scale = None
    isBase64 = 0

def GenerateOscarFile(_items, _recType):
    print ("Generating the Oscar file")
    fieldsToSkip = ['Create_TS','Modify_ID','Modify_TS','OCCNO','RowID','PartitionKey', 'SOURCEDELETED', 'DTS_DTTMSP','HASH', 'Distributed_KEY', 'Modification_Count', 'HistoryAsOfDate','PurgeAfterDate']
    fileSource = ""
    baseTable = ""
    reoccurTable = ""
    baseColumns = []
    reoccurColumns = []
    for item in _items:
        fileSource = item.filesource
        if item.atttributename.endswith("RECORD_KEY") or item.atttributename in fieldsToSkip:
            pass
        else:
            if item.itemname.endswith("_REOCCUR"):
                reoccurTable = item.itemname
                reoccurColumns.append(item)
            else:
                baseTable = item.itemname
                baseColumns.append(item)
        #print(item.schema, item.itemname, item.atttributename, item.datatype, item.length, item.isBase64)
    d = {}
    d["M204File"] = fileSource
    d["schema"] = "Legacy"
    d["baseTable"] = baseTable
    d["reoccurTable"] = reoccurTable
    d["version"] = baseColumns[0].version
    d["baseColumns"] = baseColumns
    d["reoccurColumns"] = reoccurColumns
    d["hasRectype"] = "N" if _recType == "No Rectype" else "Y"
    d["rectype"] = _recType
    d["hasReoccur"] = "Y" if len(reoccurColumns) > 0 else "N"
    t = pyratemp.Template(filename="Legacy.tmpl")
    with open("Legacy.dvo", "a") as fout:
        fout.write(t(**d))

def WriteFilePrefix(_dataStore, _version):
    version = "{ " + f'"Version" : "{str(_version)}"' + " }"
    prefix = f"""BEGIN
    datastore {_dataStore} {version}
    """
    with open("Legacy.dvo", "w") as fout:
        fout.write(prefix)

def WriteFileSuffix():
    suffix = """
    end_datastore
END"""
    with open("Legacy.dvo", "a") as fout:
        fout.write(suffix)

def ParseDataType(_item, _dataType):
    newItem = _item
    if _dataType.startswith("VARCHAR"):
        newItem.datatype = "String"
        newItem.length = "-1" if _dataType.endswith("MAX)") else "255"
    elif _dataType.endswith("INT"):
        newItem.datatype = "Integer"
    elif _dataType.startswith("DATETIME"):
        newItem.datatype = "Datetime"
        newItem.precision = "7"
    elif _dataType.startswith("NUMERIC"):
        newItem.datatype = "NUMERIC"
        newItem.precision = "30"
        newItem.scale = "0"
    elif _dataType.startswith("Datetime"):
        newItem.datetype = "Datetime"
        newItem.precision = "7"
    return newItem

def RetrieveStageEntities(_version, _entity):
    print("Getting Entities for {}".format(_entity))
    items = []
    try:
        queryFilter = """(PartitionKey eq 'YRC-M204') and (RowKey ge '{0}-{1}') and (RowKey lt '{0}-{1}.')""".format(_version, _entity)
        print(queryFilter)
        i = 0
        table_service = TableService(account_name=my_account_name, account_key=my_account_key)
        entities = table_service.query_entities("dvStageEntity", filter = queryFilter)
        for entity in entities:
            i += 1
            item = M204Legacy()
            item.filesource = _entity
            item.version = str(entity.RowKey)[0:3]
            item.schema = entity.schemaName
            item.itemname = entity.stageTableName
            item.atttributename = f"{entity.stageColumnName}_R" if entity.stageColumnName == "DATE" or entity.stageColumnName == "TIME" else entity.stageColumnName
            item = ParseDataType(item, entity.stageEasyDataType)
            item.isBase64 = entity.isBase64
            items.append(item)
            #print(entity.RowKey, entity.stageEasyDataType, entity.isBase64)
    except Exception as e:
        print(e)
    finally:
        table_service = None
    return items
    
def GetSources(environment, _account_name, _account_key):
    sources = {}
    if environment is not None:
        try:
            queryFilter = "(PartitionKey eq '{}')".format(environment)
            table_service = TableService(account_name=_account_name,account_key=_account_key)
            entities = table_service.query_entities("dvSource", filter = queryFilter)
            for entity in entities:
                if entity.isActive==1:
                    sources[entity.RowKey] = entity.rectype
        except Exception as e:
            log.error(e)
            sources = {}
        finally:
            table_service = None
    else:
        sources = {}

    return sources
    
def Main(_argv):
    print("Starting Azure Table program")
    m204Files = GetSources("YRC-M204", my_account_name, my_account_key)
    WriteFilePrefix("Legacy", 260)
    for m204File in m204Files.keys():
        items = RetrieveStageEntities(260, m204File)
        GenerateOscarFile(items, m204Files[m204File])
    WriteFileSuffix()

if __name__ == "__main__":
    Main(sys.argv)
