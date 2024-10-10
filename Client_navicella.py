import socket
import threading
import tkinter as tk
from PIL import Image, ImageTk

# Configurazione della connessione al server
HOST = 'localhost'
PORT = 9999
M = 10  # Dimensione della griglia
meteoriti_posizioni = {}  # Dizionario per tenere traccia delle posizioni dei meteoriti
score = 0  # Punteggio corrente
highscore = 0  # Punteggio più alto raggiunto
game_over = False  # Stato del gioco (True se il gioco è finito)
timer = None  # Timer per l'aggiornamento del punteggio

def ricevi_meteoriti(socket_client, posizione_navicella, canvas, meteorite_img, info_label):
    """
    Funzione che riceve la posizione dei meteoriti dal server e aggiorna la griglia.
    """
    global meteoriti_posizioni, game_over
    client_running = True  # Variabile per mantenere il ciclo di ricezione attivo
    while client_running:
        try:
            # Ricezione dati dal server
            dati, _ = socket_client.recvfrom(1024)
            message = dati.decode()
            
            if message == 'clear':
                # Se il server invia 'clear', rimuove tutti i meteoriti dalla griglia
                canvas.delete('meteorite')
                meteoriti_posizioni.clear()
            elif ',' in message:
                # Gestione della posizione del meteorite
                posizione_meteorite = tuple(map(int, message.split(',')))
                meteoriti_posizioni[posizione_meteorite] = posizione_meteorite
                disegna_meteorite(canvas, posizione_meteorite, meteorite_img)

                # Controllo collisione tra navicella e meteorite
                if posizione_meteorite == tuple(posizione_navicella):
                    game_over = True
                    client_running = False
                    canvas.create_text(150, 150, text="GAME OVER", font=("Helvetica", 30), fill="red")
                    return
            else:
                print(message)  # Debug per messaggi di benvenuto o altri messaggi del server
            aggiorna_info(info_label)
        except SyntaxError as e:
            print(f"Errore di sintassi durante la ricezione dei dati: {e}")
        except socket.error as e:
            print(f"Errore durante la ricezione dei dati: {e}")
        except ValueError as e:
            print(f"Errore nel parsing dei dati ricevuti: {e}")
        except Exception as e:
            print(f"Errore sconosciuto: {e}")

def aggiorna_punteggio(info_label):
    """
    Aggiorna il punteggio del giocatore ogni secondo.
    """
    global score, highscore, game_over, timer
    if not game_over:
        score += 1  # Incrementa il punteggio
        if score > highscore:
            highscore = score  # Aggiorna l'highscore se il punteggio corrente è maggiore
        aggiorna_info(info_label)
        # Imposta un timer per aggiornare il punteggio ogni secondo
        timer = info_label.after(1000, lambda: aggiorna_punteggio(info_label))

def invia_comando(comando, socket_client):
    """
    Invia un comando al server.
    """
    try:
        socket_client.sendto(comando.encode(), (HOST, PORT))
    except socket.error as e:
        print(f"Errore durante l'invio del comando: {e}")

def disegna_navicella(canvas, posizione_attuale, nuova_posizione, navicella_img):
    """
    Disegna la navicella sulla griglia.
    """
    # Rimuove la navicella dalla posizione attuale
    canvas.delete('navicella')
    # Disegna la navicella nella nuova posizione
    canvas.create_image(nuova_posizione[0] * 30 + 15, nuova_posizione[1] * 30 + 15, image=navicella_img, anchor=tk.CENTER, tags='navicella')

def disegna_meteorite(canvas, posizione_meteorite, meteorite_img):
    """
    Disegna un meteorite sulla griglia.
    """
    x, y = posizione_meteorite
    # Disegna il meteorite nella posizione specificata
    canvas.create_image(x * 30 + 15, y * 30 + 15, image=meteorite_img, anchor=tk.CENTER, tags='meteorite')

def disegna_griglia(canvas, M):
    """
    Disegna la griglia di gioco.
    """
    for i in range(M):
        for j in range(M):
            # Disegna un rettangolo per ogni cella della griglia
            canvas.create_rectangle(i * 30, j * 30, i * 30 + 30, j * 30 + 30, outline="gray")

def muovi_navicella(event, socket_client, posizione_navicella, canvas, M, navicella_img, info_label):
    """
    Gestisce il movimento della navicella in risposta agli input da tastiera.
    """
    global game_over
    if game_over:
        return  # Non fare nulla se il gioco è finito

    x, y = posizione_navicella
    # Determina la nuova posizione in base alla direzione del tasto premuto
    if event.keysym == 'Up' and y > 0:
        nuova_posizione = (x, y - 1)
    elif event.keysym == 'Down' and y < M-1:
        nuova_posizione = (x, y + 1)
    elif event.keysym == 'Left' and x > 0:
        nuova_posizione = (x - 1, y)
    elif event.keysym == 'Right' and x < M-1:
        nuova_posizione = (x + 1, y)
    else:
        nuova_posizione = (x, y)

    disegna_navicella(canvas, (x, y), nuova_posizione, navicella_img)
    posizione_navicella[0], posizione_navicella[1] = nuova_posizione

    # Controllo collisione tra navicella e meteorite
    if tuple(nuova_posizione) in meteoriti_posizioni:
        game_over = True
        canvas.create_text(150, 150, text="GAME OVER", font=("Helvetica", 30), fill="red")
        return

    # Invia la nuova posizione della navicella al server
    invia_comando(f'{nuova_posizione[0]},{nuova_posizione[1]}', socket_client)

def retry_gioco(socket_client, canvas, posizione_navicella, navicella_img, meteorite_img, info_label):
    """
    Riavvia il gioco resettando tutte le variabili e la griglia.
    """
    global score, game_over, meteoriti_posizioni, timer
    game_over = True
    meteoriti_posizioni.clear()
    canvas.delete("all")  # Cancella tutti gli elementi dal canvas
    disegna_griglia(canvas, M)  # Ridisegna la griglia
    posizione_navicella[0], posizione_navicella[1] = M//2, M//2  # Riposiziona la navicella al centro
    disegna_navicella(canvas, posizione_navicella, posizione_navicella, navicella_img)
    invia_comando('retry', socket_client)  # Invia il comando di retry al server
    score = 0
    game_over = False
    aggiorna_info(info_label)
    if timer is not None:
        info_label.after_cancel(timer)
    aggiorna_punteggio(info_label)  # Ricomincia l'aggiornamento del punteggio
    threading.Thread(target=ricevi_meteoriti, args=(socket_client, posizione_navicella, canvas, meteorite_img, info_label)).start()

def aggiorna_info(info_label):
    """
    Aggiorna l'etichetta con il punteggio corrente e l'highscore.
    """
    global score, highscore
    info_label.config(text=f"Punteggio: {score}\nHighscore: {highscore}")

def avvia_gioco(M):
    """
    Inizializza l'interfaccia grafica del gioco e gestisce l'avvio.
    """
    global timer
    root = tk.Tk()
    root.title("Gioco Navicella")

    frame = tk.Frame(root)
    frame.pack()

    # Etichetta informativa a sinistra
    info_label_sx = tk.Label(frame, text="Regole:\nEvita i meteoriti!\n\nComandi:\nFreccia su: Muovi su\nFreccia giù: Muovi giù\nFreccia sinistra: Muovi sinistra\nFreccia destra: Muovi destra", font=("Courier", 12), justify=tk.LEFT, anchor="w", fg="black")
    info_label_sx.grid(row=0, column=0, padx=10, pady=10)

    # Canvas per la griglia di gioco
    canvas = tk.Canvas(frame, width=30*M, height=30*M, bg="white")
    canvas.grid(row=0, column=1, padx=10, pady=10)

    # Etichetta informativa a destra
    info_label_dx = tk.Label(frame, text="", font=("Courier", 12), justify=tk.LEFT, anchor="w")
    info_label_dx.grid(row=0, column=2, padx=10, pady=10)

    disegna_griglia(canvas, M)  # Disegna la griglia

    posizione_navicella = [M//2, M//2]  # Posizione iniziale della navicella

    # Caricamento delle immagini
    navicella_img = Image.open("navicella.png")
    navicella_img = navicella_img.resize((45, 45), Image.Resampling.LANCZOS)
    navicella_img = ImageTk.PhotoImage(navicella_img)

    meteorite_img = Image.open("meteorite.png")
    meteorite_img = meteorite_img.resize((30, 30), Image.Resampling.LANCZOS)
    meteorite_img = ImageTk.PhotoImage(meteorite_img)

    disegna_navicella(canvas, posizione_navicella, posizione_navicella, navicella_img)  # Disegna la navicella iniziale

    # Configurazione del socket client
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_client.sendto(b'start', (HOST, PORT))

    # Thread per ricevere i meteoriti dal server
    threading.Thread(target=ricevi_meteoriti, args=(socket_client, posizione_navicella, canvas, meteorite_img, info_label_dx)).start()

    # Bind dei tasti freccia per il movimento della navicella
    root.bind('<KeyPress>', lambda event: muovi_navicella(event, socket_client, posizione_navicella, canvas, M, navicella_img, info_label_dx))

    # Bottone per il retry del gioco
    retry_button = tk.Button(frame, text="Retry", command=lambda: retry_gioco(socket_client, canvas, posizione_navicella, navicella_img, meteorite_img, info_label_dx))
    retry_button.grid(row=1, column=1, pady=10)

    aggiorna_punteggio(info_label_dx)  # Inizia ad aggiornare il punteggio
    aggiorna_info(info_label_dx)  # Aggiorna l'etichetta con le informazioni iniziali

    root.mainloop()  # Avvia il loop principale dell'interfaccia grafica

if __name__ == "__main__":
    avvia_gioco(M)
