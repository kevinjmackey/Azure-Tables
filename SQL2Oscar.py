from datetime import datetime
import pypyodbc
import pyratemp
import random, config, string
import DVConnection
import os
import sys

class SQLColumn:
    attributename = ""
    datatype = ""
    length = ""
    precision = ""
    scale = ""
    nullable = "NO"
    default = ""
    pk = False

def GetTables(_database):
    print("Getting the set of SQL tables to work with...")
    tables = {}
    SqlString = f"""SELECT t.[name] AS [Table], s.[name] AS [Schema]
        FROM [{_database}].sys.tables AS t
        INNER JOIN [{_database}].sys.[schemas] AS [S] ON [S].[schema_id] = [t].[schema_id]
        WHERE [t].[temporal_type_desc] <> 'HISTORY_TABLE'
        ORDER BY 2,1"""
    cnxn = pypyodbc.connect(DVConnection.GetCodeGenerationConnectionString())
    cursor = cnxn.cursor()
    try:
        cursor.execute(SqlString)
        for row in cursor:
            tables[str(row[0])] = str(row[1])

    except Exception as ex:
        cnxn.close()
        print("Error reading file groups from the database.")
        print ("Failed SQL statement " + SqlString)
        print (datetime.now())
        print(ex)
        raise #re-raise the exception

    return tables

def GetColumns(_table, _database):
    columns = []
    SqlString = f"EXECUTE {_database}.sys.sp_columns '{_table}'"
    cnxn = pypyodbc.connect(DVConnection.GetCodeGenerationConnectionString())
    cursor = cnxn.cursor()
    try:
        cursor.execute(SqlString)
        #print(_table)
        for row in cursor:
            column = SQLColumn()
            column.attributename = str(row[3]).rstrip()
            column.precision = str(row[6]).rstrip()
            column.precision = None if column.precision=="None" or column.precision=="NONE" else column.precision
            column.scale = str(row[8]).rstrip()
            column.scale = None if column.scale=="None" or column.scale=="NONE" else column.scale
            column.length = str(row[7]).rstrip()
            column.nullable = str(row[17]).rstrip()
            column.default = str(row[12]).rstrip().upper()
            column.default = None if column.default=="None" or column.default=="NONE" else column.default
            column.datatype = ParseDataType(str(row[5]).rstrip().upper())
            columns.append(column)
            #print(column.attributename, column.datatype, column.length, column.precision, column.scale, column.default)
    except Exception as ex:
        cnxn.close()
        print("Error reading file groups from the database.")
        print ("Failed SQL statement " + SqlString)
        print (datetime.now())
        print(ex)
        raise #re-raise the exception

    return columns

def ParseDataType(_dataType):
    datatype = _dataType
    # print(_dataType)
    if _dataType.startswith("NVARCHAR"):
        datatype = "String"
    elif _dataType.rstrip().endswith("INT") or _dataType.rstrip().endswith("IDENTITY"):
        datatype = "Integer"
    elif _dataType.startswith("DATETIME"):
        datatype = "Datetime"
    elif _dataType.startswith("NUMERIC"):
        datatype = "NUMERIC"
    elif _dataType.startswith("DECIMAL"):
        datatype = "NUMERIC"
    elif _dataType.startswith("SMALLMONEY"):
        datatype = "Float"
    elif _dataType.startswith("MONEY"):
        datatype = "Float"
    elif _dataType.startswith("NCHAR"):
        datatype = "Character"
    elif _dataType.startswith("CHAR"):
        datatype = "Character"
    elif _dataType.startswith("VARCHAR"):
        datatype = "String"
    elif _dataType == "FLAG":
        datatype = "Boolean"
    elif _dataType == "NAME":
        datatype = "String"
    elif _dataType == "UNIQUEIDENTIFIER":
        datatype = "Guid"
    return datatype

def WriteFilePrefix(_dataStore):
    print ("Generating the Oscar file")
    prefix = f"""BEGIN
    datastore {_dataStore}
    """
    with open(f"{_dataStore}.dvo", "w") as fout:
        fout.write(prefix)

def GenerateOscarFile(_columns, _table, _schema, _database):
    d = {}
    d["columns"] = _columns
    d["schema"] = _schema
    d["table"] = _table
    t = pyratemp.Template(filename="SQL2Oscar.tmpl")
    with open(f"{_database}.dvo", "a") as fout:
        fout.write(t(**d))

def WriteFileSuffix(_dataStore):
    suffix = """
    end_datastore
END"""
    with open(f"{_dataStore}.dvo", "a") as fout:
        fout.write(suffix)

def Main(_argv):
    print("Starting SQL to Oscar program...")
    sqlTables = GetTables("WideWorldImporters")
    print(f"We read {len(sqlTables)} tables")
    WriteFilePrefix("WideWorldImporters")
    for table in sqlTables.keys():
        sqlColumns = GetColumns(table, "WideWorldImporters")
        GenerateOscarFile(sqlColumns, table, sqlTables[table], "WideWorldImporters")
    WriteFileSuffix("WideWorldImporters")

if __name__ == "__main__":
    Main(sys.argv)