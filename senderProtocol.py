import netsquid as ns
from netsquid.protocols import NodeProtocol
from netsquid.qubits import qubitapi as qapi
from randomness import generate_random_bit


class SenderProtocol(NodeProtocol):
    """Protocollo per Alice e Bob: Generazione qubit con basi casuali."""
    def __init__(self, node, port_name, num_bits, name="Sender"):
        super().__init__(node, name)
        self.port_name = port_name
        self.num_bits = num_bits
        self.raw_key = []

    # usato in demo custom_noise e performance
    def run(self):
        for i in range(self.num_bits):
            # si sceglie un bit unif. a caso e lo si associa ad un qubit
            bit = generate_random_bit()
            self.raw_key.append(bit)
            
            # creazione qubit (per default si troverà nello stato |0>)
            qubit, = qapi.create_qubits(1)
            
            qapi.operate(qubit, ns.H)
            if bit == 1:
                qapi.operate(qubit, ns.Z) # Se bit=1, invertiamo la fase: |+> -> |->
            
            self.node.ports[self.port_name].tx_output(qubit)
            
            yield self.await_timer(10)


class SenderProtocolAdvanced(NodeProtocol):
    """Protocollo per Alice e Bob: Generazione qubit con basi casuali."""
    def __init__(self, node, port_name, num_bits, name="Sender"):
        super().__init__(node, name)
        self.port_name = port_name
        self.num_bits = num_bits
        self.raw_key = []
        self.bases = []  # 0 = Base Z (Computazionale), 1 = Base X (Fase)


    # usato in advance_simulator e shannon_simulator
    def run(self):
        for i in range(self.num_bits):
            bit = generate_random_bit()
            basis = generate_random_bit()
            self.raw_key.append(bit)
            self.bases.append(basis)
            
            qubit, = qapi.create_qubits(1)
            
            # Codifica BB84 / TF-QKD standard
            if basis == 0:  
                if bit == 1: qapi.operate(qubit, ns.X)
            else:  
                if bit == 1: qapi.operate(qubit, ns.X)
                qapi.operate(qubit, ns.H)
                
            self.node.ports[self.port_name].tx_output(qubit)
            yield self.await_timer(10)