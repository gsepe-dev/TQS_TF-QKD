import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel
import random
from PROTOCOLLI.senderProtocol import SenderProtocol
from PROTOCOLLI.charlieProtocol import CharlieProtocol

# --- ALGORITMO CLASSICO DI CORREZIONE ERRORE ---

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

# --- FUNZIONE DI SIMULAZIONE SINGOLA ---

def run_single_simulation(num_bits=15, noise_probability=0.0):
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
    proto_charlie = CharlieProtocol(charlie, "port_in_a", "port_in_b", num_bits=num_bits, noise_probability=noise_probability)
    
    proto_alice.start()
    proto_bob.start()
    proto_charlie.start()
    
    ns.sim_run()
    
    # Riconciliazione iniziale basata sui dati di Charlie
    alice_raw = proto_alice.raw_key
    bob_raw = []
    for i in range(num_bits):
        bob_bit = proto_bob.raw_key[i]
        parity = proto_charlie.announcements[i]
        bob_raw.append(1 - bob_bit if parity == 1 else bob_bit)
        
    # Parameter Estimation: Sacrifichiamo 3 bit casuali
    control_indices = sorted(random.sample(range(num_bits), 3))
    alice_sifted = [alice_raw[i] for i in range(num_bits) if i not in control_indices]
    bob_sifted = [bob_raw[i] for i in range(num_bits) if i not in control_indices]
    
    # Information Reconciliation: Correzione Cascade sui 3 blocchi da 4 bit
    bob_corrected = []
    for b in range(3):
        start_idx = b * 4
        end_idx = start_idx + 4
        alice_block = alice_sifted[start_idx:end_idx]
        bob_block = bob_sifted[start_idx:end_idx]
        corrected_bob_block = cascade_correct_block(alice_block, bob_block)
        bob_corrected.extend(corrected_bob_block)
        
    # Restituisce True se le chiavi finali da 12 bit coincidono al 100%
    return alice_sifted == bob_corrected

# --- BENCHMARK LOOP ---

def run_performance_benchmark(iterations_per_step=100):
    print("=" * 60)
    print(f"AVVIO BENCHMARK: {iterations_per_step} simulazioni per ogni livello di rumore")
    print("=" * 60)
    print(f"{'Noise Prob':<12}{'Successi':<12}{'Tasso di Successo':<18}")
    print("-" * 60)
    
    # Generiamo i valori di rumore da 0.00 a 1.00 con step di 0.05
    noise_steps = [round(x * 0.05, 2) for x in range(21)]
    
    results = []
    
    for noise in noise_steps:
        success_count = 0
        for _ in range(iterations_per_step):
            if run_single_simulation(num_bits=15, noise_probability=noise):
                success_count += 1
                
        success_rate = (success_count / iterations_per_step) * 100
        results.append((noise, success_rate))
        print(f"{noise:<12.2f}{success_count:<12}{success_rate:>5.1f}%")
        
    print("=" * 60)
    print("BENCHMARK COMPLETATO")
    print("=" * 60)

if __name__ == "__main__":
    run_performance_benchmark(iterations_per_step=100)