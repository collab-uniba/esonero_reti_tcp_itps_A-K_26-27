# Esonero TCP - Corso di Reti di Calcolatori - ITPS A-K 2026-27

Repository per l'assegnazione della prima prova di esonero: client-server TCP.


## Descrizione

Questo repository contiene la struttura base per lo sviluppo di un'applicazione client-server TCP in linguaggio C, utilizzando l'API socket (BSD socket su Linux e macOS, Winsock su Windows). Il codice è progettato per essere portabile su sistemi operativi **Windows**, **Linux** e **macOS**.

## Struttura del Repository

Il repository è organizzato in due progetti Eclipse CDT separati, più la cartella della verifica automatica:

```
.
├── .github/                # Verifica automatica (GitHub Actions), non modificare
│
├── client-project/         # Progetto Eclipse per il client
│   ├── .project            # Configurazione progetto Eclipse
│   ├── .cproject           # Configurazione Eclipse CDT
│   └── src/
│       ├── main.c          # File principale del client
│       └── protocol.h      # Header con definizioni e prototipi
│
└── server-project/         # Progetto Eclipse per il server
    ├── .project            # Configurazione progetto Eclipse
    ├── .cproject           # Configurazione Eclipse CDT
    └── src/
        ├── main.c          # File principale del server
        └── protocol.h      # Header con definizioni e prototipi
```

## Come Utilizzare il Repository

### 1. Creare la propria copia del repository

1. Cliccare su "Use this template" in alto a destra su GitHub
2. Creare un nuovo repository personale (nome a scelta) con visibilità **Private**
3. In _Settings → Collaborators → Add people_ aggiungere l'utente `correttore-lab-reti`: senza questo passo la correzione non può clonare il repository
4. Clonare il repository sul proprio computer:
   ```bash
   git clone <url-del-tuo-repository>
   ```

### 2. Importare i progetti in Eclipse

1. Aprire **Eclipse CDT**
2. Selezionare `File → Import → General → Existing Projects into Workspace`
3. In **Select root directory** scegliere la cartella del repository clonato: compaiono `client-project` e `server-project`, selezionarli entrambi
4. Lasciare **deselezionata** l'opzione **Copy projects into workspace**, altrimenti le modifiche non finiscono nel repository Git
5. Cliccare `Finish`

### 3. Configurare il progetto in Eclipse

Dopo aver importato i progetti, è necessario verificare e configurare le impostazioni del compilatore:

#### Verificare la toolchain
Per ciascun progetto (client e server):
1. Click destro sul progetto → `Properties`
2. Andare in `C/C++ Build → Tool Chain Editor`
3. Verificare che il **Current toolchain** sia corretto per il proprio sistema operativo:
   - **Linux**: Linux GCC
   - **macOS**: MacOSX GCC (richiede gli Xcode Command Line Tools: `xcode-select --install`)
   - **Windows**: MinGW GCC (richiede MinGW-w64 già installato)

#### Solo per Windows: Aggiungere libreria Winsock
Per compilare su Windows, è necessario linkare la libreria Winsock. Per ciascun progetto (client e server):
1. Click destro sul progetto → `Properties`
2. Andare in `C/C++ Build → Settings` e, in alto, scegliere **Configuration: [All configurations]**
3. Selezionare `MinGW C Linker → Libraries`
4. In **Libraries (-l)**, cliccare su `Add` e inserire: `ws2_32`
5. Applicare le modifiche e cliccare `OK`


## File Principali

### protocol.h
È identico nei due progetti e contiene:
- **Definizioni del protocollo** (già fornite, **non modificare**): strutture dei messaggi, codici di stato, costanti condivise
- **Prototipi delle funzioni**: inserire qui le firme delle funzioni implementate

### main.c (Client e Server)
Contiene:
- **Codice boilerplate** per la portabilità cross-platform
- **Inizializzazione Winsock** su Windows
- **Sezioni TODO** dove implementare la logica dell'applicazione
- Solo nel server: la disabilitazione del buffering di `stdout` (`setvbuf`), che garantisce la stampa immediata del log; non rimuoverla

### Eseguire client e server da terminale
Eclipse compila gli eseguibili nella cartella `Debug/` di ciascun progetto. Per aprire un terminale direttamente in quella cartella:
1. In **Project Explorer**, espandere il progetto e poi **Binaries**
2. Click destro sull'eseguibile → `Show in Local Terminal → Terminal`

Ripetere per l'altro progetto, in modo da avere un terminale per il server e uno per il client. Avviare prima il server, poi il client con gli argomenti previsti dall'assegnazione:

**Linux e macOS**
```bash
./server-project
./client-project <argomenti>
```

**Windows**
```
.\server-project.exe
.\client-project.exe <argomenti>
```

Il server resta in esecuzione finché non viene interrotto con `Ctrl+C`.

## Specifiche dell'Assegnazione

[Protocollo applicativo e istruzioni per la consegna](Assegnazione.md)

## Verifica Automatica

A ogni `git push`, GitHub compila client e server su **Windows, Linux e macOS** e li verifica con alcuni esempi presi dall'assegnazione.

- L'esito compare nella scheda **Actions** del vostro repository e accanto a ogni commit (✅ superato, ❌ fallito).
- In caso di fallimento, aprite l'esecuzione e consultate la pagina **Summary**: per ogni verifica fallita è indicato cosa era atteso e cosa è stato ricevuto.
- La verifica automatica serve a intercettare subito gli errori evidenti (codice che non compila su un sistema operativo, formato di output errato, byte order). **Superarla non garantisce** il superamento della correzione finale, che usa ulteriori casi di test.
- Non modificate la cartella `.github/`.
- Non serve alcuna configurazione: la verifica si attiva da sola nel repository creato con "Use this template".
- **È normale che le prime esecuzioni falliscano** (e che GitHub vi invii un'email di notifica) finché client e server non sono implementati.
- Se la scheda **Actions** mostra che i workflow sono disabilitati (ad es. perché avete creato un fork invece di usare il template), abilitateli da lì oppure da _Settings → Actions → General → Allow all actions and reusable workflows_.

## Salvare e Caricare le Modifiche su GitHub

Durante lo sviluppo in Eclipse, salvate regolarmente le modifiche sul repository GitHub utilizzando Git da riga di comando.

### Configurazione iniziale di Git (una volta sola)

Senza nome ed email Git rifiuta il primo commit. Senza la strategia di merge, `git pull` si ferma con l'errore "Need to specify how to reconcile divergent branches" quando il repository contiene commit del compagno di coppia che non avete in locale.
```bash
git config --global user.name "Nome Cognome"
git config --global user.email "email"
git config --global pull.rebase false
```

**Credenziali**: il repository è privato, quindi `git clone` e `git push` chiedono di autenticarsi. GitHub non accetta la password dell'account:
- **Windows**: Git for Windows include Git Credential Manager, che apre il browser per il login
- **macOS e Linux**: creare un [Personal Access Token](https://github.com/settings/tokens) (classic, con scope `repo`) e incollarlo quando Git chiede la password, oppure installare [Git Credential Manager](https://github.com/git-ecosystem/git-credential-manager)

### Workflow Git Completo

1. **Sincronizzare con il repository remoto**

   Prima di iniziare a lavorare, scaricare eventuali modifiche fatte da altri collaboratori sul repository condiviso:
   ```bash
   git pull
   ```

   Questo comando scarica e integra le modifiche dal repository remoto. È particolarmente importante quando si lavora in coppia o si lavora da computer diversi.

2. **Verificare lo stato del repository**

   Aprire un terminale nella directory del progetto e controllare quali file sono stati modificati o creati:
   ```bash
   git status
   ```

   Questo comando mostra:
   - File modificati (in rosso se non ancora aggiunti)
   - Nuovi file non tracciati
   - File pronti per il commit (in verde)

3. **Aggiungere file alla staging area**

   La staging area (area di preparazione) è uno spazio intermedio dove si selezionano le modifiche da includere nel prossimo commit.

   Per aggiungere **tutti** i file modificati e i nuovi file:
   ```bash
   git add .
   ```

   Oppure, per aggiungere **file specifici**:
   ```bash
   git add client-project/src/main.c
   git add server-project/src/main.c
   git add client-project/src/protocol.h
   ```

4. **Committare le modifiche**

   Dopo aver aggiunto i file alla staging area, creare un commit con un messaggio descrittivo:
   ```bash
   git commit -m "Implementazione logica client-server TCP"
   ```

   Il messaggio del commit dovrebbe descrivere brevemente le modifiche apportate. Altri esempi:
   ```bash
   git commit -m "Aggiunta funzione di gestione connessioni"
   git commit -m "Implementazione protocollo comunicazione"
   git commit -m "Fix gestione errori socket"
   ```

5. **Pushare le modifiche su GitHub**

   Infine, caricare i commit sul repository remoto:
   ```bash
   git push
   ```

### Esempio Pratico Completo

Ecco un esempio del flusso completo dopo aver modificato i file in Eclipse:

```bash
# 1. Sincronizzare con il repository remoto
git pull

# 2. Controllare lo stato
git status

# 3. Aggiungere tutti i file modificati
git add .

# 4. Verificare che i file siano nella staging area
git status

# 5. Creare il commit
git commit -m "Completamento implementazione client e server"

# 6. Caricare su GitHub
git push
```

### Suggerimenti

- **Sincronizzare prima di lavorare**: Fate sempre `git pull` prima di iniziare a modificare i file, specialmente se lavorate in coppia o da computer diversi. Questo riduce il rischio di conflitti.
- **Committare frequentemente**: Non aspettate di completare tutto il progetto. Fate commit incrementali ogni volta che completate una funzionalità o risolvete un problema.
- **Messaggi descrittivi**: Usate messaggi di commit chiari che descrivano cosa avete fatto, non come lo avete fatto.
- **Controllare sempre**: Usate `git status` prima e dopo `git add` per verificare quali file state per committare.
- **Push regolari**: Fate push regolarmente su GitHub per avere un backup del vostro lavoro e per condividere le modifiche con il vostro compagno di coppia.

### In Caso di Problemi

Se `git push` viene rifiutato perché il repository remoto contiene modifiche che non avete in locale (ad es. del compagno di coppia):
```bash
# Scaricare le ultime modifiche dal repository
git pull

# Risolvere eventuali conflitti manualmente
# Poi aggiungere i file risolti e committare
git add .
git commit -m "Risoluzione conflitti"
git push
```

Se dopo `git pull` si apre un editor con il messaggio "Merge branch 'main' …", il merge è andato a buon fine e va solo confermato: in vim scrivere `:wq` e premere Invio; in nano premere `Ctrl+O`, Invio, `Ctrl+X`.

## Licenza

Vedere il file [LICENSE](LICENSE) per i dettagli.
