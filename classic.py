import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel
from netsquid.protocols import NodeProtocol
from netsquid.qubits import qubitapi as qapi
from netsquid.components.models.qerrormodels import DephasingNoiseModel # Inietta Dephasing Noise
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
            bit = random.choice([0, 1])
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
    def __init__(self, node, port_a, port_b, num_bits, name="Charlie"):
        super().__init__(node, name)
        self.port_a = port_a
        self.port_b = port_b
        self.num_bits = num_bits
        self.announcements = [] # Lista per i messaggi classici (la parità)

    def run(self):
        for i in range(self.num_bits):
            # 1. Aspetta i qubit
            yield self.await_port_input(self.node.ports[self.port_a]) & \
                  self.await_port_input(self.node.ports[self.port_b])
            
            msg_a = self.node.ports[self.port_a].rx_input()
            msg_b = self.node.ports[self.port_b].rx_input()
            
            qubit_a = msg_a.items[0]
            qubit_b = msg_b.items[0]
            
            # 2. Estrazione della parità di fase
            # Riportiamo in base Z
            qapi.operate(qubit_a, ns.H)
            qapi.operate(qubit_b, ns.H)
            
            # Il CNOT "scrive" su qubit_b lo XOR tra i due bit (0 se uguali, 1 se diversi)
            qapi.operate([qubit_a, qubit_b], ns.CX)
            
            # Misuriamo SOLO la parità (qubit_b) e scartiamo qubit_a (cancellazione informazione)
            res_parity, _ = qapi.measure(qubit_b)
            qapi.discard(qubit_a)
            
            self.announcements.append(res_parity)
            print(f"   -> [Charlie] Qubit {i+1}: Parità rilevata = {'Uguali (0)' if res_parity == 0 else 'Diversi (1)'}")

# --- SETUP E POST-PROCESSING ---

def setup_and_run_tfqkd(num_bits=15):
    ns.sim_reset()
    
    alice = Node("Alice", port_names=["port_out"])
    bob = Node("Bob", port_names=["port_out"])
    charlie = Node("Charlie", port_names=["port_in_a", "port_in_b"])
    
    channel_a = QuantumChannel("Channel_Alice_Charlie", delay=10)
    channel_b = QuantumChannel("Channel_Bob_Charlie", delay=10)
    
    alice.ports["port_out"].connect(channel_a.ports["send"])
    channel_a.ports["recv"].connect(charlie.ports["port_in_a"])
    
    bob.ports["port_out"].connect(channel_b.ports["send"])
    channel_b.ports["recv"].connect(charlie.ports["port_in_b"])
    
    proto_alice = SenderProtocol(alice, "port_out", num_bits=num_bits)
    proto_bob = SenderProtocol(bob, "port_out", num_bits=num_bits)
    proto_charlie = CharlieProtocol(charlie, "port_in_a", "port_in_b", num_bits=num_bits)
    
    proto_alice.start()
    proto_bob.start()
    proto_charlie.start()
    
    print(f"--- Inizio Simulazione: Scambio di {num_bits} bit ---")
    ns.sim_run()
    
    # --- RICONCILIAZIONE DELLA CHIAVE ---
    print("\n--- Riconciliazione Classica ---")
    alice_final_key = proto_alice.raw_key
    bob_final_key = []
    
    for i in range(num_bits):
        bob_bit = proto_bob.raw_key[i]
        parity = proto_charlie.announcements[i]
        
        # Se Charlie dice che erano diversi (parità = 1), Bob inverte il suo bit
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
    
    # Verifica che le chiavi siano identiche
    if alice_final_key == bob_final_key:
        print("\n✅ SUCCESSO: Le chiavi corrispondono perfettamente!")
    else:
        print("\n❌ ERRORE: Le chiavi non corrispondono.")

if __name__ == "__main__":
    setup_and_run_tfqkd(num_bits=15)