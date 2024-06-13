import sys
import os
import re
from collections import defaultdict

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import QDragEnterEvent, QDropEvent


def detect_image_sequences(folder_path:str) -> list:
    sequences = defaultdict(list)
    
    for filename in os.listdir(folder_path):
        # Split the filename into name and extension
        name, extension = os.path.splitext(filename)
        
        # Find the sequence number by iterating from the end of the name
        i = len(name) - 1
        while i >= 0 and name[i].isdigit():
            i -= 1
        
        # The sequence number starts from the first digit we encounter
        sequence_number = name[i + 1:]
        base_name = name[:i + 1]
        
        if sequence_number:
            number = int(sequence_number)
            padding = len(sequence_number) * '#'
            key = (base_name, extension.lstrip('.'))
            sequences[key].append((number, filename, padding))
    
    results = []
    
    for key, values in sequences.items():
        base_name, extension = key
        padding = values[0][2]
        values.sort()
        ranges = []
        current_range = [values[0][0], values[0][0]]
        
        for i in range(1, len(values)):
            if values[i][0] == current_range[1] + 1:
                current_range[1] = values[i][0]
            else:
                ranges.append((current_range[0], current_range[1]))
                current_range = [values[i][0], values[i][0]]
        
        ranges.append((current_range[0], current_range[1]))
        
        result = {
            "name": base_name,
            "padding": padding,
            "ranges": ranges,
            "start": ranges[0][0],
            "extension": extension
        }
        
        results.append(result)
    
    return results


def get_rename_pairs(old:dict, new:dict) -> list:
    name_pairs = []
    offset = new["start"] - old["start"]
    for r in old["ranges"]:
        for i in range(r[0], r[1] + 1):
            name_pair = []
            name_pair.append(
                f'{old["name"]}{str(i).zfill(len(old["padding"]))}.{old["extension"]}'
            )
            name_pair.append(
                f'{new["name"]}{str(i + offset).zfill(len(new["padding"]))}.{new["extension"]}'
            )
            name_pairs.append(name_pair)
    return name_pairs


class SequenceRow(QWidget):
    sequence_renamed = Signal(str)

    def __init__(self, seq=None, path=None):
        super().__init__()
        self.old = seq
        self.path = path
        hbox = QHBoxLayout()
        hbox.setContentsMargins(1,0,1,0)
        hbox.setSpacing(2)
        self.name_field = QLineEdit(seq["name"])
        self.pad_field = QLineEdit(seq["padding"])
        dot = QLabel(".")
        self.ext_field = QLineEdit(seq["extension"])
        start_label = QLabel("Start Number:")
        self.start_field = QLineEdit(str(seq["start"]))
        self.rename_btn = QPushButton("Rename")

        self.pad_field.setMaximumWidth(40)
        dot.setMaximumWidth(10)
        self.ext_field.setMaximumWidth(30)
        start_label.setAlignment(Qt.AlignRight)
        start_label.setAlignment(Qt.AlignCenter)
        
        hbox.addWidget(self.name_field, stretch=1)
        hbox.addWidget(self.pad_field)
        hbox.addWidget(dot)
        hbox.addWidget(self.ext_field)
        hbox.addWidget(start_label)
        hbox.addWidget(self.start_field)
        hbox.addWidget(self.rename_btn)

        for i, s in enumerate([10,2,1,1,3,1,2]):
            hbox.setStretch(i, s)

        self.setLayout(hbox)

        self.rename_btn.clicked.connect(self._rename_clicked)

    def _rename_clicked(self):
        new = {
            "name": self.name_field.text(),
            "padding": self.pad_field.text(),
            "extension": self.ext_field.text(),
            "start": int(self.start_field.text())
        }
        rename_pairs = get_rename_pairs(self.old, new)
        # TODO: Wenn neuer name bereits existiert (z.B. weil man nur die startnummer, aber sonst nichts ändern will)
        # kann es zu Konflikten kommen (wenn sich z.B. die Nummern-Bereiche überschneiden!)
        # Hier sollte man gar nicht erst Renamen oder wenigstens den User vorher WARNEN!
        for old_name, new_name in rename_pairs:
            old_path = f"{self.path}/{old_name}"
            new_path = f"{self.path}/{new_name}"
            print(f"Renaming '{old_name}' to '{new_name}'")
            try:
                os.rename(old_path, new_path)
            except FileExistsError:
                print("Renaming skipped, as the new name already exists in this folder!")

        self.sequence_renamed.emit(self.path)


class SequenceRenamer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Squence Renamer")
        self.setMinimumWidth(600)
        self.setAcceptDrops(True)  # Enable drag and drop
        self._create_widgets()
        self._connect_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.drop_label = QLabel("Drop a folder here", self)
        self.drop_label.setMinimumHeight(150)
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("QLabel {font-size: 18px;}")
        self.current_path_label = QLabel("No folder dropped. Drop folder to field above!")
        self.global_seq_info_label = QLabel("No Folder -> No Sequence!")

    def _connect_widgets(self):
        pass

    def _create_layout(self):
        self.seq_row_vbox = QVBoxLayout()
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.drop_label)
        vbox.addWidget(self.current_path_label)
        vbox.addWidget(self.global_seq_info_label)
        vbox.addLayout(self.seq_row_vbox)
        self.setLayout(vbox)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()  # Accept the event if it has URLs

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            folder_path = urls[0].toLocalFile()
            if folder_path:  # Store the folder path
                self.folder_dropped(folder_path)
                              
    def folder_dropped(self, folder_path):
        sequences = detect_image_sequences(folder_path)
        # clear rows
        for i in reversed(range(self.seq_row_vbox.count())): 
            self.seq_row_vbox.itemAt(i).widget().setParent(None)
        # set global infos
        self.current_path_label.setText(folder_path)
        self.global_seq_info_label.setText(f"{len(sequences)} sequences detected:")

        # create row for each sequence
        for seq in sequences:
            row = SequenceRow(seq, folder_path)
            row.sequence_renamed.connect(self.folder_dropped)
            self.seq_row_vbox.addWidget(row)
         

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SequenceRenamer()
    window.show()
    sys.exit(app.exec_())