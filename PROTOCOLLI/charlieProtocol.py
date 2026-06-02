import netsquid as ns
from netsquid.protocols import NodeProtocol
from netsquid.qubits import qubitapi as qapi
import random


class CharlieProtocol(NodeProtocol):
    #Protocollo usato da Charlie: Bell State Measurement (BSM) simmetrico
    def __init__(self, node, port_a, port_b, num_bits, noise_probability=0.0, name="Charlie"):
        super().__init__(node, name)
        self.port_a = port_a
        self.port_b = port_b
        self.num_bits = num_bits
        self.noise_probability = noise_probability
        self.announcements = []

    # usato in demo, custom_noise e performance
    def run(self):
        for i in range(self.num_bits):
            # attesa di qubit sul canale
            yield self.await_port_input(self.node.ports[self.port_a]) & \
                  self.await_port_input(self.node.ports[self.port_b])
            
            qubit_a = self.node.ports[self.port_a].rx_input().items[0]
            qubit_b = self.node.ports[self.port_b].rx_input().items[0]
            
            # INIEZIONE DI RUMORE
            # Se la probabilità è impostata, applichiamo una porta Z a sorpresa,
            # invertendo la fase del fotone prima della misurazione.
            if self.noise_probability > 0:
                if random.random() < self.noise_probability:
                    qapi.operate(qubit_a, ns.Z)
                if random.random() < self.noise_probability:
                    qapi.operate(qubit_b, ns.Z)
            
            # Estrazione della parità di fase
            qapi.operate(qubit_a, ns.H)
            qapi.operate(qubit_b, ns.H)
            
            qapi.operate([qubit_a, qubit_b], ns.CX)
            
            res_parity, _ = qapi.measure(qubit_b)
            qapi.discard(qubit_a)
            
            self.announcements.append(res_parity)
            # stampa di log
            #print(f"   -> [Charlie] Qubit {i+1}: Parità rilevata = {'Uguali (0)' if res_parity == 0 else 'Diversi (1)'}")




class CharlieProtocolAdvanced(NodeProtocol):
    """Protocollo per Charlie: Bell State Measurement (BSM) simmetrico."""
    def __init__(self, node, port_a, port_b, num_bits, noise_probability=0.0, name="Charlie"):
        super().__init__(node, name)
        self.port_a = port_a
        self.port_b = port_b
        self.num_bits = num_bits
        self.noise_probability = noise_probability
        self.announcements = []

    # usato in advanced_simulator e shannon_simulator
    def run(self):
        for i in range(self.num_bits):
            yield self.await_port_input(self.node.ports[self.port_a]) & \
                  self.await_port_input(self.node.ports[self.port_b])
            
            qubit_a = self.node.ports[self.port_a].rx_input().items[0]
            qubit_b = self.node.ports[self.port_b].rx_input().items[0]
            
            # Vero BSM: CNOT (A controllo, B target) seguito da Hadamard su A
            qapi.operate([qubit_a, qubit_b], ns.CX)
            qapi.operate(qubit_a, ns.H)
            
            res_a, _ = qapi.measure(qubit_a)
            res_b, _ = qapi.measure(qubit_b)
            
            # Charlie pubblica i risultati di misurazione di entrambi i qubit
            self.announcements.append((res_a, res_b))
            #print(f"res_a == {res_a}, res_b = {res_b}")
