# TQS_TF-QKD

## Descrizione

Il repository contiene il secondo progetto del corso [TECNOLOGIE QUANTISTICHE PER LA SICUREZZA](https://docenti.unisa.it/030400/didattica?anno=2025&id=524113&cId=10000-2025&pId=N0*N0*S2).

Utilizzando il simulatore [NetSquid](https://netsquid.org/) è stato implementato un simulatore di rete quantistica per il protocollo di distribuzione della chiave di tipo **Twin-Field (TF-QKD)**.

In particolare, il progetto modella l'hardware quantistico e integra algoritmi classici per il Sifting, la Parameter Estimation e l'Information Reconciliation tramite il protocollo **Cascade** (di cui è stata implementata solo la prima parte, ovvero quella inerente il controllo del bit di parità sacrificando un piccolo numero di qubit).

## Componenti

| Programma | Funzionalità |
| :--- | :--- |
| **`little_noisy_no_error_correction.py`** | **Proof of Concept**  - Esegue un test su 15 bit in presenza di pochissimo rumore (prob. 1%) per validare la logica di scambio e la correzione di parità. |
| **`noisy_benchmark_with_cascade.py`** | **Parameter Estimation** -  Sacrifica alcuni bit per la stima del canale rumoroso e implementa una prima versione deterministica dell'algoritmo Cascade su blocchi da 4 bit. |
| **`double_noisy_benchmark_with_cascade.py`** | **Motore Fisico** - Attiva il `DepolarNoiseModel` di NetSquid (oltre al rumore di default) per degradare le matrici di densità e mappa la resilienza di Cascade al variare del rumore hardware. |
| **`entropy_calculator_without_error_correction.py`** | **Baseline Analitica** - Esegue cicli statistici asintotici calcolando l'entropia binaria di Shannon per dimostrare matematicamente il collasso della chiave oltre l'11% di QBER. |
| **`entropy_calculator_with_cascade.py`** | **Simulatore Avanzato** - Integra Cascade, protocolli multi-base e rumore fisico per mappare sia i limiti quantistici che l'efficienza classica. |

## Istruzioni

### Requisiti

Il simulatore richiede un ambiente basato su **Python 3.10**. 

*Nota:* È necessario mantenere questa specifica versione

Versioni più recenti di Python non sono al momento pienamente supportate dai pacchetti di NetSquid utilizzati per questo progetto.

### Creazione dell'Ambiente (Conda)
Apri il terminale nella cartella principale del progetto ed esegui i seguenti comandi per creare un ambiente virtuale locale (nella cartella `.venv`):

```bash
conda create --prefix ./.venv python=3.10
conda activate ./.venv
```
(è importante che la versione di Python sia la 3.10 perché dalla 3.11 in poi alcune istruzioni hanno cambiato sintassi e quindi c'è il rischio che i vari programmi vadano in errore)

### Installazione di NetSquid
NetSquid non è disponibile sul PyPI pubblico standard, ma deve essere installato contattando direttamente il loro repository ufficiale.

L'accesso necessita delle credenziali utilizzate per la registrazione sul loro sito ufficiale.

Esegui questo comando sostituendo _username_ e _password_ con le tue credenziali:

```bash
pip install --extra-index-url 'https://<username>:<password>@pypi.netsquid.org' netsquid
```

*Attenzione*: Se la password contiene caratteri speciali, devi codificarli in formato URL-encoded (HTML) affinché il comando bash riesca ad interpretarli correttamente. Se ad esempio la password presenta il carattere '!', dovrai inserirlo come '%3F'

## Esecuzione
Una volta attivato l'ambiente e installate le dipendenze, puoi lanciare qualsiasi benchmark o calcolatore della suite passando il nome del file al comando python:

```bash
python entropy_calculator_without_error_correction.py
```
