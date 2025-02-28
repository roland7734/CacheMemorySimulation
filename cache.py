import random

from PyQt5.QtWidgets import QApplication, QHBoxLayout, QTableWidget, QTableWidgetItem, QWidget, QLabel, QPushButton, \
    QVBoxLayout, QLineEdit, QTextEdit, QComboBox
from collections import OrderedDict, Counter
from PyQt5.QtCore import Qt

import sys

class CacheSimulator:
    def __init__(self, memory_size, cache_size, block_size, mapping, replacement_policy):
        self.memory_size = memory_size
        self.cache_size = cache_size
        self.block_size = block_size
        self.cache_size = min(memory_size, cache_size)
        self.index_max = cache_size // block_size - 1
        self.index_bits = len(bin(self.cache_size // self.block_size - 1)[2:])
        self.offset_bits = len(bin(self.block_size - 1)[2:])
        self.tag_bits = 32 - self.index_bits - self.offset_bits
        self.mapping = mapping
        self.replacement_policy = replacement_policy
        self.cache = OrderedDict()
        self.usage_count = Counter()
        self.hits = 0
        self.misses = 0
        self.associativity = 2
        self.evictions = 0
        self.hit_instructions = []
        self.miss_instructions = []
        self.sample_text = ""
        self.current_text = ""
        self.current_index = 0
        self.current_tag = 0

    def hit(self, address, index, tag):
        if self.replacement_policy == "LRU" or self.replacement_policy == "MRU":
            self.cache.move_to_end(index)
        else:
            if self.replacement_policy == "LFU":
                self.usage_count[index] += 1
        self.hits += 1
        self.current_text = f'{hex(address)}: {"Hit"}\n'
        self.sample_text += f'{hex(address)}: {"Hit"}\n'
        self.hit_instructions.append(address)

    def miss(self, address, index, tag):
        self.misses += 1
        self.current_text = f'{hex(address)}: {"Miss"}\n'
        self.sample_text += f'{hex(address)}: {"Miss"}\n'
        self.miss_instructions.append(address)
        if len(self.cache) >= self.cache_size // self.block_size:
            self.evictions += 1
            self.evict()
        self.cache[index] = tag
        self.usage_count[index] = 1

    def access_memory_address(self, address):
        self.get_index_and_tag(address)
        index = self.current_index
        tag = self.current_tag
        if address < 0 or address >= self.memory_size:
            raise ValueError(f"Invalid memory address: {hex(address)}")
        if self.mapping == "Direct Mapping":
            if index in self.cache and self.cache[index] == tag:
                self.hit(address, index, tag)
            else:
                self.miss(address, index, tag)

        elif self.mapping == "Fully Associative":
            if tag in self.cache.values():
                self.hits += 1
                self.current_text = f'{hex(address)}: {"Hit"}\n'
                self.sample_text += f'{hex(address)}: {"Hit"}\n'
                self.hit_instructions.append(address)
            else:
                self.misses += 1
                self.current_text = f'{hex(address)}: {"Miss"}\n'
                self.sample_text += f'{hex(address)}: {"Miss"}\n'
                self.miss_instructions.append(address)
                if len(self.cache) >= self.cache_size // self.block_size:
                    self.evictions += 1
                    self.evict()
                    index = self.find_unused_index()
                self.cache[index] = tag

    def find_unused_index(self):
        all_indices = set(range(self.cache_size // self.block_size))
        used_indices = set(self.cache.keys())
        unused_indices = all_indices - used_indices
        return min(unused_indices) if unused_indices else None

    def evict(self):
        """Evict one item from the cache based on the selected replacement policy."""
        if not self.cache:
            raise ValueError("Cache is empty, cannot evict.")
        if self.replacement_policy == "LRU":
            self.cache.popitem(last=False)
        elif self.replacement_policy == "FIFO":
            self.cache.popitem(last=False)
        elif self.replacement_policy == "RANDOM":
            random_key = random.choice(list(self.cache.keys()))
            del self.cache[random_key]
        elif self.replacement_policy == "LFU":
            lfu_key = min(self.usage_count, key=self.usage_count.get)
            del self.cache[lfu_key]
            del self.usage_count[lfu_key]
        elif self.replacement_policy == "MRU":
            self.cache.popitem(last=True)
        else:
            raise ValueError(f"Unknown replacement policy: {self.replacement_policy}")

    def evict_set(self, set_index):
        """ Evict one item from a cache set based on the selected replacement policy """
        if self.replacement_policy == "LRU":
            self.cache[set_index].popitem(last=False)  # LRU eviction for sets
        elif self.replacement_policy == "FIFO":
            self.cache[set_index].popitem(last=False)  # FIFO eviction for sets
        elif self.replacement_policy == "RANDOM":
            random_key = random.choice(list(self.cache[set_index].keys()))  # Random eviction for sets
            del self.cache[set_index][random_key]

    def get_index_and_tag(self, address):
        tag = 0
        index = 0
        if self.mapping == "Direct Mapping":
            tag = address >> (self.index_bits + self.offset_bits)
            index = (address >> self.offset_bits) & ((1 << self.index_bits) - 1)
        elif self.mapping == "Fully Associative":
            tag = address >> self.offset_bits
            index = len(self.cache)
            if index >= self.cache_size // self.block_size:
                self.evictions += 1
                self.evict()
                index = self.find_unused_index()

        self.current_index = index
        self.current_tag = tag


class CacheSimulatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.k = 0
        self.address_sequence = []
        self.cache_simulator = None

    def initUI(self):
        self.setWindowTitle('Cache Simulator')
        self.setGeometry(100, 100, 600, 400)

        # Labels and input fields
        self.memory_size_label = QLabel('Memory Size (bytes):')
        self.memory_size_input = QLineEdit()
        self.memory_size_input.setText("256")

        self.cache_size_label = QLabel('Cache Size (bytes):')
        self.cache_size_input = QLineEdit()
        self.cache_size_input.setText("32")

        self.block_size_label = QLabel('Block Size (bytes):')
        self.block_size_input = QLineEdit()
        self.block_size_input.setText("4")

        self.mapping_label = QLabel('Mapping Technique:')
        self.mapping_combobox = QComboBox()
        self.mapping_combobox.addItems(["Direct Mapping", "Fully Associative"])

        self.replacement_policy_label = QLabel('Replacement Policy:')
        self.replacement_policy_combobox = QComboBox()
        self.replacement_policy_combobox.addItems(["LRU", "FIFO", "RANDOM", "LFU", "MRU"])
        self.replacement_policy_combobox.setEnabled(False)

        self.mapping_combobox.currentIndexChanged.connect(self.update_replacement_policy_status)

        self.address_label = QLabel('Memory Address Sequence:')
        self.address_input = QLineEdit()
        self.address_input.setText("29, 15, 67, 53, 23, 11, 17, 18")

        self.simulate_button = QPushButton('Simulate')
        self.simulate_button.clicked.connect(self.simulate)

        self.generate_button = QPushButton('Generate 10 Random Addresses')
        self.generate_button.clicked.connect(self.generate_random_sequence)

        self.result_label = QLabel('Simulation Result:')
        self.result_textbox = QTextEdit()
        self.result_textbox.setReadOnly(True)

        self.history_label = QLabel('History:')
        self.history_textbox = QTextEdit()
        self.history_textbox.setReadOnly(True)

        self.hitMiss_label = QLabel('Hit / Miss:')
        self.hitMiss = QTextEdit('')
        self.hitMiss.setReadOnly(True)
        self.next_button = QPushButton('Next')
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.step_simulation)

        # Layout setup
        layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.addWidget(self.memory_size_label)
        left_layout.addWidget(self.memory_size_input)
        left_layout.addWidget(self.cache_size_label)
        left_layout.addWidget(self.cache_size_input)
        left_layout.addWidget(self.block_size_label)
        left_layout.addWidget(self.block_size_input)
        left_layout.addWidget(self.mapping_label)
        left_layout.addWidget(self.mapping_combobox)
        left_layout.addWidget(self.replacement_policy_label)
        left_layout.addWidget(self.replacement_policy_combobox)
        left_layout.addWidget(self.address_label)
        left_layout.addWidget(self.address_input)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.simulate_button)
        button_layout.addWidget(self.generate_button)
        left_layout.addLayout(button_layout)

        left_layout.addWidget(self.result_label)
        left_layout.addWidget(self.result_textbox)
        left_layout.addWidget(self.history_label)
        left_layout.addWidget(self.history_textbox)

        left_layout.addWidget(self.next_button)

        self.cache_table = QTableWidget()
        self.cache_table.setColumnCount(4)
        self.cache_table.setHorizontalHeaderLabels(["Index", "Valid", "Tag", "Data"])
        self.cache_table.verticalHeader().setVisible(False)
        self.cache_table.setColumnWidth(2, 250)  # Wider Tag field
        self.cache_table.setColumnWidth(3, 250)  # Wider Data field

        self.instr_table = QTableWidget()
        self.instr_table.setColumnCount(3)
        self.instr_table.setHorizontalHeaderLabels(["Tag", "Index", "Offset"])
        self.instr_table.verticalHeader().setVisible(False)
        self.instr_table.setColumnWidth(0, 250)





        table_layout = QVBoxLayout()
        table_layout.setAlignment(Qt.AlignCenter)
        table_layout.addWidget(self.cache_table)
        table_layout.addWidget(self.instr_table)
        table_layout.setSpacing(10)
        table_layout.setContentsMargins(10, 10, 10, 10)

        layout.addLayout(left_layout)
        layout.addLayout(table_layout)
        self.setLayout(layout)


        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;  /* Soft light gray background for the app */
            }
            QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #1b4f72;  /* Elegant dark blue for labels */
                font-family: 'Segoe UI', Arial, sans-serif; /* Clean, modern font */
            }
            QLineEdit, QTextEdit, QComboBox, QPushButton {
                font-size: 14px;
                padding: 8px;
                border: 1px solid #dcdde1;  /* Subtle gray border for inputs */
                border-radius: 8px;  /* Rounded corners for a polished look */
                background-color: #ffffff;  /* Crisp white input fields */
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #1b4f72;  /* Dark blue for input text */
            }
            QPushButton {
                background-color: #007bff;  /* Vibrant blue for buttons */
                color: white;  /* White text for high contrast */
                border-radius: 8px;
                border: 1px solid #0056b3;  /* Slightly darker blue border */
                font-weight: bold;  /* Bold text for emphasis */
            }
            QPushButton:hover {
                background-color: #0056b3;  /* Darker blue on hover for feedback */
                border: 1px solid #003f7f;  /* Even darker blue border on hover */
            }
            QTextEdit {
                background-color: #fcfcfd;  /* Slightly off-white for text background */
                border: 1px solid #dcdde1;
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #1b4f72;
            }
            QTableWidget {
                background-color: #ffffff;  /* White table background */
                border: 1px solid #dcdde1;  /* Soft gray border for tables */
                gridline-color: #ececec;  /* Subtle grid lines */
                alternate-background-color: #e9f3fb;  /* Light blue alternating row colors */
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                color: #1b4f72;  /* Dark blue for table text */
            }
            QHeaderView::section {
                background-color: #007bff;  /* Vibrant blue header for tables */
                color: white;  /* White text for headers */
                font-weight: bold;
                padding: 6px;
                text-align: center;
                border: 1px solid #0056b3;  /* Slightly darker blue border for headers */
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }

            QComboBox QAbstractItemView {
                selection-background-color: #007bff;  /* Blue highlight for dropdown selection */
                selection-color: white;  /* White text for selection */
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #007bff;  /* Blue border for focused inputs */
                outline: none;
            }
        """)

    def update_replacement_policy_status(self):
        if self.mapping_combobox.currentText() == "Direct Mapping":
            self.replacement_policy_combobox.setEnabled(False)
        else:
            self.replacement_policy_combobox.setEnabled(True)

    def generate_random_sequence(self):
        memory_size = int(self.memory_size_input.text())
        random_sequence = [random.randint(0, memory_size - 1) for _ in range(10)]
        self.address_input.setText(", ".join(map(str, random_sequence)))

    def simulate(self):
        try:
            # Initialize cache simulator parameters
            self.history_textbox.setPlainText("")
            self.next_button.setEnabled(True)
            memory_size = int(self.memory_size_input.text())
            cache_size = int(self.cache_size_input.text())
            block_size = int(self.block_size_input.text())
            mapping = self.mapping_combobox.currentText()
            replacement_policy = self.replacement_policy_combobox.currentText()
            self.address_sequence = [int(addr.strip()) for addr in self.address_input.text().split(',')]

            # Validate inputs
            if memory_size <= 0 or cache_size <= 0 or block_size <= 0 or not self.address_sequence:
                raise ValueError("All fields must be filled with positive values!")

            # Initialize cache simulator
            self.cache_simulator = CacheSimulator(memory_size, cache_size, block_size, mapping, replacement_policy)

            # Setup UI for simulation
            self.create_cache_table()
            self.create_instr_table()
            self.next_button.setEnabled(True)
            self.k = 0  # Reset address sequence index
            self.result_textbox.clear()
            self.step_simulation()  # Start the simulation with the first address
        except ValueError as e:
            self.result_textbox.setPlainText(str(e))

    def step_simulation(self):
        if self.k < len(self.address_sequence):
            address = self.address_sequence[self.k]
            self.k += 1
            self.cache_simulator.access_memory_address(address)

            # Update UI with simulation results
            self.update_cache_table()
            self.update_instr_table(address)
            self.update_result_textbox(address)
        else:
            self.next_button.setEnabled(False)
            self.history_textbox.setStyleSheet("color: blue;")
            self.history_textbox.append("Simulation Complete.")


    def create_cache_table(self):
        num_blocks = self.cache_simulator.cache_size // self.cache_simulator.block_size
        self.cache_table.setRowCount(num_blocks)
        self.cache_table.setColumnCount(4)
        self.cache_table.setHorizontalHeaderLabels(["Index", "Valid", "Tag", "Data"])

        self.cache_table.setColumnWidth(2, 250)  # Wider Tag field
        self.cache_table.setColumnWidth(3, 250)  # Wider Data field


        for i in range(num_blocks):
            self.cache_table.setItem(i, 0, QTableWidgetItem(str(i)))
            self.cache_table.setItem(i, 1, QTableWidgetItem("0"))  # Valid bit
            self.cache_table.setItem(i, 2, QTableWidgetItem("-"))  # Tag
            self.cache_table.setItem(i, 3, QTableWidgetItem("0"))  # Data

    def create_instr_table(self):
        self.instr_table.setRowCount(2)
        self.instr_table.setColumnCount(3)
        self.instr_table.setHorizontalHeaderLabels(["Tag", "Index", "Offset"])
        self.instr_table.setColumnWidth(0, 250)

        for i in range(3):
            self.instr_table.setItem(1, i, QTableWidgetItem("-"))  # Actual values
        self.instr_table.setItem(0, 0, QTableWidgetItem(f'{self.cache_simulator.tag_bits} bits'))
        self.instr_table.setItem(0, 1, QTableWidgetItem(f'{self.cache_simulator.index_bits} bits'))
        self.instr_table.setItem(0, 2, QTableWidgetItem(f'{self.cache_simulator.offset_bits} bits'))



    def update_cache_table(self):
        offset_bits = self.cache_simulator.offset_bits
        index_bits = self.cache_simulator.index_bits
        tag_bits = self.cache_simulator.tag_bits
        for index, tag in self.cache_simulator.cache.items():
            if index < self.cache_table.rowCount():
                self.cache_table.item(index, 1).setText("1")  # Valid bit
                self.cache_table.item(index, 2).setText(bin(tag)[2:].zfill(tag_bits)[-tag_bits:])  # Tag
                self.cache_table.item(index, 3).setText(f"BLOCK {hex((tag << index_bits | index)
                                                                     << (offset_bits - 2))[2:]} WORD 0 - {(1 << self.cache_simulator.offset_bits) - 1}")
        self.cache_table.setStyleSheet("QTableWidget::item { text-align: center; }")


    def update_instr_table(self, address):
        offset_bits = self.cache_simulator.offset_bits
        index_bits = self.cache_simulator.index_bits
        tag_bits = self.cache_simulator.tag_bits
        self.instr_table.item(1, 0).setText(bin(self.cache_simulator.current_tag)[2:].zfill(tag_bits)[-tag_bits:])
        self.instr_table.item(1, 1).setText(bin(self.cache_simulator.current_index)[2:].zfill(index_bits)[-index_bits:])
        self.instr_table.item(1, 2).setText(bin(address)[2:].zfill(offset_bits)[-offset_bits:])
        self.instr_table.setStyleSheet("QTableWidget::item { text-align: center; }")


    def update_result_textbox(self, address):
        hit_or_miss = "Hit" if address in self.cache_simulator.hit_instructions else "Miss"
        self.hitMiss.setPlainText(f"{address} = {hex(address)}: {hit_or_miss}")
        self.hitMiss.setStyleSheet("color: blue;" if hit_or_miss == "Hit" else "color: red;")

        if hit_or_miss == "Hit":
            self.history_textbox.setTextColor(Qt.blue)
        else:
            self.history_textbox.setTextColor(Qt.red)
        self.history_textbox.append(f"{address} = {hex(address)}: {hit_or_miss}")

        total_accesses = self.cache_simulator.hits + self.cache_simulator.misses
        hit_rate = (self.cache_simulator.hits / total_accesses) * 100 if total_accesses > 0 else 0
        miss_rate = (self.cache_simulator.misses / total_accesses) * 100 if total_accesses > 0 else 0

        self.result_textbox.setPlainText(
            f"Hits: {self.cache_simulator.hits} ({hit_rate:.2f}%)\n"
            f"Misses: {self.cache_simulator.misses} ({miss_rate:.2f}%)\n"
            f"Evictions: {self.cache_simulator.evictions}\n"
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CacheSimulatorApp()
    window.setGeometry(100, 100, 600, 600)
    while True:
        window.show()
        sys.exit(app.exec_())