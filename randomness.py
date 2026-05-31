from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile

def generate_random_bit() -> int:
    qr = QuantumRegister(1, 'q')
    cr = ClassicalRegister(1, 'c')
    qc = QuantumCircuit(qr, cr)


    qc.h(qr[0])          # |0⟩ → |+⟩
    qc.measure(qr[0], cr[0])   # collassa: 0 o 1 con p=0.5

    sim = AerSimulator() # non si tratta di vera casualità perché si usa un simulatore
    qc_t = transpile(qc, sim)
    job = sim.run(qc_t, shots=1)
    result = job.result()
    counts = result.get_counts()

    #qc.draw('mpl').savefig('circuit.png')

    random_bit = int(list(counts.keys())[0])
    return random_bit


def genera_sequenza(n: int) -> list[int]:
    """Genera una sequenza di n bit casuali quantistici."""
    return [generate_random_bit() for _ in range(n)]

#print(generate_random_bit())
#print(genera_sequenza(11))