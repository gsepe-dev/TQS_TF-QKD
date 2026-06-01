import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel
from netsquid.components.models.qerrormodels import DepolarNoiseModel
import math
from senderProtocol import SenderProtocolAdvanced
from charlieProtocol import CharlieProtocolAdvanced



# =====================================================================
# 2. ALGORITMI CLASSICI (CORREZIONE ED ENTROPIA)
# =====================================================================

def cascade_correct_block(alice_blk, bob_blk):
    """Algoritmo classico ricorsivo per la correzione degli errori (Bisezione)."""
    if sum(alice_blk) % 2 == sum(bob_blk) % 2:
        return bob_blk  # Parità identica, si assume nessun errore dispari
    if len(alice_blk) < 2:
        bob_blk[0] = 1 - bob_blk[0]  # Errore trovato e corretto
        return bob_blk
        
    mid = len(alice_blk) // 2
    if sum(alice_blk[:mid]) % 2 != sum(bob_blk[:mid]) % 2:
        bob_blk[:mid] = cascade_correct_block(alice_blk[:mid], bob_blk[:mid])
    else:
        bob_blk[mid:] = cascade_correct_block(alice_blk[mid:], bob_blk[mid:])
    return bob_blk

def binary_entropy(p):
    """Calcola l'entropia binaria di Shannon (necessaria per il calcolo dell'SKR)."""
    if p <= 0 or p >= 1:
        return 0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)

# =====================================================================
# 3. ENGINE DELLA SINGOLA SIMULAZIONE FISICA
# =====================================================================

def run_single_simulation(num_bits=25, noise_rate=0.0, block_size=4):
    ns.sim_reset()
    
    # Inizializzazione Rete e Modello di Rumore Termico
    alice, bob, charlie = Node("Alice", port_names=["port_out"]), Node("Bob", port_names=["port_out"]), Node("Charlie", port_names=["port_in_a", "port_in_b"])
    noise_model = DepolarNoiseModel(depolar_rate=noise_rate, time_independent=True)
    channel_a = QuantumChannel("Chan_A", delay=10, models={"quantum_noise_model": noise_model})
    channel_b = QuantumChannel("Chan_B", delay=10, models={"quantum_noise_model": noise_model})
    
    # Connessioni Hardware
    alice.ports["port_out"].connect(channel_a.ports["send"]); channel_a.ports["recv"].connect(charlie.ports["port_in_a"])
    bob.ports["port_out"].connect(channel_b.ports["send"]); channel_b.ports["recv"].connect(charlie.ports["port_in_b"])
    
    proto_alice = SenderProtocolAdvanced(alice, "port_out", num_bits=num_bits)
    proto_bob = SenderProtocolAdvanced(bob, "port_out", num_bits=num_bits)
    proto_charlie = CharlieProtocolAdvanced(charlie, "port_in_a", "port_in_b", num_bits=num_bits)
    
    # Avvio Simulazione Quantistica
    proto_alice.start(); proto_bob.start(); proto_charlie.start()
    ns.sim_run()
    
    # --- POST-PROCESSING CLASSICO (SIFTING) ---
    alice_raw, alice_bases, bob_bases = proto_alice.raw_key, proto_alice.bases, proto_bob.bases
    alice_sifted, bob_sifted = [], []
    
    for i in range(num_bits):
        if alice_bases[i] == bob_bases[i]:  # Conserva solo se le basi coincidono
            shared_basis = alice_bases[i]
            res_a, res_b = proto_charlie.announcements[i]
            
            # Logica di parità del BSM (Z-basis -> res_b | X-basis -> res_a)
            parity = res_b if shared_basis == 0 else res_a
            bob_bit = proto_bob.raw_key[i]
            bob_adjusted = 1 - bob_bit if parity == 1 else bob_bit
            
            alice_sifted.append(alice_raw[i])
            bob_sifted.append(bob_adjusted)
            
    if len(alice_sifted) == 0: return 0.0, 0.0, False
        
    # --- CALCOLO METRICHE (LEZIONE 2) ---
    errors = sum(1 for a, b in zip(alice_sifted, bob_sifted) if a != b)
    qber = errors / len(alice_sifted)
    skr = max(0, 1 - 2 * binary_entropy(qber))  # Secret Key Rate (Soglia ~11%)
    
    # --- CORREZIONE ERRORE (CASCADE) ---
    bob_corrected = []
    num_blocks = len(alice_sifted) // block_size
    for b in range(num_blocks):
        start = b * block_size
        end = start + block_size
        corrected_block = cascade_correct_block(alice_sifted[start:end], bob_sifted[start:end])
        bob_corrected.extend(corrected_block)
        
    # Verifica Finale
    alice_compared = alice_sifted[:len(bob_corrected)]
    success = (alice_compared == bob_corrected) if len(bob_corrected) > 0 else False
    
    return qber, skr, success

# =====================================================================
# 4. BENCHMARK COMPLETO (DOPPIO TEST)
# =====================================================================

def run_ultimate_benchmark(iterations_per_step=100):
    print("=" * 85)
    print(" AVVIO BENCHMARK QUANTISTICO COMPLETO (PROGETTO FASCIA ALTA)")
    print("=" * 85)

    # -----------------------------------------------------------------
    # TEST 1: Impatto del Rumore sulla Sicurezza (Limite Quantistico)
    # -----------------------------------------------------------------
    print("\n[ TEST 1: ANALISI QBER E SECRET KEY RATE (SOGLIA CRITICA 11%) ]")
    print("Obiettivo: Mappare l'orizzonte di sicurezza al variare del rumore del canale.")
    print(f"{'Prob. Rumore':<15}{'QBER Medio (%)':<18}{'SKR Teorico':<15}{'Successo Cascade'}")
    print("-" * 85)
    
    noise_steps = [round(x * 0.03, 2) for x in range(11)]  # Da 0.0 a 0.30
    for noise in noise_steps:
        t_qber, success_c = 0, 0
        for _ in range(iterations_per_step):
            qber, _, success = run_single_simulation(num_bits=25, noise_rate=noise, block_size=4)
            t_qber += qber
            if success: success_c += 1
                
        # Calcolo l'SKR sul QBER medio globale alla fine del ciclo
        avg_qber = t_qber / iterations_per_step
        skr_teorico = max(0, 1 - 2 * binary_entropy(avg_qber))
        
        print(f"{noise:<15.2f}{avg_qber*100:<17.1f}% {skr_teorico:<14.4f}{(success_c/iterations_per_step)*100:>5.1f}%")

    # -----------------------------------------------------------------
    # TEST 2: Ottimizzazione Cascade (Limite Classico)
    # -----------------------------------------------------------------
    print("\n" + "=" * 85)
    print("\n[ TEST 2: IMPATTO DELLA DIMENSIONE DEL BLOCCO CLASSICO CASCADE ]")
    print("Obiettivo: Trovare l'efficienza ottimale dell'algoritmo con un rumore fisso (6%).")
    print(f"{'Block Size':<15}{'QBER Medio (%)':<18}{'SKR Teorico':<15}{'Successo Cascade'}")
    print("-" * 85)
    
    blocks = [2, 4, 8, 16]
    fixed_noise = 0.06
    for b_size in blocks:
        t_qber, success_c = 0, 0
        for _ in range(iterations_per_step):
            qber, _, success = run_single_simulation(num_bits=25, noise_rate=fixed_noise, block_size=b_size)
            t_qber += qber
            if success: success_c += 1
                
        # Calcolo l'SKR sul QBER medio globale alla fine del ciclo
        avg_qber = t_qber / iterations_per_step
        skr_teorico = max(0, 1 - 2 * binary_entropy(avg_qber))
        
        print(f"{b_size:<15}{avg_qber*100:<17.1f}% {skr_teorico:<14.4f}{(success_c/iterations_per_step)*100:>5.1f}%")

    print("\n" + "=" * 85)
    print(" BENCHMARK COMPLETO TERMINATO")
    print("=" * 85)

if __name__ == "__main__":
    run_ultimate_benchmark(iterations_per_step=100)