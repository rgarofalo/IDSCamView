# IDSCamView

Software per la visualizzazione del flusso video di una telecamera IDS uEye XC.

## Descrizione

IDSCamView è un'applicazione Windows che consente di visualizzare il flusso video proveniente da una telecamera IDS, offrendo strumenti di interazione quali:

- Visualizzazione live del flusso video
- Pan della vista
- Zoom
- Gestione della ROI (Region of Interest)
- Salvataggio e caricamento delle configurazioni

L'applicazione è progettata per essere richiamata da altri software della suite SpiderSuite e viene utilizzata come supporto alle operazioni di ispezione visiva durante i processi di biofabbricazione.

---

# Contesto

IDSCamView può essere utilizzato in diveri contesti in questo caso è stato pensato per: alcune fasi operative di produzione che necessitao di una supervisione visiva dell'area di lavoro senza compromettere l'ambiente sterile. IDSCamView permette all'operatore di osservare il processo attraverso la telecamera installata sul sistema.

---

# Funzionalità

## Visualizzazione

- Streaming video in tempo reale
- Gestione della ROI
- Pan
- Zoom

## Configurazione

- Caricamento configurazioni da file INI
- Creazione automatica di configurazioni di default
- Salvataggio delle impostazioni

## Interfaccia

L'interfaccia è composta da due aree principali:

- **Area di visualizzazione**
  - visualizza il flusso video

- **Area di controllo**
  - pan
  - zoom
  - salvataggio configurazioni
  - comandi futuri

---

# Requisiti software

- Windows 10 / Windows 11
- Python 3.10.x
- IDS Peak SDK 1.6.2.0

---

# Requisiti hardware

- PC Windows
- Display touchscreen
- Risoluzione 1080 × 1920 (verticale)
- Telecamera IDS U3-36L0XC-C collegata tramite USB

---

# Architettura

IDSCamView è progettato per essere un componente della suite SpiderSuite.

```
SmartPage
     │
     ▼
 IDSCamView
     │
     ▼
 IDS Camera
```

Le applicazioni comunicano principalmente tramite file di configurazione.

---

# Configurazione

Le impostazioni vengono salvate in un file **INI** posto nella stessa cartella dell'eseguibile.

Ogni sezione rappresenta una configurazione completa.

Esempio:

```ini
[Default]

ViewAreaCorners=...
CommandAreaCorners=...
ROI=...
```

---

# Avvio

All'avvio il software:

1. verifica la presenza della telecamera;
2. inizializza il driver IDS;
3. carica la configurazione;
4. in caso di errore crea una configurazione di default;
5. avvia la visualizzazione del flusso video.

---

# Requisiti funzionali

## Caricamento configurazione

**Input**

- percorso assoluto del file INI
- nome della configurazione

**Output**

Configurazione caricata in memoria.

---

## Ripristino configurazione

Se la configurazione non esiste o è corrotta:

- viene generata automaticamente una configurazione standard;
- viene salvata nella directory dell'applicazione.

---

# Requisiti non funzionali

Il software deve rispettare i seguenti vincoli:

- GUI frameless
- finestra Always On Top
- utilizzo della libreria Tkinter
- distribuzione come singolo eseguibile
- compilazione tramite Cython

---

# Vincoli

## Hardware

Supporto esclusivo alla telecamera:

- IDS U3-36L0XC-C

## Sistema operativo

- Windows 11 (o superiore)

## Comunicazione

- collegamento USB con la telecamera

---

# Struttura del progetto (indicativa)

```
IDSCamView/
│
├── config/
│   └── IDSCamView.ini
│
├── images/
│
├── src/
│
├── requirements.txt
│
└── README.md
```

---

# Evoluzioni previste

Sono previste le seguenti funzionalità:

- miglioramento automatico dell'immagine
- registrazione del flusso video
- acquisizione di immagini statiche
- visualizzazione dati di processo in overlay
- riproduzione sincronizzata di video e dati di processo

---

# Glossario

| Termine | Descrizione |
|----------|-------------|
| SmartPage | Software principale di controllo |
| ROI | Region of Interest |
| Tkinter | Libreria grafica Python |
| Cython | Compilatore Python → C |

---

# Licenza

Da definire.