from datetime import datetime
import pypyodbc
import pyratemp
import pprint
import random, config, string
import DVConnection
import os
import sys
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
from azure.cosmosdb.table.tablebatch import TableBatch

my_account_name = "oscarapps"
my_account_key = "FY5CZqjU34AP33ITHTeIQbGj99e1MqZtNBJ2EHoScHljwwo2eBFqk6l4yMpY3X8MoqGsjq/febzhVXkkPsTNxw=="

def _RunQuery(query):
    """Arbitrary code execution, hooray"""
    # _connection = pypyodbc.connect(r"Driver={SQL Server};Server=YWSQLRTMA01v\RTMA;Database=CodeGeneration;Trusted_Connection=yes;")
    #_connection = pypyodbc.connect(r"Driver={SQL Server};Server=ERG-ASUS;Database=WideWorldImporters;Trusted_Connection=yes;")
    _connection = pypyodbc.connect(DVConnection.GetCodeGenerationConnectionString())
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

def WriteCustomerCategories():
    print("Writing Customer Categories...")
    sql = """SELECT [CC].[CustomerCategoryID]
              ,[CC].[CustomerCategoryName]
        FROM [Sales].[CustomerCategories] AS [CC]
        ORDER BY 2;"""
    results = _RunQuery(sql)
    if (results):
        try:
            print(f"Results returned: {len(results)}")
            table_service = TableService(account_name=my_account_name, account_key=my_account_key)
            records = 0
            batch = TableBatch()
            inBatch = 0
            table_service.create_table("wwiCustomerCategory")
            for cat in results:
                categoryEntity = Entity()
                categoryEntity.PartitionKey = "WWI"
                categoryEntity.RowKey = str(cat["customercategoryid"])
                categoryEntity.CustomerCategoryID = cat["customercategoryid"]
                categoryEntity.CustomerCategoryName = cat["customercategoryname"]
                inBatch += 1
                batch.insert_or_replace_entity(categoryEntity)
                if inBatch > 99:
                    table_service.commit_batch("wwiCustomerCategory", batch)
                    records += inBatch
                    inBatch = 0
                    batch = TableBatch()
            if inBatch > 0:
                table_service.commit_batch("wwiCustomerCategory", batch)
                records += inBatch
        except Exception as e:
            print(e)
            raise
        finally:
            table_service = None
    print(f"Writes/Updates done: {records}")

def WriteCustomerRecords():
    print("Writing Customer records...")
    previousPartitionKey = ""
    sql = """SELECT [C].[CustomerID]
      ,[C].[CustomerName]
      ,[C].[BillToCustomerID]
      ,[C].[CustomerCategoryID]
      ,[CC].[CustomerCategoryName]
      ,[C].[BuyingGroupID]
      ,[C].[PrimaryContactPersonID]
      ,[C].[AlternateContactPersonID]
      ,[C].[DeliveryMethodID]
      ,[C].[PostalCityID]
      ,[C].[CreditLimit]
      ,[C].[AccountOpenedDate]
      ,[C].[StandardDiscountPercentage]
      ,[C].[IsStatementSent]
      ,[C].[IsOnCreditHold]
      ,[C].[PaymentDays]
      ,[C].[PhoneNumber]
      ,[C].[FaxNumber]
      ,[C].[DeliveryRun]
      ,[C].[RunPosition]
      ,[C].[WebsiteURL]
      ,[C].[DeliveryAddressLine1]
      ,[C].[DeliveryAddressLine2]
      ,[C2].[CityName]
      ,[C].[DeliveryPostalCode]
      ,[C].[DeliveryLocation]
      ,[C].[PostalAddressLine1]
      ,[C].[PostalAddressLine2]
      ,[C].[PostalPostalCode]
    FROM [Sales].[Customers]                AS [C]
    INNER JOIN [Sales].[CustomerCategories] AS [CC]
        ON [CC].[CustomerCategoryID] = [C].[CustomerCategoryID]
    INNER JOIN [Application].[Cities]       AS [C2]
        ON [C2].[CityID] = [C].[DeliveryCityID];"""
    results = _RunQuery(sql)
    if (results):
        try:
            print(f"Results returned: {len(results)}")
            table_service = TableService(account_name=my_account_name, account_key=my_account_key)
            records = 0
            batch = TableBatch()
            inBatch = 0
            table_service.create_table("wwiCustomer")
            for cat in results:
                categoryEntity = Entity()
                categoryEntity.PartitionKey = str(cat["customercategoryid"])
                categoryEntity.RowKey = str(cat["customerid"])
                categoryEntity.CustomerName = cat["customername"]
                categoryEntity.BillToCustomerID = cat["billtocustomerid"]
                categoryEntity.CustomerCategoryID = cat["customercategoryid"]
                categoryEntity.CategoryName = cat["customercategoryname"]
                categoryEntity.BuyingGroupID = cat["buyinggroupid"]
                categoryEntity.PrimaryContactPersonID = cat["primarycontactpersonid"]
                categoryEntity.DeliveryMethodID = cat["deliverymethodid"]
                categoryEntity.CreditLimit = str(cat["creditlimit"])
                categoryEntity.AccountOpenedDate = cat["accountopeneddate"]
                categoryEntity.StandardDiscountPercentage = str(cat["standarddiscountpercentage"])
                categoryEntity.IsStatementSent = cat["isstatementsent"]
                categoryEntity.IsOnCreditHold = cat["isoncredithold"]
                categoryEntity.PaymentDays = cat["paymentdays"]
                categoryEntity.PhoneNumber = cat["phonenumber"]
                categoryEntity.WebsiteURL = cat["websiteurl"]
                categoryEntity.DeliveryAddressLine1 = cat["deliveryaddressline1"]
                categoryEntity.DeliveryAddressLine2 = cat["deliveryaddressline2"]
                categoryEntity.CityName = cat["cityname"]
                categoryEntity.DeliveryPostalCode = cat["deliverypostalcode"]
                categoryEntity.PostalAddressLine1 = cat["postaladdressline1"]
                categoryEntity.PostalAddressLine2 = cat["postaladdressline2"]
                categoryEntity.PostalPostalCode = cat["postalpostalcode"]
                if categoryEntity.PartitionKey != previousPartitionKey:
                    if inBatch > 0:
                        table_service.commit_batch("wwiCustomer", batch)
                        records += inBatch
                        inBatch = 0
                        batch = TableBatch()
                if inBatch > 99:
                    table_service.commit_batch("wwiCustomer", batch)
                    records += inBatch
                    inBatch = 0
                    batch = TableBatch()
                inBatch += 1
                batch.insert_or_replace_entity(categoryEntity)
            if inBatch > 0:
                table_service.commit_batch("wwiCustomer", batch)
                records += inBatch
        except Exception as e:
            print(e)
            raise
        finally:
            table_service = None
    print(f"Writes/Updates done: {records}")

def WriteOrders():
    print("Writing Order records...")
    previousPartitionKey = ""
    sql = """SELECT CAST([O].[CustomerID] AS VARCHAR(4)) AS [PartitionKey]
            ,CAST([O].[OrderID] AS VARCHAR(10)) AS [RowKey]
            ,[O].[OrderID]
            ,[O].[CustomerID]
            ,[O].[SalespersonPersonID]
            ,[O].[PickedByPersonID]
            ,[O].[ContactPersonID]
            ,[O].[BackorderOrderID]
            ,[O].[OrderDate]
            ,[O].[ExpectedDeliveryDate]
            ,[O].[CustomerPurchaseOrderNumber]
            ,[O].[IsUndersupplyBackordered]
            ,[O].[Comments]
            ,[O].[DeliveryInstructions]
            ,[O].[InternalComments]
            ,[O].[PickingCompletedWhen]
            ,[O].[LastEditedBy]
            ,[O].[LastEditedWhen]
        FROM [Sales].[Orders] AS [O]
        ORDER BY 1"""
    results = _RunQuery(sql)
    if (results):
        try:
            print(f"Results returned: {len(results)}")
            table_service = TableService(account_name=my_account_name, account_key=my_account_key)
            records = 0
            batch = TableBatch()
            inBatch = 0
            table_service.create_table("wwiOrder")
            for cat in results:
                categoryEntity = Entity()
                categoryEntity.PartitionKey = cat["partitionkey"]
                categoryEntity.RowKey = cat["rowkey"]
                categoryEntity.OrderID = cat["orderid"]
                categoryEntity.CustomerID = cat["customerid"]
                categoryEntity.SalespersonPersonID = cat["salespersonpersonid"]
                categoryEntity.PickedByPersonID = cat["pickedbypersonid"]
                categoryEntity.ContactPersonID = cat["contactpersonid"]
                categoryEntity.BackorderOrderID = cat["backorderorderid"]
                categoryEntity.OrderDate = cat["orderdate"]
                categoryEntity.ExpectedDeliveryDate = cat["expecteddeliverydate"]
                categoryEntity.CustomerPurchaseOrderNumber = cat["customerpurchaseordernumber"]
                categoryEntity.IsUndersupplyBackerordered = cat["isundersupplybackordered"]
                categoryEntity.Comments = cat["comments"]
                categoryEntity.DeliveryInstructions = cat["deliveryinstructions"]
                categoryEntity.InternalComments = cat["internalcomments"]
                categoryEntity.PickingCompletedWhen = cat["pickingcompletedwhen"]
                categoryEntity.LastEditedBy = cat["lasteditedby"]
                categoryEntity.LastEditedWhen = cat["lasteditedwhen"]
                if categoryEntity.PartitionKey != previousPartitionKey:
                    if inBatch > 0:
                        table_service.commit_batch("wwiOrder", batch)
                        records += inBatch
                        inBatch = 0
                        batch = TableBatch()
                if inBatch > 99:
                    table_service.commit_batch("wwiOrder", batch)
                    records += inBatch
                    inBatch = 0
                    batch = TableBatch()
                inBatch += 1
                batch.insert_or_replace_entity(categoryEntity)
            if inBatch > 0:
                table_service.commit_batch("wwiOrder", batch)
                records += inBatch
        except Exception as e:
            print(e)
            raise
        finally:
            table_service = None
    print(f"Writes/Updates done: {records}")

def WriteOrderLines():
    print("Writing Order Line records...")
    previousPartitionKey = ""
    sql = """SELECT CAST([OL].[OrderID] AS VARCHAR(10)) AS [PartitionKey]
            ,CAST([OL].[OrderLineID] AS VARCHAR(10)) AS [RowKey]
            ,[OL].[OrderLineID]
            ,[OL].[OrderID]
            ,[OL].[StockItemID]
            ,[OL].[Description]
            ,[OL].[PackageTypeID]
            ,[OL].[Quantity]
            ,[OL].[UnitPrice]
            ,[OL].[TaxRate]
            ,[OL].[PickedQuantity]
            ,[OL].[PickingCompletedWhen]
            ,[OL].[LastEditedBy]
            ,[OL].[LastEditedWhen]
        FROM [Sales].[OrderLines] AS [OL];"""
    results = _RunQuery(sql)
    if (results):
        try:
            print(f"Results returned: {len(results)}")
            table_service = TableService(account_name=my_account_name, account_key=my_account_key)
            records = 0
            batch = TableBatch()
            inBatch = 0
            table_service.create_table("wwiOrderLine")
            for cat in results:
                categoryEntity = Entity()
                categoryEntity.PartitionKey = cat["partitionkey"]
                categoryEntity.RowKey = cat["rowkey"]
                categoryEntity.OrderLineID = cat["orderlineid"]
                categoryEntity.OrderID = cat["orderid"]
                categoryEntity.StockItemID = cat["stockitemid"]
                categoryEntity.Description = cat["description"]
                categoryEntity.PackageTypeID = cat["packagetypeid"]
                categoryEntity.Quantity = cat["quantity"]
                categoryEntity.UnitPrice = str(cat["unitprice"])
                categoryEntity.TaxRate = str(cat["taxrate"])
                categoryEntity.PickedQuantity = cat["pickedquantity"]
                categoryEntity.PickingCompletedWhen = cat["pickingcompletedwhen"]
                categoryEntity.LastEditedBy = cat["lasteditedby"]
                categoryEntity.LastEditedWhen = cat["lasteditedwhen"]
                if categoryEntity.PartitionKey != previousPartitionKey:
                    if inBatch > 0:
                        table_service.commit_batch("wwiOrderLine", batch)
                        records += inBatch
                        inBatch = 0
                        batch = TableBatch()
                        if (records % 1000 == 0):
                            print("Writes/Updates done: {}".format(records))
                if inBatch > 99:
                    table_service.commit_batch("wwiOrderLine", batch)
                    records += inBatch
                    inBatch = 0
                    batch = TableBatch()
                    if (records % 1000 == 0):
                        print("Writes/Updates done: {}".format(records))
                inBatch += 1
                batch.insert_or_replace_entity(categoryEntity)
            if inBatch > 0:
                table_service.commit_batch("wwiOrderLine", batch)
                records += inBatch
        except Exception as e:
            print(e)
            raise
        finally:
            table_service = None
    print(f"Writes/Updates done: {records}")

def Main(_argv):
    print("Starting Load WWI to Azure Tables program...")
    WriteCustomerCategories()
    # WriteCustomerRecords()
    # WriteOrders()
    # WriteOrderLines()

if __name__ == "__main__":
    Main(sys.argv)
