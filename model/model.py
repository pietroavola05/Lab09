from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):
        self.tour_map = {}  # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {}  # Mappa ID attrazione -> oggetti Attrazione

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        self._tour_attrazione = []

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
        for relazione in relazioni:
            id_tour = relazione["id_tour"]
            id_attrazione = relazione["id_attrazione"]
            tour = self.tour_map[id_tour]
            attrazione = self.attrazioni_map[id_attrazione]
            tour.attrazioni.add(attrazione)
            attrazione.tour.add(tour)

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

        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        tour_regione_selezionata = self._get_tour_per_regione(id_regione)

        self._ricorsione(
            tour_regione_selezionata,
            [], 0, 0, 0, set(), max_giorni, max_budget)

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, tour_disponibili: list, pacchetto_parziale: list,
                    durata_corrente: int, costo_corrente: float,
                    valore_corrente: int, attrazioni_usate: set,
                    max_giorni: int, max_budget: float):

        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente

        # TERMINAZIONE: interrompi la ricorsione solo quando non ci sono più tour da considerare.
        if len(tour_disponibili) == 0:
            return

        #considero tutti i tour
        for tour in tour_disponibili:
            nuova_durata = durata_corrente + tour.durata_giorni
            nuovo_costo = costo_corrente + tour.costo

            # vincoli durata/costo
            if (max_giorni is not None and nuova_durata > max_giorni) or (max_budget is not None and nuovo_costo > max_budget):
                continue

            # vincolo attrazioni uniche
            if len(tour.attrazioni.intersection(attrazioni_usate)) > 0:
                continue

            nuovo_valore = valore_corrente + sum(a.valore_culturale for a in tour.attrazioni)
            nuove_attrazioni = attrazioni_usate.union(tour.attrazioni)
            nuovo_pacchetto = pacchetto_parziale + [tour]

            # nuovi tour rimanenti (deepcopy)
            nuovi_tour = tour_disponibili.copy()
            nuovi_tour.remove(tour)
            # ricorsione
            self._ricorsione(
                nuovi_tour,
                nuovo_pacchetto,
                nuova_durata,
                nuovo_costo,
                nuovo_valore,
                nuove_attrazioni,
                max_giorni,
                max_budget
            )

    def _get_tour_per_regione(self, id_regione):
        tour_per_regione = [
            tour for tour in self.tour_map.values()
            if tour.id_regione == id_regione]

        return tour_per_regione