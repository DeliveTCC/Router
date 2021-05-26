from random import randint, sample
import numpy as np

from City import Distance


class Individuals:
    def __init__(self, time_distances, cities, generation=0, init_chromosome=True, verbose=False):
        self.time_distances = time_distances  # 2D array [[], []]
        self.cities = cities  # City list [City(), City()]
        self.generation = generation
        self.note_review = 0
        self.chromosome = []
        self.visited_cities = []
        self.travelled_distance = 0
        self.probability = 0
        self.verbose = verbose

        # if init_chromosome:
        # Cria cromossomos (não repete cidades)
        # Ex.: [0, 2, 3, 1] --> [A, C, D, B]
        cities_copy = self.cities.copy()
        for i in range(len(cities_copy)):
            cities_copy[i]._index = i

        names_aux = []

        # Adicionando ponto de partida que é a localição do DeliveryMan
        for i in range(len(cities_copy)):
            if cities_copy[i].trip_type == "deliveryMan":

                names_aux.append(cities_copy[i].name)

                collect_point = cities_copy[i].detail
                names_aux.append(collect_point)

                self.chromosome.append(cities_copy.pop(i)._index)

                # Adicionando ponto de destino do deliveryMan
                for j in range(len(cities_copy)):
                    if cities_copy[j].name == collect_point:
                        self.chromosome.append(cities_copy.pop(j)._index)
                        break
                break

        while len(cities_copy) > 0:

            x = randint(0, len(cities_copy) - 1)
            gene = cities_copy[x]._index
            self.chromosome.append(gene)

            if self.check_chromosome(chromosome=self.chromosome):
                cities_copy.pop(x)
            else:
                self.chromosome.pop(-1)

    # Avaliação de aptidão
    def fitness(self):
        sum_distance = 0
        current_city = self.chromosome[0]

        for dest_city in self.chromosome:
            d = Distance(self.cities)
            distance = d.get_distance(current_city, dest_city)
            sum_distance += distance
            self.visited_cities.append(dest_city)
            current_city = dest_city

            # soma distância da última cidade para a primeira - caminho de volta
            if dest_city == self.chromosome[-1]:
                sum_distance += d.get_distance(
                    self.chromosome[len(self.chromosome) - 1], self.chromosome[0]
                )

        self.travelled_distance = sum_distance

    def crossover(self, otherIndividual):
        """
        Alteração dos cromossomos para trazer diversidade nas gerações
        Sorteia um gene no cromossomo e realiza a troca, respeitando o critério de não conter genes duplicados,
        e de ser um cromossomo válido.
        """
        chromosome_1 = self.chromosome.copy()
        chromosome_2 = otherIndividual.chromosome.copy()
        children_chromosomes = tuple()

        if chromosome_1 == chromosome_2:
            children_chromosomes = (chromosome_1, chromosome_2)
        else:
            _break = 0
            while True:
                children_chromosomes = self.pmx(
                    chromosome_1.copy(), chromosome_2.copy()
                )
                # para ao formar um cromossomo válido
                if self.check_chromosome(children_chromosomes[0]) & self.check_chromosome(children_chromosomes[1]):
                    break
                # ou após 100 tentativas sem sucesso para evitar loops infinitos
                elif _break == 100:
                    children_chromosomes = (chromosome_1, chromosome_2)
                    break
                _break += 1

        childs = [
            Individuals(self.time_distances, self.cities, self.generation + 1),
            Individuals(self.time_distances, self.cities, self.generation + 1),
        ]

        childs[0].chromosome = children_chromosomes[0]
        childs[1].chromosome = children_chromosomes[1]

        return childs

    def pmx(self, chromosome_1: list(), chromosome_2: list()):
        """
        Realiza combinação dos genes entre dois cromossomos
        Método: PMX (Partially Mapped Crossover)
        Fontes:
            1. Artigo:
                Genetic Algorithm for Traveling Salesman Problem with Modified Cycle Crossover Operator (2017)
                Capítulo 2.1.1
                https://doi.org/10.1155/2017/7430125 (Acesso em 14/04/2021)

            2. Palestra:
                [PyBR14] Algoritmo Genético com Python - Ana Paula Mendes
                https://youtu.be/PCa0koOOQnM?t=814 (Acesso em 14/04/2021)

        Args:
            chromosome_1 (list): lista de inteiros que será combinado com a lista chromosome_2
            chromosome_2 (list): lista de inteiros que será combinado com a lista chromosome_1

        Returns:
            chromosome_result (tuple): tuple com as duas listas de cromossomos resultantes
        """
        p1 = randint(2, len(chromosome_1) - 1)
        p2 = p1 + 1

        section_1 = chromosome_1[p1:p2]
        section_2 = chromosome_2[p1:p2]

        # reservando posições para o cruzamento
        for i in range(p1, p2):
            chromosome_1[i] = "reserved"
            chromosome_2[i] = "reserved"

        # Removendo genes que ficariam duplicados após o cruzamento
        # Para cada gene de section_2 que já exista no cromossomo
        # É substituido por um gene de section_1 que não exista em section_2
        replaced = []
        for s2 in section_2:
            if s2 in chromosome_1:
                index = chromosome_1.index(s2)
                for s1 in section_1:
                    if (s1 not in section_2) & (s1 not in replaced):
                        chromosome_1[index] = s1
                        replaced.append(s1)
                        break

        replaced = []
        for s1 in section_1:
            if s1 in chromosome_2:
                index = chromosome_2.index(s1)
                for s2 in section_2:
                    if (s2 not in section_1) & (s2 not in replaced):
                        chromosome_2[index] = s2
                        replaced.append(s2)
                        break

        chromosome_1[p1:p2] = section_2
        chromosome_2[p1:p2] = section_1

        return (chromosome_1, chromosome_2)

    def get_duplicated_gene(self, genes, exchanged_genes):
        """
        Busca genes duplicados em um cromossomo
        """
        for gene in range(len(genes)):
            if gene in exchanged_genes:
                continue

            if len([g for g in genes if g == genes[gene]]) > 1:
                return gene

        return -1

    def mutate(self, mutationRate):
        """
        Mutação
        Sorteia um intervalo de 1% a 100%, se corresponder a taxa de mutação altera os genes
        Respeita o critério de não existir genes duplicados
        """
        while True:
            # sorteia um intervalo de 1% a 100%
            if randint(1, 100) <= mutationRate:
                # if self.verbose:
                #     print("Realizando mutação no cromossomo %s" % self.chromosome)
                genes = self.chromosome.copy()
                # iniciando range em 2, 0 é entregador e 1 a coleta mais próxima
                gene_1 = randint(2, len(genes) - 1)
                gene_2 = randint(2, len(genes) - 1)
                tmp = genes[gene_1]
                genes[gene_1] = genes[gene_2]
                genes[gene_2] = tmp
                # if self.verbose:
                #     print("Valor após mutação: %s" % self.chromosome)

                if self.check_chromosome(genes):
                    self.chromosome = genes
                    break

        return self

    def check_chromosome(self, chromosome=[]):
        """
        Verifica se o cromossomo é válido.
        """
        return self.check_duplicates(chromosome) & self.check_requirements(chromosome)

    def check_duplicates(self, chromosome=[]):
        """
        Verifica se existe genes duplicados no cromossomo
        """
        return len(chromosome) == len(set(chromosome))

    def check_requirements(self, chromosome=[]):
        """
        Verifica se existe uma entrega antes de uma coleta
        """
        ok = True
        for i, gene in enumerate(chromosome):
            city = self.cities[gene]

            if city.trip_type == "delivery":
                previous_chromosome = chromosome[:i]
                # apenas os pontos anteriores ao da entrega
                previous_cities = [self.cities[g].name for g in previous_chromosome]

                if city.detail not in previous_cities:
                    ok = False
                    break
        return ok
