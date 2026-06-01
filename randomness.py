from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile

_SIMULATOR = AerSimulator()

def generate_random_bit() -> int:
    """Genera un singolo bit casuale (usato solo se serve un bit isolato)."""
    return generate_sequence(1)[0]

def generate_sequence(n: int) -> list[int]:
    """Genera una sequenza di n bit casuali quantistici in una singola esecuzione."""

    if n < 0:
        return []
    
    # Creiamo un circuito con 'n' qubit e 'n' bit classici
    qc = QuantumCircuit(n, n)

    # Applichiamo l'Hadamard a tutti i qubit per metterli in sovrapposizione |+>
    qc.h(range(n))

    # Misuriamo tutti i qubit sui rispettivi bit classici
    qc.measure(range(n), range(n))

    # Compiliamo ed eseguiamo in un solo colpo (1 shot)
    qc_t = transpile(qc, _SIMULATOR)
    job = _SIMULATOR.run(qc_t, shots=1)

    # Il risultato è una stringa binaria
    bit_string = list(job.result().get_counts().keys())[0]

    # Convertiamo la stringa binaria in una lista di interi
    return [int(b) for b in bit_string]