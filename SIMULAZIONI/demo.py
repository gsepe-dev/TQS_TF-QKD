import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel
from senderProtocol import SenderProtocol
from charlieProtocol import CharlieProtocol

# --- SETUP E POST-PROCESSING ---

def setup_and_run_tfqkd(num_bits=15, noise_probability=0.0):
    ns.sim_reset()
    
    # creazione nodi coinvolti nella comunicazione
    alice = Node("Alice", port_names=["port_out"])
    bob = Node("Bob", port_names=["port_out"])
    charlie = Node("Charlie", port_names=["port_in_a", "port_in_b"])
    
    # creazione canali fisici standard
    channel_a = QuantumChannel("Channel_Alice_Charlie", delay=10)
    channel_b = QuantumChannel("Channel_Bob_Charlie", delay=10)
    
    alice.ports["port_out"].connect(channel_a.ports["send"])
    channel_a.ports["recv"].connect(charlie.ports["port_in_a"])
    
    bob.ports["port_out"].connect(channel_b.ports["send"])
    channel_b.ports["recv"].connect(charlie.ports["port_in_b"])
    
    proto_alice = SenderProtocol(alice, "port_out", num_bits=num_bits)
    proto_bob = SenderProtocol(bob, "port_out", num_bits=num_bits)
    
    proto_charlie = CharlieProtocol(charlie, "port_in_a", "port_in_b", num_bits=num_bits, noise_probability=noise_probability)
    
    # il metodo start crea un thread che esegue il codice contenuto nel metodo run della classe
    proto_alice.start()
    proto_bob.start()
    proto_charlie.start()
    
    print(f"--- Inizio Simulazione: Scambio di {num_bits} bit [Probabilità Rumore: {noise_probability * 100}%] ---")
    ns.sim_run()
    
    # --- RICONCILIAZIONE DELLA CHIAVE ---
    print("\n--- Riconciliazione Classica ---")
    alice_final_key = proto_alice.raw_key
    bob_final_key = []
    
    for i in range(num_bits):
        bob_bit = proto_bob.raw_key[i]
        parity = proto_charlie.announcements[i]
        
        if parity == 1:
            bob_final_key.append(1 - bob_bit)
        else:
            bob_final_key.append(bob_bit)
            
    print(f"Chiave Raw di Alice: {alice_final_key}")
    print(f"Chiave Raw di Bob:   {proto_bob.raw_key}")
    print(f"Annunci di Charlie:  {proto_charlie.announcements}")
    print("-" * 30)
    print(f"Chiave Finale Alice: {alice_final_key}")
    print(f"Chiave Finale Bob:   {bob_final_key}")
    
    errors = sum(1 for a, b in zip(alice_final_key, bob_final_key) if a != b)
    qber = (errors / num_bits) * 100
    print(f"QBER calcolato sulla chiave finale: {qber:.2f}%")

    # --- NUOVA VERIFICA DELLA SOGLIA DI SICUREZZA ---
    SOGLIA_CRITICA_QBER = 11.0  # Soglia classica dell'11%
    
    if qber == 0:
        print("\nSUCCESSO: Le chiavi corrispondono al 100%!")
    elif qber <= SOGLIA_CRITICA_QBER:
        print(f"\nWARNING: Ci sono errori ({qber:.2f}%), ma siamo sotto la soglia del {SOGLIA_CRITICA_QBER}%.")
        print("I bit errati possono essere corretti con algoritmi classici. Chiave SICURA.")
    else:
        print(f"\nERRORE: QBER al {qber:.2f}% (Soglia superata!).")
        print("Troppo rumore o potenziale presenza di un intercettatore. Chiave SCARTATA.")

if __name__ == "__main__":
    # noise_probability=0.5 distrugge sistematicamente la stabilità della chiave (QBER ~ 50%) in quanto è la confusione massima
    setup_and_run_tfqkd(num_bits=15, noise_probability=0.01)