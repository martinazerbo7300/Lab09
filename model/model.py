from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """

        relazioni = TourDAO.get_tour_attrazioni()

        # Inizializzo i set nelle classi
        for tour in self.tour_map.values():
            tour.attrazioni = set()
            tour.valore_culturale_totale = 0  # utile per velocizzare

        for attr in self.attrazioni_map.values():
            attr.tours = set()

        # Associo relazioni
        for row in relazioni:
            t_id = row["id_tour"]
            a_id = row["id_attrazione"]

            if t_id in self.tour_map and a_id in self.attrazioni_map:
                tour = self.tour_map[t_id]
                attr = self.attrazioni_map[a_id]

                tour.attrazioni.add(attr)
                attr.tours.add(tour)

        # Calcolo il valore culturale totale del tour
        for tour in self.tour_map.values():
            tour.valore_culturale_totale = sum(
                attr.valore_culturale for attr in tour.attrazioni
            )


def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
    """
    Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
    :param id_regione: id della regione
    :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
    :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

    :return: self._pacchetto_ottimo (una lista di oggetti Tour)
    :return: self._costo (il costo del pacchetto)
    :return: self._valore_ottimo (il valore culturale del pacchetto)
    """

    if max_giorni is None or max_giorni == "":
        max_giorni = float("inf")
    if max_budget is None or max_budget == "":
        max_budget = float("inf")

    self._pacchetto_ottimo = []
    self._costo = 0
    self._valore_ottimo = -1

    tour_regione = [
        t for t in self.tour_map.values()
        if str(t.id_regione) == str(id_regione)
    ]

    # Ordinare i tour non è obbligatorio ma aiuta la ricorsione
    tour_regione.sort(key=lambda t: t.valore_culturale_totale, reverse=True)

    # Avvio ricorsione
    self._ricorsione(
        start_index=0,
        pacchetto_parziale=[],
        durata_corrente=0,
        costo_corrente=0,
        valore_corrente=0,
        attrazioni_usate=set(),
        lista_tour=tour_regione,
        max_giorni=max_giorni,
        max_budget=max_budget
    )

    return self._pacchetto_ottimo, self._costo, self._valore_ottimo


def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, attrazioni_usate: set, lista_tour: list, max_giorni: int, max_budget: int):
    """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il valore culturale"""

    if valore_corrente > self._valore_ottimo:
        self._valore_ottimo = valore_corrente
        self._pacchetto_ottimo = pacchetto_parziale.copy()
        self._costo = costo_corrente

        # 🔵 B: Ricorsione su tutti i tour successivi
    for i in range(start_index, len(lista_tour)):
        tour = lista_tour[i]

        # --- C: Vincoli ---

        # Durata
        if durata_corrente + tour.durata_giorni > max_giorni:
            continue

        # Budget
        if costo_corrente + tour.costo > max_budget:
            continue

        # Attrazioni duplicate → NON consentite
        if not attrazioni_usate.isdisjoint(tour.attrazioni):
            continue

        # --- D: Aggiungo il tour ---
        pacchetto_parziale.append(tour)

        nuove_attr = tour.attrazioni
        attrazioni_usate.update(nuove_attr)

        nuovo_valore = valore_corrente + tour.valore_culturale_totale

        # --- E: Ricorsione ---
        self._ricorsione(
            i + 1,
            pacchetto_parziale,
            durata_corrente + tour.durata_giorni,
            costo_corrente + tour.costo,
            nuovo_valore,
            attrazioni_usate,
            lista_tour,
            max_giorni,
            max_budget
        )

        # --- F: Backtracking ---
        pacchetto_parziale.pop()
        attrazioni_usate.difference_update(nuove_attr)