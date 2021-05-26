import json

import numpy as np
import pandas as pd
import requests
from sklearn.cluster import KMeans

pd.options.mode.chained_assignment = None


def _convertVolume(df, col_name):
    df[col_name] = np.where(
        df.isin({col_name: ["Alta", "Grande"]})[col_name],
        0,
        np.where(
            df.isin({col_name: ["Média", "Médio"]})[col_name],
            1,
            np.where(df.isin({col_name: ["Baixa", "Pequeno"]})[col_name], 2, -1),
        ),
    )
    return df


def run(deliverymen, orders, seed=None):
    try:
        nr_ordens = np.count_nonzero(orders.index)
        nr_entregadores = np.count_nonzero(np.unique(deliverymen.Id))
        if nr_entregadores < nr_ordens:
            nr_clusters = nr_entregadores
        else:
            nr_clusters = nr_ordens

        print(f"Defined {nr_clusters} clusters")

        features = orders[
            [
                "CollectPoint__Latitude__s",
                "CollectPoint__Longitude__s",
                "DeliveryPoint__Latitude__s",
                "DeliveryPoint__Longitude__s",
                "TamanhoPacote__c",
            ]
        ]

        features = _convertVolume(df=features, col_name="TamanhoPacote__c")

        km = KMeans(n_clusters=nr_clusters, random_state=seed)
        km.fit(features)

        orders["cluster"] = km.labels_

        return orders
    except BaseException as e:
        print(e)
