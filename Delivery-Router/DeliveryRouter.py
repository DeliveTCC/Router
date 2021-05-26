import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".//GeneticAlgorithm//")
import GeneticAlgorithm as ge

import GraphGenerator as gr


def MakeMatrix(df_graph):
    matrix = {}

    for _, d in df_graph.sort_values("origin_id").iterrows():

        origin_id = (
            d[["origin_id"]]
            .str.extract(pat=r"(.*)(_)(collect|delivery$|deliveryMan)")
            .values[0]
        )

        trip_type = origin_id[2]

        if trip_type == "collect":
            destination = origin_id[0] + "_delivery"
        elif trip_type == "delivery":
            destination = origin_id[0] + "_collect"
        else:
            destination = origin_id[0] + "_collect"

        matrix[d["origin_id"]] = [trip_type, destination, []]

    for _, d in df_graph.sort_values("origin_id").iterrows():
        d = dict(d)
        sorted_keys = sorted(d)

        for key in sorted_keys:
            if (key not in ["origin_id", "cluster", "type"]) & (key in matrix):
                distance = d[key]
                matrix[d["origin_id"]][2].append(
                    float(distance) if str(distance) != "nan" else None
                )

    return matrix


def run(df=None, populationSize=20, mutationRate=5, min_generations=1000, test=False, verbose=False):

    list_routes = list()

    if test:
        route = ge.run(test=test, verbose=verbose)
        list_routes.append(route)
    else:
        df_graphs = gr.run(df=df)
        pd.set_option("display.max_columns", None)

        clusters = np.unique(df_graphs["cluster"])

        for c in clusters:

            print(f"\nrunning to cluster {c}...")

            graph = df_graphs.query(f"cluster == {c}")

            matrix = MakeMatrix(graph)

            event = {
                "populationSize": 20,
                "mutationRate": 1,
                "min_generations": 1000,
                "matrix": matrix,
            }
            route = ge.run(event=event, verbose=verbose)
            list_routes.append(route)

    return list_routes
