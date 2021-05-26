import numpy as np


class City:
    def __init__(self, name, trip_type, detail, distances):
        self.name = name
        self.trip_type = trip_type
        self.detail = detail
        distances = [np.inf if d is None else d for d in distances]
        self.distances = distances

    def getName(self):
        return self.name

    def getDistances(self):
        return self.distances


class Cities:
    def __init__(self, cities=[]):
        self.cities = cities

    def chromose_to_cities(self, chromosome):
        cities = []
        for i in range(len(chromosome)):
            cities.append(self.get_city(chromosome[i]).name)
        return cities

    def get_city_distances(self, index):
        return self.get_city(index).distances

    def get_cities(self):
        return self.cities

    def get_city(self, index):
        return self.cities[index]

    def set_cities(self, cities={}):
        self.cities = []
        for k, v in cities.items():
            c = City(name=k, trip_type=v[0], detail=v[1], distances=v[2])
            self.cities.append(c)

    def get_total_cities(self):
        return len(self.cities)


class Distance:
    def __init__(self, cities):
        self.cities = cities

    def get_distance(self, fromCity: int, toCity: int):
        if fromCity == toCity:
            return 0
        else:
            city1 = self.cities[fromCity]
            return city1.distances[toCity]
