from City import Cities
from Individuals import Individuals
from random import choices
import numpy as np

import sys

class GeneticAlgorithm:
    def __init__(self, population_size=20, cities=[], verbose=False):
        self.populationSize = population_size
        self.population = []
        self.generation = 0
        self.best_solution = None
        self.cities = cities
        self.verbose = verbose

    # time_distances será um array 2D
    # cities será [City("A", [0, 10]), City("B", [10, 0])]
    def init_population(self, time_distances, cities):
        for _ in range(self.populationSize):
            self.population.append(Individuals(time_distances=time_distances, cities=cities, verbose=self.verbose))

    def sort_population(self, population):
        """
        orderna a população pelo atributo travelled_distance ascendentemente
        """
        self.population = sorted(
            self.population,
            key=lambda population: population.travelled_distance,
            reverse=False,
        )

        return population

    def best_individual(self, population):
        """
        caso encontre um indivíduo com menor distância o marcamos como melhor solução
        no atributo self.best_solution
        """
        population = self.sort_population(population)
        
        best = population[0]

        if self.best_solution is None:
            self.best_solution = best
        elif best.travelled_distance < self.best_solution.travelled_distance:
            self.best_solution = best
        
        return best

    def get_total_travelled_distance(self):
        """
        Soma distância percorrida por cada indivíduo da população
        """
        total_travelled_distance = 0

        for individual in self.population:
            distance = individual.travelled_distance
        
            if distance != np.inf:
                total_travelled_distance += distance
        
        return total_travelled_distance

    def select_parents(self):
        """
        Este método seleciona pais com base na roleta viciada onde,
        sendo a escolha aleatória, indivíduos com as menores distâncias percorridas
        possuem maior probabilidade de serem escolhidos.

        Os pesos são inversamente proporcionais à distância percorrida
        weight = 1-(travelled_distance / total_travelled_distance)
        Sendo:
            total_travelled_distance: a soma de todas as travelled_distance da população
        """
        parent = -1  # nenhum indivíduo sorteado
        
        total_travelled_distance = self.get_total_travelled_distance()

        weights = [
            (1 - (p.travelled_distance / total_travelled_distance))
            if p.travelled_distance != np.inf
            else 0
            for p in self.population
        ]
        if np.sum(weights) == 0:
            weights = None

        parent = choices(range(len(self.population)), weights, k=1)

        return parent[0]

    def resolve(self, mutationRate, min_generations, time_distances, cities):
        self.init_population(time_distances, cities)
        for individual in self.population:
            individual.fitness()

        self.best_individual(self.population)

        for generation in range(min_generations):

            newPopulation = []
            if self.verbose:
                print("generation:", generation)

            for _ in range(0, self.populationSize, 2):
                # seleciona dois indivíduos para reprodução - cai na roleta
                parent1 = self.select_parents()
                parent2 = self.select_parents()

                # cria os filhos a partir de dois pais
                childs = self.population[parent1].crossover(self.population[parent2])

                newPopulation.append(childs[0].mutate(mutationRate))
                newPopulation.append(childs[1].mutate(mutationRate))

            # sobrescreve antiga população eliminando os pais
            self.population = list(newPopulation)

            for individual in self.population:
                individual.fitness()
                if self.verbose:
                    print(f"Generation: {generation} New population: {individual.chromosome} - Travelled Distance: {individual.travelled_distance}")

            self.best_individual(self.population)

            if (generation == (min_generations - 1)) & (self.best_solution.travelled_distance == np.inf):
                print(f"Nenhuma rota válida pode ser gerada com  'min_generations' == {min_generations}.")
                sys.exit(0)

        print(f"Melhor solução -> Generation: {self.best_solution.generation} - Distância percorrida: {self.best_solution.travelled_distance} - Cromossomo: {self.best_solution.visited_cities}")

        print(
            "check_chromosome:",
            self.best_solution.check_chromosome(self.best_solution.chromosome),
        )

        return [
            self.best_solution.generation,
            self.best_solution.travelled_distance,
            self.best_solution.visited_cities,
        ]


def run(event=None, test=False, verbose=False):
    """
    event example:
    event = {
        'populationSize':20,
        "mutationRate":1,
        "min_generations":1000,
        'matrix':{"a":["deliveryMan", "b", [None, 1, None, None, None]],
                       "b":["collect", "d", [1, None, 2, 4, 5]],
                       "c":["collect", "e", [3, 2, None, 5, 6]],
                       "d":["delivery", "b", [7, 4, 5, None, 6]],
                       "e":["delivery", "c", [9, 5, 6, 6, None]],
                    },
    }
    """
    if test:
        event = {
            "populationSize": 20,
            "mutationRate": 1,
            "min_generations": 1000,
            "matrix": {
                "a": ["deliveryMan", "b", [None, 1, None, None, None]],
                "b": ["collect", "d", [1, None, 2, 4, 5]],
                "c": ["collect", "e", [3, 2, None, 5, 6]],
                "d": ["delivery", "b", [7, 4, 5, None, 6]],
                "e": ["delivery", "c", [9, 5, 6, 6, None]],
            },
        }

    if event:
        population_size = int(event["populationSize"])
        mutation_rate = int(event["mutationRate"])
        min_generations = int(event["min_generations"])
        body_cities = event["matrix"]

        c = Cities()
        if body_cities:
            c.set_cities(body_cities)

        cities_list = c.get_cities()

        time_distances = [city.distances for city in cities_list]

        ga = GeneticAlgorithm(population_size=population_size, verbose=verbose)
        result = ga.resolve(mutation_rate, min_generations, time_distances, cities_list)

        to_return = {
            "generation": result[0],
            "travelled_distance": result[1],
            "chromosome": result[2],
            "cities": c.chromose_to_cities(result[2]),
        }
        return to_return
    else:
        return f"'event' is None. 'event':{event}"

# if __name__=="__main__":
#     run(test=True, verbose=False)