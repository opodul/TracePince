# Application d'acquisition série — Chauvin Arnoux

## 1. Objectif

Développer une application desktop Python permettant de communiquer avec un appareil de mesure Chauvin Arnoux — Harmonic & Power Meter via une liaison série.

L'application doit recevoir les données série, conserver une copie des données brutes, analyser les mesures et afficher les valeurs en temps réel sous forme de tableau et de graphiques.

L'application doit être conçue de manière modulaire afin de pouvoir adapter facilement le parser à différents modes de mesure ou à différents modèles d'appareils Chauvin Arnoux.

## 2. Communication série

L'application doit permettre de configurer les paramètres de la liaison série :

- Port série
- Baudrate
- Nombre de bits de données
- Parité
- Nombre de bits de stop
- RTS/CTS activé ou désactivé

Exemple de port :

`COM5`

Sous Linux, les ports seront typiquement :

- `/dev/ttyUSB0`
- `/dev/ttyACM0`

La communication série doit utiliser Python, idéalement avec la bibliothèque :

`pyserial`

Les paramètres initiaux de l'interface sont `19200` bauds avec `RTS/CTS`
activé. Ils restent modifiables avant la connexion.

### Gestion de la connexion

L'interface doit fournir :

- Liste des ports disponibles
- Rafraîchissement des ports
- Bouton Connecter
- Bouton Déconnecter
- État de la connexion
- Affichage des erreurs de communication

Exemple :

- ● Connecté — COM5

ou :

- ○ Déconnecté

L'application doit gérer proprement la déconnexion ou le retrait physique du périphérique.

## 3. Enregistrement des données brutes

Toutes les données reçues depuis le port série doivent être enregistrées automatiquement.

Le fichier doit conserver les données aussi fidèlement que possible afin de permettre une analyse ultérieure du protocole.

Chaque session de communication doit créer un nouveau fichier.

Exemple :

```text
logs/
├── serial_2026-09-20_14-32-15.log
├── serial_2026-09-20_15-04-27.log
└── serial_2026-09-20_15-18-42.log
```

Le timestamp doit être présent dans le nom du fichier.

Les données brutes ne doivent pas être remplacées par les valeurs parsées.

## 4. Format observé des données

Les traces disponibles montrent que l'appareil envoie des blocs de texte ASCII structurés.

Une session commence notamment par :

`******  HARMONIC & POWER  METER  ******`

Puis des informations générales :

- `* NAME:              SITE:`
- `* TIME:              DATE:`

et une description du type de mesure.

Exemple :

- `* VOLTAGE    AC+DC`
- `*                    SCAN: 01 mn  (005)`

Les données sont ensuite envoyées périodiquement sous forme de blocs.

Chaque bloc commence par :

`ELAPSED TIME: 00:00`

puis contient différentes mesures.

## 5. Mode VOLTAGE_ACDC

Exemple observé :

```text
  ELAPSED TIME: 00:00
 RMS    (V) =   1.43
 Peak+  (V) = + 1.46
 Peak-  (V) = + 1.40
 CF         =   1.02
 DC     (V) = + 1.43
 Freq ( Hz) =   0.00
```

Le parser doit reconnaître le mode :

`VOLTAGE_ACDC`

et extraire au minimum :

| Champ | Exemple | Unité |
|---|---:|---:|
| elapsed_time | 00:00 | — |
| RMS | 1.43 | V |
| Peak+ | 1.46 | V |
| Peak- | 1.40 | V |
| CF | 1.02 | — |
| DC | 1.43 | V |
| Frequency | 0.00 | Hz |

Le champ principal destiné au graphique de tension est :

`RMS (V)`

## 6. Mode CURRENT_DC

Exemple observé :

```text
  ELAPSED TIME: 00:00
 DC     (A) = + 2.08
 Peak+  (A) = + 2.27
 Peak-  (A) = + 1.86
 Ripple (%) =   19.8
 Freq ( Hz) =   0.00
```

Le parser doit reconnaître le mode :

`CURRENT_DC`

et extraire au minimum :

| Champ | Exemple | Unité |
|---|---:|---:|
| elapsed_time | 00:00 | — |
| DC | 2.08 | A |
| Peak+ | 2.27 | A |
| Peak- | 1.86 | A |
| Ripple | 19.8 | % |
| Frequency | 0.00 | Hz |

Le champ principal destiné au graphique de courant est :

`DC (A)`

## 7. Mode POWER_1PH_DC

Exemple observé :

```text
  ELAPSED TIME: 00:00
 P     ( W) = +  2.9
 A      (A) = + 2.11
 V      (V) = + 1.42
 Freq ( Hz) =   0.00
```

Le parser doit reconnaître le mode :

`POWER_1PH_DC`

et extraire :

| Champ | Exemple | Unité |
|---|---:|---:|
| elapsed_time | 00:00 | — |
| Power | 2.9 | W |
| Current | 2.11 | A |
| Voltage | 1.42 | V |
| Frequency | 0.00 | Hz |

Dans ce mode, les trois valeurs principales sont :

- `P = Power (W)`
- `A = Current (A)`
- `V = Voltage (V)`

## 8. Modèle de données interne

Le logiciel doit convertir les données reçues en objets de mesure structurés.

Par exemple :

```python
Measurement(
    timestamp=...,
    elapsed_time="00:01",
    mode="CURRENT",
    current=2.11,
    voltage=None,
    power=None,
    frequency=0.0,
    raw_block="..."
)
```

Pour le mode `POWER_1PH_DC` :

```python
Measurement(
    timestamp=...,
    elapsed_time="00:01",
        mode="POWER_1PH_DC",
    current=2.15,
    voltage=1.42,
    power=3.0,
    frequency=0.0,
    raw_block="..."
)
```

Les champs non disponibles doivent être représentés par `None` et non par `0`.

## 9. Association temporelle

Chaque mesure doit avoir au minimum deux informations temporelles :

- Timestamp système

Le timestamp correspondant au moment où le logiciel reçoit la mesure.

Exemple :

`2026-09-20 14:32:15.423`

- Elapsed time

Le temps envoyé par l'appareil :

`00:00`  
`00:01`  
`00:02`  
`...`

Le timestamp système sera utilisé pour les logs et l'affichage temporel.

L'elapsed_time fourni par l'appareil doit également être conservé.

## 10. Affichage temps réel

L'application doit afficher les valeurs reçues en direct.

### Tableau

Le tableau doit être capable d'afficher des données provenant des différents modes.

Exemple :

| Timestamp | Mode | Courant (A) | Tension (V) | Puissance (W) | Fréquence (Hz) |
|---|---|---:|---:|---:|---:|
| 14:32:15 | VOLTAGE | — | 1.43 | — | 0.00 |
| 14:32:16 | VOLTAGE | — | 1.43 | — | 0.00 |
| 14:33:01 | CURRENT | 2.08 | — | — | 0.00 |
| 14:33:02 | CURRENT | 2.11 | — | — | 0.00 |
| 14:34:10 | POWER_1PH_DC | 2.11 | 1.42 | 2.9 | 0.00 |

Les valeurs non disponibles doivent être affichées avec `—`.

## 11. Graphiques

L'application doit afficher les données en temps réel.

### Graphique courant

Tracer :

`Current (A) / temps`

Pour le mode `CURRENT_DC` :

`DC (A)`

Pour le mode `POWER_1PH_DC` :

`A (A)`

### Graphique tension

Tracer :

`Voltage (V) / temps`

Pour le mode `VOLTAGE_ACDC` :

`RMS (V)`

Pour le mode `POWER_1PH_DC` :

`V (V)`

### Graphique puissance

Lorsque le mode `POWER_1PH_DC` est utilisé, afficher également :

`Power (W) / temps`

## 12. Schéma générique des blocs

Le logiciel ne doit pas limiter le protocole à `VOLTAGE_ACDC`, `CURRENT_DC` et
`POWER_1PH_DC`. Le mode est détecté depuis l'en-tête du bloc, mais un mode
inconnu doit être accepté.

Chaque ligne numérique d'un bloc devient une valeur dont le nom est le
libellé reçu, nettoyé des espaces superflus. Par exemple :

- `DC     (A)` devient `DC (A)` ;
- `Freq ( Hz)` devient `Freq (Hz)` ;
- `CF` reste `CF`.

La mesure conserve donc un dictionnaire `values` contenant toutes les
colonnes du bloc, y compris celles que le programme ne connaît pas encore.
Les attributs historiques (`current`, `voltage`, `power`, etc.) peuvent être
alimentés lorsqu'un libellé connu est rencontré, mais ne doivent pas limiter
le tableau.

## 13. Tableau et changement de mode

Le tableau est construit à partir des colonnes des blocs reçus, et non d'une
liste fixe de grandeurs. Les colonnes de contexte sont `Timestamp`, `Mode` et
`Elapsed`, puis viennent les libellés numériques du bloc.

Lorsqu'un nouveau mode est détecté, les mesures en mémoire et les lignes du
tableau sont effacées. Le nouveau schéma est alors construit à partir du
premier bloc de ce mode. Les valeurs absentes d'un bloc sont affichées par
`-` et restent `None` dans le modèle lorsque le champ n'est pas présent.

Un bouton `Clear table` permet de vider manuellement les mesures, les lignes
du tableau et les courbes, sans interrompre la connexion série.

Chaque colonne numérique dispose d'une case à cocher. Une colonne cochée est
tracée ; les changements de sélection mettent à jour le graphique sans
modifier les données reçues.

Le tableau peut être exporté avec la commande `Export CSV`. Le fichier est
encodé en UTF-8 avec marqueur BOM et utilise le séparateur `;`, afin de
s'ouvrir directement dans LibreOffice Calc. Il contient les colonnes
`Timestamp`, `Mode`, `Elapsed` et toutes les colonnes numériques reçues.

## 14. Graphiques génériques

Un axe est créé pour chaque colonne sélectionnée. Tous les axes utilisent le
même axe X et les mêmes indices de mesure, afin que les courbes restent
parfaitement synchronisées même si une colonne est absente de certains blocs.
L'axe X représente l'ordre des blocs reçus ; `elapsed_time` reste affiché et
conservé dans le tableau.

Le graphique courant peut être exporté avec la commande `Export graph PDF`.
Le PDF est adapté à l'impression ; un export PNG est également proposé.

## 15. Injection d'un log enregistré

L'interface fournit une commande `Inject log` permettant de choisir un fichier
texte ou `.log`. Le contenu est envoyé au même parser incrémental que les
données série, puis affiché dans le tableau et les graphiques. L'injection
réinitialise le parser courant et n'écrase pas les fichiers bruts enregistrés
par une session série.

La puissance doit pouvoir être activée/désactivée dans l'interface.

## 12. Console série

L'application doit disposer d'une console permettant de voir les données brutes reçues.

Exemple :

```text
[14:32:15.421] ELAPSED TIME: 00:00
[14:32:15.422] RMS    (V) =   1.43
[14:32:15.422] Peak+  (V) = + 1.46
...
```

Cette console est importante pour :

- diagnostiquer les problèmes de communication ;
- comprendre le protocole ;
- vérifier le parser ;
- identifier de nouveaux modes de mesure.

Il doit être possible de vider la console sans supprimer le fichier de log.

## 13. Architecture logicielle

Le code doit être organisé en plusieurs composants indépendants.

Proposition :

```text
project/
├── main.py
├── requirements.txt
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── main_window.py
│   ├── serial_manager.py
│   ├── serial_logger.py
│   ├── protocol_parser.py
│   ├── measurement.py
│   ├── data_manager.py
│   └── plot_manager.py
│
├── logs/
│
└── tests/
    ├── test_parser.py
    └── samples/
        └── chauvin_arnoux_sample.txt
```

## 14. SerialManager

Responsabilités :

- ouvrir le port ;
- fermer le port ;
- configurer baudrate/parité/bits/stop bits ;
- gérer RTS/CTS ;
- lire les données ;
- détecter les erreurs ;
- signaler les données reçues au reste de l'application.

La lecture série ne doit jamais bloquer l'interface graphique.

Utiliser un thread dédié ou une architecture asynchrone appropriée.

## 15. SerialLogger

Responsabilités :

- créer automatiquement le fichier de session ;
- enregistrer les données brutes ;
- ajouter éventuellement le timestamp de réception ;
- gérer les erreurs d'écriture ;
- fermer proprement le fichier à la fin de la session.

Le logger ne doit pas modifier les données brutes.

## 16. ProtocolParser

Le parser doit fonctionner par blocs de mesure.

Il doit identifier automatiquement le mode à partir de l'en-tête :

- `VOLTAGE_ACDC`
- `CURRENT_DC`
- `POWER_1PH_DC`

Il doit ensuite reconnaître les lignes de mesures correspondantes.

Le parser doit utiliser des expressions régulières robustes afin de tolérer les variations d'espaces.

Par exemple, la ligne :

`RMS    (V) =   1.43`

doit être correctement analysée même si le nombre d'espaces change.

Même principe pour :

- `DC     (A) = + 2.08`
- `P     ( W) = +  2.9`

Le parser ne doit pas dépendre de positions fixes dans la chaîne.

## 17. Gestion des blocs

Une mesure complète est constituée de plusieurs lignes.

Le parser doit attendre d'avoir reçu un bloc suffisamment complet avant de générer un objet `Measurement`.

Exemple :

```text
ELAPSED TIME: 00:01
RMS    (V) =   1.43
Peak+  (V) = + 1.46
Peak-  (V) = + 1.40
CF         =   1.02
DC     (V) = + 1.43
Freq ( Hz) =   0.00
```

Le parser doit générer une seule mesure à partir de ce bloc.

## 18. Données brutes et données parsées

Il est essentiel de conserver deux niveaux de données.

### Niveau 1 — Raw

Les données originales reçues de l'appareil :

```text
RMS    (V) =   1.43
Peak+  (V) = + 1.46
...
```

### Niveau 2 — Parsed

Les données structurées :

```json
{
  "mode": "VOLTAGE",
  "voltage_rms": 1.43,
  "voltage_peak_positive": 1.46,
  "voltage_peak_negative": 1.40,
  "crest_factor": 1.02,
  "voltage_dc": 1.43,
  "frequency": 0.0
}
```

Les deux niveaux doivent rester indépendants.

## 19. Tests

Créer des tests unitaires à partir des traces réelles fournies.

Le parser doit notamment être testé avec :

- Un bloc `VOLTAGE_ACDC`.
- Un bloc `CURRENT_DC`.
- Un bloc `POWER_1PH_DC`.
- Plusieurs blocs successifs.
- Des espaces différents.
- Des valeurs positives et négatives.
- Des trames incomplètes.
- Des données inconnues.
- Une déconnexion au milieu d'un bloc.
- Plusieurs modes successifs.

Les traces fournies doivent être conservées comme fichiers de test.

## 20. Exemple de séquence réelle

La communication observée peut suivre cette séquence :

```text
Serial port COM5 opened
        │
        ▼
VOLTAGE
        │
        ├── 00:00
        ├── 00:01
        ├── 00:02
        └── ...
        │
        ▼
Serial port COM5 closed
        │
        ▼
Serial port COM5 opened
        │
        ▼
CURRENT
        │
        ├── 00:00
        ├── 00:01
        └── 00:02
        │
        ▼
Serial port COM5 closed
        │
        ▼
Serial port COM5 opened
        │
        ▼
POWER_1PH_DC
        │
        ├── 00:00
        └── 00:01
        │
        ▼
Serial port COM5 closed
```

L'application doit donc accepter qu'un mode de mesure soit utilisé pendant une période puis qu'un nouveau mode apparaisse après une reconnexion.

## 21. Configuration graphique souhaitée

L'interface peut être organisée comme suit :

```text
┌──────────────────────────────────────────────────────────────┐
│  CHAUVIN ARNOUX — SERIAL DATA ACQUISITION                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Port: [ /dev/ttyUSB0 ▼ ]   Baudrate: [ 9600 ▼ ]             │
│  Data: [ 8 ▼ ]  Parity: [ None ▼ ]  Stop: [ 1 ▼ ]           │
│  RTS/CTS: [ ]                                                │
│                                                              │
│  [ Connect ] [ Disconnect ]     ● Connected                 │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  CURRENT       VOLTAGE       POWER                           │
│  2.11 A        1.42 V        3.0 W                           │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                     LIVE GRAPH                               │
│                                                              │
│                    ╱╲                                         │
│          ╱╲      ╱  ╲                                        │
│     ╱───╯  ╲────╯                                           │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  LIVE DATA                                                   │
│  ┌────────┬────────┬────────┬────────┐                      │
│  │ Time   │ A      │ V      │ W      │                      │
│  ├────────┼────────┼────────┼────────┤                      │
│  │ 00:00  │ 2.11   │ 1.42   │ 3.0    │                      │
│  │ 00:01  │ 2.15   │ 1.42   │ 3.0    │                      │
│  └────────┴────────┴────────┴────────┘                      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  RAW SERIAL DATA                                             │
│  > RMS (V) = 1.43                                           │
│  > Peak+ (V) = +1.46                                        │
│  > ...                                                       │
└──────────────────────────────────────────────────────────────┘
```

## 22. Contraintes importantes

- Ne jamais bloquer l'interface graphique pendant la lecture série.
- Ne jamais perdre volontairement les données brutes reçues.
- Ne jamais inventer une valeur lorsqu'une mesure n'est pas présente.
- Une valeur absente doit être `None` / `—`.
- Le parser doit être indépendant de l'interface graphique.
- Le logger doit fonctionner indépendamment du parser.
- Les données brutes doivent toujours être disponibles même si le parser rencontre une erreur.
- Une erreur de parsing ne doit pas interrompre l'acquisition série.
- Le système doit pouvoir fonctionner pendant plusieurs heures.
- Le nombre de données conservées en mémoire doit être limité/configurable.
- Les fichiers de logs doivent être fermés proprement lors de l'arrêt de l'application.

## 23. Technologies envisagées

Python 3.

### Communication série

`pyserial`

### Interface graphique

Choisir une solution adaptée à Linux et à l'affichage temps réel.

Pour le graphique, utiliser une bibliothèque permettant un affichage fluide des séries temporelles.

Le choix précis du framework GUI doit être fait en tenant compte de l'environnement cible :

- Fedora Sway Atomic ou ubuntu
- Python
- VS Code Flatpak ou en archive
- Toolbox ou non

## 24. Évolution future

L'architecture doit permettre d'ajouter ultérieurement :

- d'autres modèles Chauvin Arnoux ;
- d'autres modes de mesure ;
- export CSV ;
- export JSON ;
- export Excel ;
- sauvegarde des mesures parsées ;
- statistiques min/max/moyenne ;
- alarmes sur seuil ;
- enregistrement automatique des sessions ;
- sélection de plusieurs courbes ;
- curseurs sur le graphique ;
- zoom temporel ;
- reprise après déconnexion ;
- reconnexion automatique ;
- configuration sauvegardée ;
- détection automatique des paramètres série.
- reinjection de log ;




