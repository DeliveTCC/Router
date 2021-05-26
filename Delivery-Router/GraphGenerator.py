import pandas as pd
import numpy as np

pd.options.mode.chained_assignment = None


def _calculateCartesianDistance(points):

    for _, r in points.iterrows():
        xA_less_xB = points["lat"] - r["lat"]
        yA_less_yB = points["long"] - r["long"]
        points[r["Id"] + "_" + r["type"]] = np.sqrt(
            (xA_less_xB ** 2) + (yA_less_yB ** 2)
        )

    return points


def run(df):
    clusters = np.unique(df["cluster"])

    dfList = []

    for c in clusters:
        dfCluster = df.query(f"cluster == {c}")

        collectPoint = dfCluster[
            ["Id", "cluster", "CollectPoint__Latitude__s", "CollectPoint__Longitude__s"]
        ].rename(
            columns={
                "CollectPoint__Latitude__s": "lat",
                "CollectPoint__Longitude__s": "long",
            }
        )
        collectPoint["type"] = "collect"

        deliveryPoint = dfCluster[
            [
                "Id",
                "cluster",
                "DeliveryPoint__Latitude__s",
                "DeliveryPoint__Longitude__s",
            ]
        ].rename(
            columns={
                "DeliveryPoint__Latitude__s": "lat",
                "DeliveryPoint__Longitude__s": "long",
            }
        )
        deliveryPoint["type"] = "delivery"

        deliveryManLocation = dfCluster[
            [
                "Id",
                "cluster",
                "DeliveryManLocation__Latitude__s",
                "DeliveryManLocation__Longitude__s",
            ]
        ].rename(
            columns={
                "DeliveryManLocation__Latitude__s": "lat",
                "DeliveryManLocation__Longitude__s": "long",
            }
        )
        deliveryManLocation["type"] = "deliveryMan"

        points = pd.concat([deliveryManLocation, collectPoint, deliveryPoint])

        points = _calculateCartesianDistance(points)

        points = points.drop(["lat", "long"], 1).melt(id_vars=["Id", "type", "cluster"])

        points_2 = points.copy()

        # points_2 = points_2.query("value > 0")
        points_2 = points_2.loc[
            ((points["Id"] + "_" + points["type"]) != points["variable"])
            & ~(
                points["variable"].str.contains("_deliveryMan")
                & (points["value"] == 0.0)
            )
        ]

        points_2["rw"] = (
            points_2.sort_values("value", ascending=True)
            .groupby(["Id", "type"])
            .cumcount()
            + 1
        )

        # ideia inicial era seleciona apenas as k arestas de menor disância de cada ponto.
        # Porém foi constatado que era mais eficiente considerando todas as ligações possíveis,
        # ou seja, cada ponto possui uma aresta com todos os outros pontos do grafo.
        # Por esse motivo a linha abaixo foi comentada.
        # points_2 = points_2.query(f"rw in {[i for i in range(k+1)]}")

        points_2 = pd.merge(
            points.drop("value", 1),
            points_2,
            left_on=["Id", "type", "cluster", "variable"],
            right_on=["Id", "type", "cluster", "variable"],
            how="left",
        )

        points_2["origin_id"] = points_2["Id"] + "_" + points_2["type"]
        points_2 = points_2.rename(
            columns={"variable": "destination_id", "value": "distance"}
        )
        points_2 = points_2[
            ["origin_id", "type", "destination_id", "distance", "cluster"]
        ]

        # DeliveryMan terá apenas uma única direção possível no grafo,
        # sendo ela a origem da ordem mais próxima a ele
        deliveryMan = points_2.query("(type == 'deliveryMan')")
        deliveryMan = deliveryMan[deliveryMan.destination_id.str.contains(".*_collect")]
        deliveryMan = deliveryMan[
            deliveryMan.origin_id.str.extract("(.*)(_deliveryMan)")[0]
            == deliveryMan.destination_id.str.extract("(.*)(_collect)")[0]
        ]
        deliveryMan = deliveryMan.sort_values(by=["distance"], ascending=True)
        deliveryMan = deliveryMan.iloc[:1]
        # print(deliveryMan)

        points_3 = pd.concat([deliveryMan, points_2.query("type != 'deliveryMan'")])

        # Será retornado uma matriz de distâncias
        points_3 = points_3.pivot(
            index=["origin_id", "type", "cluster"],
            columns="destination_id",
            values="distance",
        )

        points_3 = points_3.reset_index()

        dfList.append(points_3)

    df_result = pd.concat(dfList)

    return df_result
