import random

class Strategy:
    def __init__(self, rows: int, cols: int, ships_dict: dict[int, int]):
        """
        Inicializuje strategii pro hru Battleship.

        Parametry:
        - rows: Počet řádků na herní desce.
        - cols: Počet sloupců na herní desce.
        - ships_dict: Slovník, kde klíče jsou velikosti lodí a hodnoty jsou počty lodí dané velikosti.
        """
        self.rows = rows
        self.cols = cols
        self.ships_dict = ships_dict
        self.enemy_board = [['?' for _ in range(cols)] for _ in range(rows)]  # Inicializace desky nepřítele
        self.shots_fired = set()  # Množina souřadnic, kde byly vystřeleny střely
        self.missed_shots = set()  # Množina souřadnic, kde střely minuly
        self.hit_queue = []  # Seznam možných cílených útoků po zásahu lodi
        self.current_hits = []  # Seznam souřadnic aktuálně zasažené lodi
        self.available_shots = {(x, y) for x in range(cols) for y in range(rows)}  # Množina všech možných střel

    def get_random_shot(self):
        """
        Získá náhodnou střelu z dostupných střel.

        Vrací:
        - N-tici (x, y) reprezentující náhodnou střelu, nebo None, pokud nejsou žádné střely dostupné.
        """
        if not self.available_shots:
            return None  # Pokud není žádná dostupná střela, vrátí None
        return random.choice(tuple(self.available_shots))  # Vybere náhodnou dostupnou střelu

    def get_next_attack(self) -> tuple[int, int]:
        """
        Získá další střelu k útoku, přičemž dává přednost střelám z hit queue.

        Vrací:
        - N-tici (x, y) reprezentující další střelu.
        """
        if self.hit_queue:
            return self.hit_queue.pop(0)  # Pokud jsou nějaké zásahy, pokračuj v útoku na sousední pole
        return self.get_random_shot()  # Jinak zvol náhodnou střelu

    def register_attack(self, x: int, y: int, is_hit: bool, is_sunk: bool) -> None:
        """
        Registrovat výsledek útoku na desce nepřítele.

        Parametry:
        - x: X-ová souřadnice útoku.
        - y: Y-ová souřadnice útoku.
        - is_hit: Boolovská hodnota, zda střela zasáhla loď.
        - is_sunk: Boolovská hodnota, zda byla loď potopena (všechny její části byly zasaženy).
        """
        self.shots_fired.add((x, y))  # Označíme, že byla střela vystřelena
        self.available_shots.discard((x, y))  # Odebereme střelu z dostupných střel
        self.enemy_board[y][x] = 'H' if is_hit else 'M'  # Označíme výsledek na desce nepřítele
        
        if not is_hit:
            self.missed_shots.add((x, y))  # Sledujeme minulé střely
            return

        self.current_hits.append((x, y))  # Sledujeme zasažené buňky
        if is_sunk:
            self.identify_sunk_ship()  # Pokud byla loď potopena, aktualizujeme počet lodí
            self.mark_surrounding_cells()  # Označíme sousední buňky jako neplatné pro útok
            self.hit_queue.clear()  # Vyčistíme hit queue, protože loď byla potopena
            self.current_hits.clear()  # Vyčistíme seznam zasažených buněk
        else:
            self.hit_queue.extend(self.get_target_cells())  # Přidáme možné cíle pro další útoky

    def get_adjacent_cells(self, x, y):
        """
        Získá platné sousední buňky (nahoře, dole, vlevo, vpravo) kolem dané souřadnice.

        Parametry:
        - x: X-ová souřadnice buňky.
        - y: Y-ová souřadnice buňky.

        Vrací:
        - Seznam platných sousedních buněk v rámci desky, které jsou stále dostupné pro střelbu.
        """
        candidates = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]  # Seznam sousedních souřadnic
        return [(cx, cy) for cx, cy in candidates
                if 0 <= cx < self.cols and 0 <= cy < self.rows and (cx, cy) in self.available_shots]

    def get_target_cells(self):
        """
        Určuje další cílové buňky na základě aktuálních zásahů.

        Vrací:
        - Seznam cílových souřadnic pro další útoky.
        """
        if len(self.current_hits) == 1:
            return self.get_adjacent_cells(*self.current_hits[0])  # Pokud máme pouze jeden zásah, útočíme na sousední buňky
        
        xs, ys = zip(*self.current_hits)  # Získáme x a y souřadnice aktuálních zásahů
        
        if len(set(xs)) == 1:
            # Vertikální zásah (stejné x pro všechny zásahy)
            min_y, max_y = min(ys), max(ys)
            targets = [(xs[0], min_y - 1), (xs[0], max_y + 1)]  # Útočíme nad a pod zásahy
        else:
            # Horizontální zásah (stejné y pro všechny zásahy)
            min_x, max_x = min(xs), max(xs)
            targets = [(min_x - 1, ys[0]), (max_x + 1, ys[0])]  # Útočíme vlevo a vpravo od zásahů
        
        return [(cx, cy) for cx, cy in targets if (cx, cy) in self.available_shots]  # Platné střely

    def identify_sunk_ship(self):
        """
        Označí loď jako potopenou na základě aktuálních zásahů.

        Tato metoda sníží počet lodí dané velikosti ve slovníku lodí.
        """
        ship_size = len(self.current_hits)  # Velikost lodi je rovna počtu zásahů
        if ship_size in self.ships_dict and self.ships_dict[ship_size] > 0:
            self.ships_dict[ship_size] -= 1  # Snížíme počet lodí dané velikosti

    def mark_surrounding_cells(self):
        """
        Označí buňky kolem potopené lodi jako neplatné pro střelbu.
        """
        for x, y in self.current_hits:
            neighbors = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]  # Sousední buňky k označení
            for nx, ny in neighbors:
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    self.available_shots.discard((nx, ny))  # Odebereme neplatné buňky
                    self.enemy_board[ny][nx] = 'M'  # Označíme buňku jako minulé místo

    def get_enemy_board(self) -> list[list[str]]:
        """
        Získá aktuální stav desky nepřítele.

        Vrací:
        - Desku nepřítele (2D seznam znaků) ukazující zásahy a minulé střely.
        """
        return self.enemy_board

    def get_remaining_ships(self) -> dict[int, int]:
        """
        Získá aktuální počet zbývajících lodí podle velikosti.

        Vrací:
        - Slovník zbývajících lodí podle jejich velikosti.
        """
        return self.ships_dict

    def all_ships_sunk(self) -> bool:
        """
        Zkontroluje, zda byly všechny lodě potopeny.

        Vrací:
        - True, pokud byly všechny lodě potopeny, jinak False.
        """
        return all(count == 0 for count in self.ships_dict.values())  # Pokud jsou všechny lodě potopeny, vrátí True
