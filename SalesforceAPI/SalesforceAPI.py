import json

import pandas as pd
import requests


def _authentication():
    params = {
        "grant_type": "password",
        "client_id": "xxx",
        "client_secret": "xxx",
        "username": "xxx",
        "password": "xxx",
    }

    r = requests.post(
        "https://delive-dev-ed.my.salesforce.com/services/oauth2/token", params=params
    )
    if r.status_code == 400:
        return {
            "status_code": r.status_code,
            "reason": r.reason,
            "text": r.text,
            "succes": False,
        }
    else:
        return {
            "access_token": r.json().get("access_token"),
            "instance_url": r.json().get("instance_url"),
            "status_code": r.status_code,
            "reason": r.reason,
            "text": r.text,
            "succes": False,
        }


def _call(parameters={}, method="get", action="/services/data/v39.0/query/", data={}):

    auth = _authentication()
    if auth["status_code"] == 400:
        return auth
    else:
        headers = {
            "Content-type": "application/json; charset=UTF-8",
            "Accept-Encoding": "gzip",
            "Authorization": "Bearer %s" % auth["access_token"],
        }

        if method == "get":
            r = requests.request(
                method,
                auth["instance_url"] + action,
                headers=headers,
                params=parameters,
                timeout=30,
            )
        elif method == "post":
            r = requests.request(
                method,
                auth["instance_url"] + action,
                headers=headers,
                params=parameters,
                data=data,
            )
        else:
            return {"error": f"method '{method}' invalid", "succes": False}

        return r.json()


def _get_data(query=""):
    try:
        r_json = _call(parameters={"q": query})
        if "records" not in r_json:
            raise NameError(r_json)
        else:
            data = json.dumps(r_json["records"])
            if data == "[]":
                print("JSON is empty")
                return None
            else:
                deliverymen = pd.read_json(data)
                return deliverymen
    except BaseException as e:
        print(e)


def getDeliverymen(test=False):
    if test:
        df = _test(table="deliverymen")
    else:
        query_deliverymen = """
        SELECT
            Id,
            car_capacity__c,
            DeliveryManLocation__Latitude__s,
            DeliveryManLocation__Longitude__s
        FROM Entregadores__c
        WHERE Next_WorkDay__c = TRUE
        """
        df = _get_data(query_deliverymen)
        if df is not None:
            df = df[
                [
                    "Id",
                    "car_capacity__c",
                    "DeliveryManLocation__Latitude__s",
                    "DeliveryManLocation__Longitude__s",
                ]
            ]
            # df = df.rename(columns={"Id":"Id"})
            df.Id = df.Id.astype("string")

    return df


def getOrders(test=False, seed=None, _where="WHERE CreatedDate__c = Yesterday"):
    if test:
        df = _test(table="orders", seed=seed)
    else:
        query_orders = f"""
        SELECT
            ExternalId__c,
            TamanhoPacote__c,
            CollectPoint__Latitude__s,
            CollectPoint__Longitude__s,
            DeliveryPoint__Latitude__s,
            DeliveryPoint__Longitude__s
        FROM SolicitacaoEntrega__c
        {_where}
        """

        df = _get_data(query_orders)
        if df is not None:
            df = df[
                [
                    "ExternalId__c",
                    "TamanhoPacote__c",
                    "CollectPoint__Latitude__s",
                    "CollectPoint__Longitude__s",
                    "DeliveryPoint__Latitude__s",
                    "DeliveryPoint__Longitude__s",
                ]
            ]
            df = df.rename(columns={"ExternalId__c": "Id"})
            df.Id = df.Id.astype("string")
            # df = df.sample(n=50, random_state=21)

    return df


def postRoutes(body={}):
    print(f"\n\nbody: {json.dumps(body)}")
    status = list()
    try:
        for b in body:
            r_json = _call(
                action="/services/data/v48.0/sobjects/Rota__c/",
                method="post",
                data=json.dumps(b),
            )
            if "errorCode" in r_json:
                raise NameError(r_json[0])
            else:
                print({"body": b, "status": r_json})
                status.append({"body": b, "status": r_json})

        print(status)
        return status
    except BaseException as e:
        print(e)


def _test(table=None, seed=None):
    """
    Description:
    ------------
    Para fins de teste, essa função retornará 2 bases de amostras de teste,
    as quais passaram por tratamento para esse teste.
    Fonte: https://www.kaggle.com/olistbr/brazilian-ecommerce

    Return:
    -------
    List[DataFrame:"Deliverymen", DataFrame:"Orders"]
    """

    if table == "deliverymen":
        deliverymen = pd.read_csv(
            "..\\Delivery-Clustering\\Notebooks\\Bases\\Entregadores__c.csv"
        )
        deliverymen.Id = deliverymen.Id.astype("string")
        return deliverymen
    elif table == "orders":
        orders = (
            pd.read_csv(
                "..\\Delivery-Clustering\\Notebooks\\Bases\\SolicitacaoEntrega__c.csv"
            ).sample(n=50, random_state=seed)
            # random_state=21
        )
        orders.Id = orders.Id.astype("string")
        return orders
    else:
        print(f"ERRO: Base de teste {table} não encontrada.")
        return False
