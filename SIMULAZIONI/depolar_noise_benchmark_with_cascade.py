import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel
from netsquid.components.models.qerrormodels import DepolarNoiseModel
import random
from PROTOCOLLI.senderProtocol import SenderProtocol
from PROTOCOLLI.charlieProtocol import CharlieProtocol

# --- ALGORITMO CLASSICO (PARZIALE) DI CORREZIONE ERRORE ---

def cascade_correct_block(alice_blk, bob_blk):
    if sum(alice_blk) % 2 == sum(bob_blk) % 2:
        return bob_blk 
    
    if sum(alice_blk[:2]) % 2 != sum(bob_blk[:2]) % 2:
        if alice_blk[0] != bob_blk[0]:
            bob_blk[0] = 1 - bob_blk[0]
        else:
            bob_blk[1] = 1 - bob_blk[1]
    else:
        if alice_blk[2] != bob_blk[2]:
            bob_blk[2] = 1 - bob_blk[2]
        else:
            bob_blk[3] = 1 - bob_blk[3]
    return bob_blk

# --- ESECUZIONE DELLA SINGOLA SIMULAZIONE FISICA ---

def run_single_simulation(num_bits=15, noise_rate=0.0):
    ns.sim_reset()
    
    alice = Node("Alice", port_names=["port_out"])
    bob = Node("Bob", port_names=["port_out"])
    charlie = Node("Charlie", port_names=["port_in_a", "port_in_b"])
    
    # configurazione del rumore (0.0 = no caos, 0.5 = caos totale)
    noise_model = DepolarNoiseModel(depolar_rate=noise_rate, time_independent=True)
    
    # a chiave del dizionario deve essere "quantum_noise_model" per sfruttare il rumore
    channel_a = QuantumChannel("Channel_Alice_Charlie", delay=10, models={"quantum_noise_model": noise_model})
    channel_b = QuantumChannel("Channel_Bob_Charlie", delay=10, models={"quantum_noise_model": noise_model})
    
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
    
    ns.sim_run()
    
    # Post-processing classico
    alice_raw = proto_alice.raw_key
    bob_raw = []
    for i in range(num_bits):
        bob_bit = proto_bob.raw_key[i]
        parity = proto_charlie.announcements[i]
        bob_raw.append(1 - bob_bit if parity == 1 else bob_bit)
        
    # Tecniche di controllo: 3 qubit sacrificati per la stima, 12 mantenuti
    control_indices = sorted(random.sample(range(num_bits), 3))
    alice_sifted = [alice_raw[i] for i in range(num_bits) if i not in control_indices]
    bob_sifted = [bob_raw[i] for i in range(num_bits) if i not in control_indices]
    
    # Correzione dell'errore classica a blocchi
    bob_corrected = []
    for b in range(3):
        start_idx = b * 4
        end_idx = start_idx + 4
        alice_block = alice_sifted[start_idx:end_idx]
        bob_block = bob_sifted[start_idx:end_idx]
        corrected_bob_block = cascade_correct_block(alice_block, bob_block)
        bob_corrected.extend(corrected_bob_block)
        
    return alice_sifted == bob_corrected

# --- LOOP DI BENCHMARK REALISTICO ---
def run_performance_benchmark(iterations_per_step=100):
    print("=" * 70)
    print(f"AVVIO BENCHMARK QUANTISTICO REALISTICO ({iterations_per_step} test per step)")
    print("= Modello: DepolarNoiseModel (Nativo) | Canale: Matrice di Densità =")
    print("=" * 70)
    print(f"{'Prob. Depolarizzazione':<25}{'Successi':<15}{'Tasso di Successo (%)'}")
    print("-" * 70)
    
    # Generiamo probabilità reali da 0.0 a 0.45 (step di 0.03)
    noise_steps = [round(x * 0.05, 2) for x in range(21)]
    
    for noise in noise_steps:
        success_count = 0
        for _ in range(iterations_per_step):
            if run_single_simulation(num_bits=15, noise_rate=noise):
                success_count += 1
                
        success_rate = (success_count / iterations_per_step) * 100
        print(f"{noise:<25.2f}{success_count:<15}{success_rate:>5.1f}%")
        
    print("=" * 70)
    print("BENCHMARK FISICO COMPLETATO")
    print("=" * 70)

if __name__ == "__main__":
    run_performance_benchmark(iterations_per_step=100)