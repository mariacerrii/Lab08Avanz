from database.distributore_DAO import DistributoreDAO
from database.prezzo_DAO import PrezzoDAO

'''
    MODELLO:
    - Rappresenta la struttura dati
    - Si occupa di gestire lo stato dell'applicazione
    - Interagisce con il database
'''

class Model:
    def __init__(self):
        self._distributori = None
        self.load_distributori()

        self.__sequenza_ottima = []
        self.__costo_ottimo = -1

    def load_distributori(self):
        """ Carica tutti i distributori e li setta nella variabile self._distributori """
        self._distributori = DistributoreDAO.get_distributori()

    def get_prezzo_medio(self, mese:int):
        """
        Calcola, per ogni distributore, il prezzo medio al litro per il mese selezionato.
        :param mese: Mese selezionato (un intero da 1 a 12)
        :return: lista di tuple --> (nome del distributore, media), es. (Distributore A, 1.789)
        """
        risultato = []

        for distributore in self._distributori:
            prezzi = PrezzoDAO.get_prezzi(distributore.id)

            if prezzi is None:
                return []

            prezzi_mese = [
                prezzo.prezzo_litro
                for prezzo in prezzi
                if prezzo.data.month == mese]

            if len(prezzi_mese) > 0:
                media = sum(prezzi_mese) / len(prezzi_mese)
                risultato.append((distributore.nome, round(media, 3)))
        return risultato

    def get_sequenza_ottima(self, mese:int):
        """
        Calcola la sequenza ottimale di rifornimenti nei primi 7 giorni
        :return: sequenza di nomi distributore ottimale
        :return: costo ottimale (cioè quello minimizzato dalla sequenza scelta)
        """
        self.__sequenza_ottima = []
        self.__costo_ottimo = -1
        prezzi_settimana = self.__get_prezzi_prima_settimana_mese(mese)

        self.__ricorsione([], 1, None, 0, prezzi_settimana)

        # Traduci gli ID in nomi
        id_to_nome = {distributore.id: distributore.nome for distributore in self._distributori}
        sequenza_nomi = [f"Giorno {giorno}: {id_to_nome[i]}" for giorno, i in enumerate(self.__sequenza_ottima, start=1)]
        return sequenza_nomi, round(self.__costo_ottimo, 2)

    def __ricorsione(self, sequenza_parziale, giorno, ultimo_distributore, costo_corrente, prezzi_settimana):
        """ Implementa la ricorsione """
        #USIAMO STRUTTURA DATA IN LAIB
        # 🟤E - Nessuna operazione sempre necessaria

        # 🟢A -CASO BASE
        if giorno > 7:
            if self.__costo_ottimo == -1 or costo_corrente < self.__costo_ottimo:
                self.__costo_ottimo = costo_corrente
                self.__sequenza_ottima = sequenza_parziale.copy()
            return

        # Provo ogni distributore disponibile
        for id_distributore, prezzi in prezzi_settimana.items():

            # 🟡C - FILTRO: salto prezzi mancanti
            prezzo_litro = prezzi[giorno - 1]
            if prezzo_litro is None:
                continue

            # 🔵B - CALCOLO PARZIALE
            costo_giorno = prezzo_litro * 100

            if ultimo_distributore is not None and ultimo_distributore != id_distributore:
                costo_giorno += 5

            sequenza_parziale.append(id_distributore)

            # 🟡C - RICORSIONE
            self.__ricorsione(
                sequenza_parziale,
                giorno + 1,
                id_distributore,
                costo_corrente + costo_giorno,
                prezzi_settimana
            )

            # 🟣D - BACKTRACKING
            sequenza_parziale.pop()

    def __get_prezzi_prima_settimana_mese(self, mese: int):
        """
        Restituisce i prezzi dei primi 7 giorni del mese selezionato per ciascun distributore.
        :return: un dizionario: {id_distributore: [prezzo_giorno1, ..., prezzo_giorno7]}
        """
        # Creo un dizionario vuoto che conterrà i prezzi dei primi 7 giorni per ciascun distributore
        prezzi_settimana = {}

        # Scorro tutti i distributori caricati nel Model
        for distributore in self._distributori:
            # Recupero dal database tutti i prezzi del distributore tramite il metodo del DAO
            prezzi = PrezzoDAO.get_prezzi(distributore.id)

            # Se il DAO non riesce a recuperare i prezzi, restituisco un dizionario vuoto
            if prezzi is None:
                return {}

            # Creo nel dizionario una voce per il distributore con una lista di 7 posizioni inizialmente vuote
            prezzi_settimana[distributore.id] = [None] * 7

            # Scorro tutti i prezzi recuperati dal database
            for prezzo in prezzi:
                # prezzi mese selezionato tra 1 e 7
                if prezzo.data.month == mese and 1 <= prezzo.data.day <= 7:
                    # Converto il giorno in un indice della lista:
                    # giorno 1 -> indice 0, giorno 7 -> indice 6
                    giorno = prezzo.data.day - 1
                    # Inserisco il prezzo al litro nella posizione corrispondente al giorno
                    prezzi_settimana[distributore.id][giorno] = prezzo.prezzo_litro

        return prezzi_settimana