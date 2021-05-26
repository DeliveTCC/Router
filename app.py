import sys

sys.path.insert(0, ".//Delivery-Clustering//")
sys.path.insert(0, ".//SalesforceAPI//")
sys.path.insert(0, ".//GeneticAlgorithm//")
sys.path.insert(0, ".//Delivery-Router//")
import argparse
from datetime import datetime

import ClusteringOrders as cl
import GeneticAlgorithm as ge
import Matching as mt
import pandas as pd
import SalesforceAPI as sf

import DeliveryRouter as dr


def body_contructor(routes, dfMatching):
    body = list()
    for r in routes:
        cities = r["cities"]
        route = ""
        data = dict()
        for c in cities:
            aux = c.split("_")
            _id = aux[0]
            _type = aux[1]
            if _type == "deliveryMan":
                row = dfMatching.query(f"Id == '{_id}'")[
                    [
                        "DeliveryManLocation__Latitude__s",
                        "DeliveryManLocation__Longitude__s",
                        "id_deliveryman",
                    ]
                ].values[0]
                id_deliveryman = str(row[2])
            elif _type == "collect":
                row = dfMatching.query(f"Id == '{_id}'")[
                    ["CollectPoint__Latitude__s", "CollectPoint__Longitude__s"]
                ].values[0]
            elif _type == "delivery":
                row = dfMatching.query(f"Id == '{_id}'")[
                    ["DeliveryPoint__Latitude__s", "DeliveryPoint__Longitude__s"]
                ].values[0]
            route = f"{route}|{row[0]},{row[1]},{_type}"
        data = {
            "Entregador__c": id_deliveryman,
            "Rota__c": route[1:],
            "Status__c": "Nova",
        }
        body.append(data)

    return body


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--orders_where", type=str, default=None)
    parser.add_argument("--getOrders_test", type=bool, default=None)
    parser.add_argument("--sample_orders_n", type=int, default=None)
    parser.add_argument("--sample_deliverymen_n", type=int, default=None)
    parser.add_argument("--verbose", type=bool, default=False)

    args = parser.parse_args()

    print("\nGetting available Deliverymen...")
    deliverymen = sf.getDeliverymen()
    if args.sample_deliverymen_n:
        deliverymen = deliverymen.sample(
            n=args.sample_deliverymen_n, random_state=args.seed
        )
    if deliverymen is None:
        print("Sem entregadores disponíveis.")
        sys.exit(0)

    print(deliverymen["Id"].count(), "deliverymen")

    print("\nGetting orders...")
    if args.orders_where:
        orders = sf.getOrders(
            test=args.getOrders_test, seed=args.seed, _where=args.orders_where
        )
    else:
        orders = sf.getOrders(
            test=args.getOrders_test, seed=args.seed
        )

    if args.sample_orders_n:
        orders = orders.sample(n=args.sample_orders_n, random_state=args.seed)
    
    if orders is None:
        print("Sem entregas disponíveis.")
        sys.exit(0)

    print(orders["Id"].count(), "orders")

    print("\nClustering orders with KMeans...")
    order_clusters = cl.run(deliverymen=deliverymen, orders=orders, seed=args.seed)

    print("\nMatching orders and deliverymen...")
    dfMatching = mt.run(order_clusters, deliverymen)
    df_without_matching = dfMatching.query("id_deliveryman == '-1'")
    if df_without_matching.count().values[0] != 0:
        print("\nFound Orders without Matching with Deliveymen!")
        print(df_without_matching)
        
        today = datetime.today().strftime('%Y-%m-%d')
        path = f"./outputs/orders_without_matching-{today}.csv"
        df_without_matching.to_csv(path, index=False)
        print(f"\nOrders were saved in '{path}'")
        
        dfMatching = dfMatching.query("id_deliveryman != '-1'")

    print("\nStarting Router using Genetic Algorithm...")
    routes = dr.run(df=dfMatching, verbose=args.verbose)

    print("\nSaving Routes to the Salesforce DB...")
    body = body_contructor(routes, dfMatching)
    r = sf.postRoutes(body)
