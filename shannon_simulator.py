import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.protocols import NodeProtocol
from netsquid.qubits import qubitapi as qapi
import random
import math

# =====================================================================
# 1. PROTOCOLLI QUANTISTICI (FISICA DEI NODI E BSM)
# =====================================================================

class SenderProtocol(NodeProtocol):
    """Protocollo per Alice e Bob: Generazione qubit con basi casuali."""
    def __init__(self, node, port_name, num_bits, name="Sender"):
        super().__init__(node, name)
        self.port_name = port_name
        self.num_bits = num_bits
        self.raw_key = []
        self.bases = []  # 0 = Base Z (Computazionale), 1 = Base X (Fase)

    def run(self):
        for i in range(self.num_bits):
            bit = random.choice([0, 1])
            basis = random.choice([0, 1])
            self.raw_key.append(bit)
            self.bases.append(basis)
            
            qubit, = qapi.create_qubits(1)
            
            if basis == 0:  
                if bit == 1: qapi.operate(qubit, ns.X)
            else:  
                if bit == 1: qapi.operate(qubit, ns.X)
                qapi.operate(qubit, ns.H)
                
            self.node.ports[self.port_name].tx_output(qubit)
            yield self.await_timer(10)


class CharlieProtocol(NodeProtocol):
    """Protocollo per Charlie: Bell State Measurement (BSM) simmetrico."""
    def __init__(self, node, port_a, port_b, num_bits, name="Charlie"):
        super().__init__(node, name)
        self.port_a = port_a
        self.port_b = port_b
        self.num_bits = num_bits
        self.announcements = []

    def run(self):
        for i in range(self.num_bits):
            yield self.await_port_input(self.node.ports[self.port_a]) & \
                  self.await_port_input(self.node.ports[self.port_b])
            
            qubit_a = self.node.ports[self.port_a].rx_input().items[0]
            qubit_b = self.node.ports[self.port_b].rx_input().items[0]
            
            # BSM: CNOT (A controllo, B target) seguito da Hadamard su A
            qapi.operate([qubit_a, qubit_b], ns.CX)
            qapi.operate(qubit_a, ns.H)
            
            res_a, _ = qapi.measure(qubit_a)
            res_b, _ = qapi.measure(qubit_b)
            
            self.announcements.append((res_a, res_b))

# =====================================================================
# 2. METRICHE DI SICUREZZA (TEORIA DELL'INFORMAZIONE)
# =====================================================================

def binary_entropy(p):
    """Calcola l'entropia binaria di Shannon (necessaria per il calcolo dell'SKR)."""
    if p <= 0 or p >= 1:
        return 0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)

# =====================================================================
# 3. ENGINE DELLA SINGOLA SIMULAZIONE FISICA
# =====================================================================

def run_single_simulation(num_bits=200, noise_rate=0.0):
    ns.sim_reset()
    
    # Inizializzazione Rete
    alice, bob, charlie = Node("Alice", port_names=["port_out"]), Node("Bob", port_names=["port_out"]), Node("Charlie", port_names=["port_in_a", "port_in_b"])
    noise_model = DepolarNoiseModel(depolar_rate=noise_rate, time_independent=True)
    channel_a = QuantumChannel("Chan_A", delay=10, models={"quantum_noise_model": noise_model})
    channel_b = QuantumChannel("Chan_B", delay=10, models={"quantum_noise_model": noise_model})
    
    # Connessioni
    alice.ports["port_out"].connect(channel_a.ports["send"]); channel_a.ports["recv"].connect(charlie.ports["port_in_a"])
    bob.ports["port_out"].connect(channel_b.ports["send"]); channel_b.ports["recv"].connect(charlie.ports["port_in_b"])
    
    proto_alice = SenderProtocol(alice, "port_out", num_bits=num_bits)
    proto_bob = SenderProtocol(bob, "port_out", num_bits=num_bits)
    proto_charlie = CharlieProtocol(charlie, "port_in_a", "port_in_b", num_bits=num_bits)
    
    # Avvio Simulazione
    proto_alice.start(); proto_bob.start(); proto_charlie.start()
    ns.sim_run()
    
    # --- SIFTING CLASSICO ---
    alice_raw, alice_bases, bob_bases = proto_alice.raw_key, proto_alice.bases, proto_bob.bases
    alice_sifted, bob_sifted = [], []
    
    for i in range(num_bits):
        if alice_bases[i] == bob_bases[i]:  # Conserva solo se le basi coincidono
            shared_basis = alice_bases[i]
            res_a, res_b = proto_charlie.announcements[i]
            
            parity = res_b if shared_basis == 0 else res_a
            bob_bit = proto_bob.raw_key[i]
            bob_adjusted = 1 - bob_bit if parity == 1 else bob_bit
            
            alice_sifted.append(alice_raw[i])
            bob_sifted.append(bob_adjusted)
            
    if len(alice_sifted) == 0: return 0.0, 0.0
        
    # --- CALCOLO METRICHE (QBER E SKR) ---
    errors = sum(1 for a, b in zip(alice_sifted, bob_sifted) if a != b)
    qber = errors / len(alice_sifted)
    skr = max(0, 1 - 2 * binary_entropy(qber))
    
    return qber, skr

# =====================================================================
# 4. BENCHMARK DEL CANALE QUANTISTICO
# =====================================================================

def run_physical_benchmark(iterations_per_step=100):
    print("=" * 70)
    print(" AVVIO BENCHMARK QUANTISTICO (ANALISI FISICA E METRICHE)")
    print("=" * 70)
    print("Obiettivo: Dimostrare il limite di Shannon (Soglia QBER ~11%).")
    print(f"{'Prob. Rumore':<20}{'QBER Medio (%)':<20}{'SKR Teorico':<15}")
    print("-" * 70)
    
    noise_steps = [round(x * 0.03, 2) for x in range(11)]  # Da 0.0 a 0.30
    
    for noise in noise_steps:
        t_qber, t_skr = 0, 0
        for _ in range(iterations_per_step):
            qber, skr = run_single_simulation(num_bits=200, noise_rate=noise)
            t_qber += qber; t_skr += skr
                
        print(f"{noise:<20.2f}{(t_qber/iterations_per_step)*100:<20.1f}{t_skr/iterations_per_step:<15.4f}")

    print("=" * 70)

if __name__ == "__main__":
    run_physical_benchmark(iterations_per_step=100)