from math import sqrt

import numpy as np
import pandas as pd


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


def _defineClusterVolume(order_clusters):

    df = _convertVolume(df=order_clusters, col_name="TamanhoPacote__c")

    df = df.groupby(["cluster"]).agg(
        cluster_volume=pd.NamedAgg(column="TamanhoPacote__c", aggfunc="min")
    )

    order_clusters = order_clusters.join(df, on="cluster", how="inner")

    return order_clusters


def _nearest_deliveryman(order_clusters, eligible_deliverymen):

    df = pd.merge(order_clusters, eligible_deliverymen, how="cross")

    xA_less_xB = (
        df["CollectPoint__Latitude__s"] - df["DeliveryManLocation__Latitude__s"]
    )
    yA_less_yB = (
        df["CollectPoint__Longitude__s"] - df["DeliveryManLocation__Longitude__s"]
    )
    df["distance"] = np.sqrt((xA_less_xB ** 2) + (yA_less_yB ** 2))

    nearest_deliveryman = (
        df[["Id_y", "distance", "cluster"]]
        .rename(columns={"Id_y": "Id"})
        .sort_values("distance", ascending=True)
        .iloc[:1]
    )

    id_deliveryman = nearest_deliveryman["Id"].values[0]

    return id_deliveryman


def _matching(order_clusters, deliverymen):

    order_clusters["id_deliveryman"] = "-1"

    for i in range(3):

        clusters = np.unique(order_clusters.query(f"cluster_volume == {i}")["cluster"])
        eligible_deliverymen = deliverymen[
            deliverymen.isin({"car_capacity__c": [0, 1, 2][: i + 1]})["car_capacity__c"]
        ]

        if not eligible_deliverymen.empty:
            for j in clusters:
                id_nearest_deliveryman = _nearest_deliveryman(
                    order_clusters.query(f"cluster == {j}"), eligible_deliverymen
                )

                order_clusters["id_deliveryman"] = np.where(
                    order_clusters["cluster"] == j,
                    str(id_nearest_deliveryman),
                    order_clusters["id_deliveryman"],
                )

                eligible_deliverymen = eligible_deliverymen.query(
                    f"Id != '{id_nearest_deliveryman}'"
                )
                deliverymen = deliverymen.query(f"Id != '{id_nearest_deliveryman}'")

                if len(eligible_deliverymen["Id"].values) == 0:
                    break

    return order_clusters


def run(order_clusters, deliverymen):

    original_order_clusters = order_clusters.copy()
    original_deliverymen = deliverymen.copy()

    order_clusters = _defineClusterVolume(order_clusters)
    deliverymen = _convertVolume(df=deliverymen, col_name="car_capacity__c")

    dfMatching = _matching(order_clusters=order_clusters, deliverymen=deliverymen)[
        ["Id", "id_deliveryman"]
    ]

    result = (
        original_order_clusters
        .join(dfMatching.set_index("Id"), on="Id", how="left")
        .join(
            original_deliverymen.rename(columns={"Id": "id_deliveryman"}).set_index("id_deliveryman"),
            on="id_deliveryman",
            how="left",
        )
    )

    return result
