import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel
from netsquid.protocols import NodeProtocol
from netsquid.qubits import qubitapi as qapi
from randomness import generate_random_bit
import random

# --- DEFINIZIONE DEI PROTOCOLLI ---

class SenderProtocol(NodeProtocol):
    def __init__(self, node, port_name, num_bits, name="Sender"):
        super().__init__(node, name)
        self.port_name = port_name
        self.num_bits = num_bits
        self.raw_key = []

    def run(self):
        for i in range(self.num_bits):
            # 1. Scelta casuale del bit e salvataggio
            bit = generate_random_bit()
            self.raw_key.append(bit)
            
            # 2. Creazione del qubit
            qubit, = qapi.create_qubits(1)
            
            # 3. Codifica in fase corretta
            qapi.operate(qubit, ns.H)     # Prima portiamo in |+>
            if bit == 1:
                qapi.operate(qubit, ns.Z) # Se bit=1, invertiamo la fase: |+> -> |->
            
            # 4. Trasmissione a Charlie
            self.node.ports[self.port_name].tx_output(qubit)
            
            # 5. Pausa per separare gli eventi
            yield self.await_timer(10)

class CharlieProtocol(NodeProtocol):
    def __init__(self, node, port_a, port_b, num_bits, noise_probability=0.0, name="Charlie"):
        super().__init__(node, name)
        self.port_a = port_a
        self.port_b = port_b
        self.num_bits = num_bits
        self.noise_probability = noise_probability # Controllo manuale del rumore
        self.announcements = []

    def run(self):
        for i in range(self.num_bits):
            # 1. Aspetta i qubit
            yield self.await_port_input(self.node.ports[self.port_a]) & \
                  self.await_port_input(self.node.ports[self.port_b])
            
            msg_a = self.node.ports[self.port_a].rx_input()
            msg_b = self.node.ports[self.port_b].rx_input()
            
            qubit_a = msg_a.items[0]
            qubit_b = msg_b.items[0]
            
            # --- INIEZIONE MANUALE DEL RUMORE (Dephasing) ---
            # Se la probabilità è impostata, applichiamo una porta Z a sorpresa,
            # invertendo la fase del fotone prima della misurazione.
            if self.noise_probability > 0:
                if random.random() < self.noise_probability:
                    qapi.operate(qubit_a, ns.Z)
                if random.random() < self.noise_probability:
                    qapi.operate(qubit_b, ns.Z)
            
            # 2. Estrazione della parità di fase
            qapi.operate(qubit_a, ns.H)
            qapi.operate(qubit_b, ns.H)
            
            qapi.operate([qubit_a, qubit_b], ns.CX)
            
            res_parity, _ = qapi.measure(qubit_b)
            qapi.discard(qubit_a)
            
            self.announcements.append(res_parity)
            print(f"   -> [Charlie] Qubit {i+1}: Parità rilevata = {'Uguali (0)' if res_parity == 0 else 'Diversi (1)'}")

# --- SETUP E POST-PROCESSING ---

def setup_and_run_tfqkd(num_bits=15, noise_probability=0.0):
    ns.sim_reset()
    
    alice = Node("Alice", port_names=["port_out"])
    bob = Node("Bob", port_names=["port_out"])
    charlie = Node("Charlie", port_names=["port_in_a", "port_in_b"])
    
    # Canali fisici standard senza modelli esterni bloccanti
    channel_a = QuantumChannel("Channel_Alice_Charlie", delay=10)
    channel_b = QuantumChannel("Channel_Bob_Charlie", delay=10)
    
    alice.ports["port_out"].connect(channel_a.ports["send"])
    channel_a.ports["recv"].connect(charlie.ports["port_in_a"])
    
    bob.ports["port_out"].connect(channel_b.ports["send"])
    channel_b.ports["recv"].connect(charlie.ports["port_in_b"])
    
    proto_alice = SenderProtocol(alice, "port_out", num_bits=num_bits)
    proto_bob = SenderProtocol(bob, "port_out", num_bits=num_bits)
    
    # Passiamo la probabilità di rumore direttamente al setup di Charlie
    proto_charlie = CharlieProtocol(charlie, "port_in_a", "port_in_b", 
                                    num_bits=num_bits, noise_probability=noise_probability)
    
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
    SOGLIA_CRITICA_QBER = 11.0  # Soglia classica del 11%
    
    if qber == 0:
        print("\n✅ SUCCESSO PERFETTO: Le chiavi corrispondono al 100%!")
    elif qber <= SOGLIA_CRITICA_QBER:
        print(f"\n⚠️ WARNING: Ci sono errori ({qber:.2f}%), ma siamo sotto la soglia del {SOGLIA_CRITICA_QBER}%.")
        print("I bit errati possono essere corretti con algoritmi classici. Chiave SICURA.")
    else:
        print(f"\n❌ ERRORE CRITICO: QBER al {qber:.2f}% (Soglia superata!).")
        print("Troppo rumore o potenziale presenza di un intercettatore. Chiave SCARTATA.")

if __name__ == "__main__":
    # noise_probability=0.5 distrugge sistematicamente la stabilità della chiave (QBER ~ 50%).
    # Impostalo a 0.0 per farlo funzionare senza errori.
    setup_and_run_tfqkd(num_bits=15, noise_probability=0.01)