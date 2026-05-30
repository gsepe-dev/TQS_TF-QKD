from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile

def genera_bit_casuale() -> int:
    """
    Genera un bit casuale quantistico.
    - Preparazione: base standard (|0⟩)
    - Misura: base di Hadamard (applica H⁻¹ = H prima di misurare)
    """
    qr = QuantumRegister(1, 'q')
    cr = ClassicalRegister(1, 'c')
    qc = QuantumCircuit(qr, cr)

    # Passo 1 — preparazione in base standard: il qubit è già |0⟩, nessuna operazione
    # (se volessimo |1⟩ basterebbe un gate X qui)

    # Passo 2 — porta il qubit in sovrapposizione con H
    qc.h(qr[0])          # |0⟩ → |+⟩ = (|0⟩ + |1⟩) / √2

    # Passo 3 — misura nella base di Hadamard: applica H⁻¹ = H prima della misura
    qc.h(qr[0])          # ruota la base: |+⟩ → |0⟩, |−⟩ → |1⟩

    # Passo 4 — misura nella base computazionale (che ora corrisponde alla base H)
    qc.measure(qr[0], cr[0])

    # Simulazione
    sim = AerSimulator()
    qc_t = transpile(qc, sim)
    job = sim.run(qc_t, shots=1)
    result = job.result()
    counts = result.get_counts()

    bit = int(list(counts.keys())[0])
    return bit


def genera_sequenza(n: int) -> list[int]:
    """Genera una sequenza di n bit casuali quantistici."""
    return [genera_bit_casuale() for _ in range(n)]

print(genera_bit_casuale())
print(genera_sequenza(11))