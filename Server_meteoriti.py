import socket
import threading
import random
import time

# Configurazione del server
HOST = 'localhost'
PORT = 9999
M = 10  # Dimensione della griglia
n = 30  # Numero massimo di meteoriti

client_addrs = set()  # Set per tenere traccia degli indirizzi dei client
lock = threading.Lock()  # Lock per gestire l'accesso concorrente alle risorse condivise
meteoriti_posizioni = set()  # Set per tenere traccia delle posizioni dei meteoriti

def invia_meteoriti(socket_server):
    """
    Funzione che invia le posizioni dei meteoriti ai client connessi.
    """
    global meteoriti_posizioni
    while True:
        time.sleep(2)  # Attende 2 secondi tra ogni invio di meteoriti
        with lock:
            # Aggiunge nuovi meteoriti se non è stato raggiunto il numero massimo
            if len(meteoriti_posizioni) < n:
                for _ in range(2):  # Genera 2 meteoriti ogni 2 secondi
                    if len(meteoriti_posizioni) < n:
                        posizione_meteorite = (random.randint(0, M-1), random.randint(0, M-1))
                        meteoriti_posizioni.add(posizione_meteorite)

            # Calcola nuove posizioni per i meteoriti esistenti
            nuove_posizioni = set()
            for posizione in meteoriti_posizioni:
                nuova_posizione = (
                    max(0, min(M-1, posizione[0] + random.choice([-1, 0, 1]))),
                    max(0, min(M-1, posizione[1] + random.choice([-1, 0, 1])))
                )
                nuove_posizioni.add(nuova_posizione)
            meteoriti_posizioni = nuove_posizioni

            # Invia le nuove posizioni dei meteoriti a tutti i client connessi
            for addr in client_addrs:
                socket_server.sendto(b'clear', addr)  # Invia comando per pulire i meteoriti
                for posizione in meteoriti_posizioni:
                    socket_server.sendto(f'{posizione[0]},{posizione[1]}'.encode(), addr)
                    time.sleep(0.05)  # Aggiunge un piccolo ritardo per evitare pacchetti UDP troppo frequenti

def ricevi_client(socket_server):
    """
    Funzione che gestisce la ricezione dei comandi dai client.
    """
    global client_addrs
    while True:
        try:
            # Riceve dati dal client
            dati, addr = socket_server.recvfrom(1024)
            comando = dati.decode()
            
            if comando == 'start':
                # Aggiunge il client all'elenco dei client connessi
                with lock:
                    client_addrs.add(addr)
                socket_server.sendto(b'Benvenuto nel gioco!', addr)
            elif comando == 'stop':
                # Rimuove il client dall'elenco dei client connessi
                with lock:
                    client_addrs.remove(addr)
            elif comando == 'retry':
                # Pulisce le posizioni dei meteoriti per il retry del gioco
                with lock:
                    meteoriti_posizioni.clear()
        except socket.error as e:
            print(f"Errore durante la ricezione dei dati: {e}")
        except Exception as e:
            print(f"Errore sconosciuto: {e}")

def main():
    """
    Funzione principale che avvia il server.
    """
    # Configura il socket del server
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    print(f"Server in ascolto su {HOST}:{PORT}")

    # Avvia il thread per inviare i meteoriti
    threading.Thread(target=invia_meteoriti, args=(server,)).start()
    # Avvia la funzione per ricevere i client
    ricevi_client(server)

if __name__ == "__main__":
    main()
