# pip install xlrd
# https://www.geeksforgeeks.org/reading-excel-file-using-python/
import xlrd
import pandas as pd
import pypyodbc
import pprint

from itertools import chain

def PandasShredExcel(file_source):
    pass
    xl = pd.ExcelFile(file_source)
    dfs = {sheet: xl.parse(sheet) for sheet in xl.sheet_names}
    target_sheet_name = 'Data Dictionary Output'
    xl2 = pd.read_excel(file_source )
    r = dfs[target_sheet_name]
    print(type(dfs), type(xl2), type(r))
    
    return dfs[target_sheet_name]


def ShredExcel(file_source):
    # FILE	RECTYPE	FIELD	OCCFLG	SUBSCRIPT	TABLE	COLUMN	SEQ	STYPE	LEN	DEC	NULLIND	M204 IX	KEY COUNT	IX FLAG	KSEQ	IX NAME	IX TYPE	RULE	ISSUE	IsBase64	LegacyEasyDataType
    # file	rectype	field	occflg	subscript	table	column	seq	stype	len	dec	nullind	m204 ix	key count	ix flag	kseq	ix name	ix type	rule	issue	isbase64	legacyeasydatatype

    results = []
    try:
        wb = xlrd.open_workbook(source_file)
        sheet = wb.sheet_by_index(0)
        for index in range(10):
            results.append({'file': sheet.cell_value(index, 0), 
                'rectype': sheet.cell_value(index, 1),
                'field':sheet.cell_value(index, 2),
                'occflg':sheet.cell_value(index, 3),
                'table':sheet.cell_value(index, 5),
                'column':sheet.cell_value(index, 6),
                'seq':sheet.cell_value(index, 7),
                'stype':sheet.cell_value(index, 8),
                'len':sheet.cell_value(index, 9),
                'dec':sheet.cell_value(index, 10),
                'nullind':sheet.cell_value(index, 11),
                # 'm204 ix':sheet.cell_value(index, 12),
                # 'key count':sheet.cell_value(index, 13),
                # 'ix flag':sheet.cell_value(index, 14),
                'kseq':sheet.cell_value(index, 15),
                'ix name':sheet.cell_value(index, 16),
                'ix type':sheet.cell_value(index, 17),
                'rule':sheet.cell_value(index, 18),
                'issue':sheet.cell_value(index, 19),
                'isbase64':sheet.cell_value(index, 20),
                'legacyeasydatatype':sheet.cell_value(index, 21)})

    except Exception as ex:
        pass
        pprint.pprint(ex)


    return results

def GetExcelSourceEntityTable_v1():
    """Project our Excel format into query format"""
    results = []
    for row in excel_results:
        results.append({'partitionkey':'YRC-M204',
            'isactive':'1', 
            'rowkey':row['file'],
            'rectype':row['rectype']})
    return results

def GetExcelSourceEntityTable_v2():
    """Project our Excel format into query format"""
    results = []
    for row in excel_results:
        yield {'partitionkey':'YRC-M204',
            'isactive':'1', 
            'rowkey':row['file'],
            'rectype':row['rectype']}
    


def _RunQuery(query):
    """Arbitrary code execution, hooray"""
    _connection = pypyodbc.connect(r"Driver={SQL Server};Server=YWSQLRTMA01v\RTMA;Database=CodeGeneration;Trusted_Connection=yes;")
    #_connection = pypyodbc.connect(r"Driver={SQL Server};Server=ERG-ASUS;Database=WideWorldImporters;Trusted_Connection=yes;")
    _cursor = _connection.cursor()
    _query_results = None
    try:
        _cursor.execute(query)
        if (not _cursor):
            return []
        if (_cursor.description):
            _query_results = [dict(zip([_column[0] for _column in _cursor.description], _row)) for _row in _cursor.fetchall()]
    except Exception as ex:
        print ("Failed SQL statement \n" + query)
        pprint.pprint(ex)
        raise #re-raise the exception
    finally:
        _connection.close()
    return _query_results

def WriteSourceEntityTable():
    print("Preparing to write the Source Entity table")
    sql = """SELECT TOP(2) 'YRC-M204'        AS [PartitionKey]
      ,[DD].[FileSource] AS [RowKey]
      ,[R].[RECTYPE]
      ,CAST(1 AS BIT)    AS [isActive]
FROM [Meta].[DataDictionary] AS [DD]
INNER JOIN 
(
   SELECT [DD].[FileSource]
      ,CASE
           WHEN [DDRT].[RecTypeColumnName] IS NULL THEN
               'No Rectype'
           ELSE
               [DDRT].[RecTypeColumnName]
       END               AS [RECTYPE]
   FROM [Meta].[DataDictionary] AS [DD]
   INNER JOIN [Meta].[DataDictionary_Table] AS [DDT] ON [DDT].[TableName] = [DD].[LegacyTableName]
   LEFT OUTER JOIN [Meta].[DataDictionary_RecType] AS [DDRT] ON [DDRT].[DataDictionaryTableId] = [DDT].[Id]
   WHERE [DD].[IsCurrent] = CAST(1 AS BIT)
   GROUP BY CASE
           WHEN [DDRT].[RecTypeColumnName] IS NULL THEN
           'No Rectype'
           ELSE
           [DDRT].[RecTypeColumnName]
           END
           ,[DD].[FileSource]
) AS [R] ON [R].[FileSource] = [DD].[FileSource]
WHERE [DD].[IsCurrent] = CAST(1 AS BIT)
      AND [DD].[IsHistoryTable] = 'N'
GROUP BY [DD].[FileSource]
        ,[R].[RECTYPE]
UNION ALL
SELECT top (1) 'YRC-M204'        AS [PartitionKey]
      ,[DD].[FileSource] AS [RowKey]
      ,CASE
           WHEN [R].[RecordType] IS NULL THEN
               'No Rectype'
           ELSE
               'RECTYPE'
       END               AS [RECTYPE]
      ,CAST(1 AS BIT)    AS [isActive]
FROM [Meta].[DataDictionary] AS [DD]
    LEFT OUTER JOIN
    (
        SELECT *
        FROM [Meta].[DataDictionary] AS [DD2]
        WHERE [DD2].[RecordType] IS NOT NULL
              AND [DD2].[IsHistoryTable] = 'Y'
    )                        AS [R]
    ON [R].[FileSource] = [DD].[FileSource]
WHERE [DD].[IsCurrent] = CAST(1 AS BIT)
      AND [DD].[IsHistoryTable] = 'Y'
GROUP BY
    CASE
        WHEN [R].[RecordType] IS NULL THEN
            'No Rectype'
        ELSE
            'RECTYPE'
    END
   ,[DD].[FileSource]
ORDER BY
    1
   ,2;"""
    results = _RunQuery(sql)

    for row in results:
        pprint.pprint(row)

    #print(type(results))
    #print(type(results[0]))

# Rip the version number out of this file
source_file = r'C:\ssisdata\output\Data Dictionary Output v243.xlsx'
#pprint.pprint(source_file.split())[:-1]

version_number = 0
try:
    version_number = (''.join([(s) for s in source_file if s.isdigit()]))
except:
    pass


if (False):
    r = WriteSourceEntityTable()

    

    excel_results = ShredExcel(source_file)


#for row in excel_results:
#    pprint.pprint(row)

    for row in GetExcelSourceEntityTable_v2():
        pprint.pprint(row)

#rr = GetExcelSourceEntityTable(source_file)
#wb = xlrd.open_workbook(source_file)
#sheet = wb.sheet_by_index(0)


#for index in range(sheet.nrows):
#    print(sheet.cell_value(index, 0))

dd = [{'file':'BSR', 'column':'reckey'}, {'file':'BSR', 'column':'dtsdtmsp'}, {'file':'BSR', 'column':'createts'}, {'file':'WGP', 'column':'reckey'}]

pprint.pprint(dd)

#for value in set(chain.from_iterable(d.values() for d in dd)):
#    print(value)

# pandas.core.frame.DataFrame
ed = PandasShredExcel(source_file)
print(type(ed))

# https://stackoverflow.com/questions/26977076/pandas-unique-values-multiple-columns
# https://stackoverflow.com/questions/35268817/unique-combinations-of-values-in-selected-columns-in-pandas-data-frame-and-count
# https://stackoverflow.com/questions/44906754/unique-values-of-two-columns-for-pandas-dataframe?rq=1
# df1.groupby(['A','B']).size().reset_index().rename(columns={0:'count'})
#pprint.pprint(pd.Series())
zcols = ed.columns.names
z = ed.groupby(ed.columns.names).size().reset_index().rename(columns={0:'count'})
pprint.pprint(z)
print()

