import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel
from netsquid.protocols import NodeProtocol
from netsquid.qubits import qubitapi as qapi

class SenderMin(NodeProtocol):
    def run(self):
        for i in range(3):
            qubit, = qapi.create_qubits(1)
            print(f"[Sender {self.node.name}] invio qubit {i} al t={ns.sim_time()}")
            self.node.ports["out"].tx_output(qubit)
            yield self.await_timer(10)

class ReceiverMin(NodeProtocol):
    def __init__(self, node, port_a, port_b):
        super().__init__(node)
        self.port_a = port_a
        self.port_b = port_b
        self._buf_a = []
        self._buf_b = []

    def _on_a(self, msg):
        print(f"  [Handler A] ricevuto al t={ns.sim_time()}, msg={msg}, items={msg.items}")
        self._buf_a.append(msg.items[0])

    def _on_b(self, msg):
        print(f"  [Handler B] ricevuto al t={ns.sim_time()}, msg={msg}, items={msg.items}")
        self._buf_b.append(msg.items[0])

    def run(self):
        self.node.ports[self.port_a].bind_input_handler(self._on_a)
        self.node.ports[self.port_b].bind_input_handler(self._on_b)
        for i in range(3):
            print(f"[Receiver] ciclo {i}, attendo timer...")
            while len(self._buf_a) == 0 or len(self._buf_b) == 0:
                yield self.await_timer(1)
                print(f"  [Receiver] tick, buf_a={len(self._buf_a)}, buf_b={len(self._buf_b)}")
            qa = self._buf_a.pop(0)
            qb = self._buf_b.pop(0)
            print(f"[Receiver] BSM {i} su {qa}, {qb}")

ns.sim_reset()
alice = Node("Alice", port_names=["out"])
bob   = Node("Bob",   port_names=["out"])
charlie = Node("Charlie", port_names=["in_a", "in_b"])

ch_a = QuantumChannel("ChA", delay=10)
ch_b = QuantumChannel("ChB", delay=10)
alice.ports["out"].connect(ch_a.ports["send"])
ch_a.ports["recv"].connect(charlie.ports["in_a"])
bob.ports["out"].connect(ch_b.ports["send"])
ch_b.ports["recv"].connect(charlie.ports["in_b"])

SenderMin(alice).start()
SenderMin(bob).start()
ReceiverMin(charlie, "in_a", "in_b").start()

ns.sim_run(duration=500)
print("DONE")