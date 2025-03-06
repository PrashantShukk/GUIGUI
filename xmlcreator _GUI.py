from PySide6 import QtWidgets, QtCore
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import sys

# Adjust path to point one level up to the Functions folder.
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Functions"))
sys.path.append(parent_dir)

from actionsList import ACTION_FUNCTIONS
FUNCTION_DEFS = list(ACTION_FUNCTIONS.keys())

INPUT_TYPE_OPTIONS = ["None", "Bool", "String", "Integer", "EffectorSelection Object Type", "Dropdown"]

CONFIG_FILE = os.path.join(os.path.expanduser("~/Documents"), "functions_config.xml")
PASSCODE = "1234"  # Set your passcode here

class OptionsEditorDialog(QtWidgets.QDialog):
    def __init__(self, initial_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Dropdown Options")
        self.resize(400, 300)
        layout = QtWidgets.QVBoxLayout(self)
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setPlainText(initial_text)
        layout.addWidget(self.text_edit)
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
    
    def get_options(self):
        text = self.text_edit.toPlainText().strip()
        options = [opt.strip() for opt in text.split(",") if opt.strip()]
        return ",".join(options)

class XMLCreatorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)  # new style super()
        self.setWindowTitle("Functions XML Creator")
        self.resize(900, 400)
        # ... rest of your initialization code ...
            
        main_layout = QtWidgets.QVBoxLayout(self)
        instr = ("Enter function details. Click 'Add Function' to add new rows and 'Generate XML' to save the configuration.\n"
                "Existing items (if any) are loaded on top.\n"
                "For 'Input Type', if you select 'Dropdown', click 'Edit Options' to define dropdown choices.\n"
                "The 'Definition' dropdown is populated from actions.py.")
        instr_label = QtWidgets.QLabel(instr)
        main_layout.addWidget(instr_label)
        
        # Create table with 9 columns.
        headers = ["Up", "Down", "Function Name", "Definition", "Input Type", "Default Value", "Dropdown Options", "Description", "Add Input", "Delete"]
        self.table = QtWidgets.QTableWidget(0, len(headers), self)
        self.table.setHorizontalHeaderLabels(headers)
        # Set columns 0 and 1 to Fixed and the rest to Stretch.
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        for col in range(2, self.table.columnCount()):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(25)
        main_layout.addWidget(self.table)

        # Set fixed widths for Up and Down columns to 10 pixels each.
        # Set columns 0 and 1 to fixed widths as already done...
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        for col in range(2, 8):  # Only columns 2 to 7 are set to Stretch
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(8, QtWidgets.QHeaderView.Fixed)  # "Add Input" column
        header.setSectionResizeMode(9, QtWidgets.QHeaderView.Fixed)  # "Delete" column

        self.table.setColumnWidth(0, 10)
        self.table.setColumnWidth(1, 10)
        self.table.setColumnWidth(8, 100)  # Set a fixed width for the "Add Input" button column
        self.table.setColumnWidth(9, 100)  # Set a fixed width for the "Delete" button column






        
        btn_layout = QtWidgets.QHBoxLayout()
        self.addButton = QtWidgets.QPushButton("Add Function")
        self.generateButton = QtWidgets.QPushButton("Generate XML")
        btn_layout.addWidget(self.addButton)
        btn_layout.addWidget(self.generateButton)
        main_layout.addLayout(btn_layout)
        
        self.addButton.clicked.connect(lambda: self.addFunctionRow())
        self.generateButton.clicked.connect(self.generateXML)
        
        self.loadExistingXML()

    
    def loadExistingXML(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            tree = ET.parse(CONFIG_FILE)
            root = tree.getroot()
            for function_elem in root.findall("Function"):
                fn_name = function_elem.get("name", "")
                definition = function_elem.findtext("Definition", "")
                desc = function_elem.findtext("Description", "")
                input_elem = function_elem.find("./Inputs/Input")
                if input_elem is not None:
                    input_type = input_elem.get("type", "None")
                    default_value = input_elem.get("default", "")
                    options = input_elem.get("options", "")
                else:
                    input_type = "None"
                    default_value = ""
                    options = ""
                self.addFunctionRow(fn_name, definition, input_type, default_value, options, desc)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to load existing XML:\n{str(e)}")

    
    def addFunctionRow(self, fn_name="", definition="", input_type="None", default_value="", options="", description=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 25)
        
        # Column 0: Up button
        up_button = QtWidgets.QPushButton("↑")
        up_button.setFixedWidth(20)  # Thinner button
        up_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: lightgreen;
            }
        """)
        up_button.clicked.connect(lambda checked=None, r=row: self.moveRowUp(r))
        self.table.setCellWidget(row, 0, up_button)
        
        # Column 1: Down button
        down_button = QtWidgets.QPushButton("↓")
        down_button.setFixedWidth(20)  # Thinner button
        down_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:pressed {
                background-color: lightcoral;
            }
        """)
        down_button.clicked.connect(lambda checked=None, r=row: self.moveRowDown(r))
        self.table.setCellWidget(row, 1, down_button)
        
        # Column 2: Function Name
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(fn_name))
        
        # Column 3: Definition (dropdown from FUNCTION_DEFS with extra option)
        def_combo = QtWidgets.QComboBox()
        items = FUNCTION_DEFS.copy()
        items.append("define one now(100% safe)")
        def_combo.addItems(items)
        if definition in items:
            def_combo.setCurrentText(definition)
        else:
            def_combo.setCurrentIndex(0)
        self.table.setCellWidget(row, 3, def_combo)
        def_combo.currentIndexChanged.connect(lambda index, row=row, combo=def_combo: self.handleNewDefinition(row, combo))
        
        # Column 4: Input Type (dropdown)
        type_combo = QtWidgets.QComboBox()
        type_combo.addItems(INPUT_TYPE_OPTIONS)
        type_combo.setCurrentText(input_type)
        self.table.setCellWidget(row, 4, type_combo)
        type_combo.currentIndexChanged.connect(lambda index, r=row, cb=type_combo: self.updateDefaultAndOptionsCells(r, cb))
        
        # Column 5: Default Value (QLineEdit or QComboBox)
        if input_type == "Dropdown":
            default_combo = QtWidgets.QComboBox()
            if options:
                opts = [opt.strip() for opt in options.split(",") if opt.strip()]
                default_combo.addItems(opts)
            default_combo.setCurrentText(default_value)
            self.table.setCellWidget(row, 5, default_combo)
        else:
            line_edit = QtWidgets.QLineEdit()
            line_edit.setText(default_value)
            self.table.setCellWidget(row, 5, line_edit)
        
        # Column 6: Dropdown Options – "Edit Options" button
        opt_button = QtWidgets.QPushButton("Edit Options")
        opt_button.setEnabled(input_type == "Dropdown")
        opt_button.setProperty("options", options)
        if options:
            opt_button.setText("Options: " + options)
        self.table.setCellWidget(row, 6, opt_button)
        opt_button.clicked.connect(lambda checked=None, r=row: self.editDropdownOptions(r))
        
        # Column 7: Description
        self.table.setItem(row, 7, QtWidgets.QTableWidgetItem(description))
        
        # Column 8: Add Input button (new)
        add_input_button = QtWidgets.QPushButton("Add Input")
        add_input_button.setStyleSheet("background-color: yellow;")
        add_input_button.clicked.connect(lambda checked=None, r=row: self.addSecondInput(r))
        self.table.setCellWidget(row, 8, add_input_button)

        
        # Column 9: Delete button
        del_button = QtWidgets.QPushButton("Delete")
        del_button.clicked.connect(lambda checked=None, r=row: self.deleteRow(r))
        self.table.setCellWidget(row, 9, del_button)


    
    def handleNewDefinition(self, row, combo):
        # Check if the selected item is our extra option.
        if combo.currentText() == "define one now(100% safe)":
            # Get the function name from column 2 ("Function Name")
            fn_item = self.table.item(row, 2)
            if fn_item:
                new_func_name = fn_item.text().strip()
                # Only proceed if a non-empty name is provided and it's not already defined.
                if new_func_name and new_func_name not in ACTION_FUNCTIONS:
                    # Create a default function template.
                    code = (
                        f"\ndef {new_func_name}(input_value='Default {new_func_name} Value'):\n"
                        f"    print('Executing {new_func_name} with input:', input_value)\n"
                    )
                    # Append the new function definition to the actions.py file.
                    actions_file = os.path.join(os.path.dirname(__file__), "actions.py")
                    try:
                        with open(actions_file, "a", encoding="utf-8") as f:
                            f.write(code)
                    except Exception as file_err:
                        QtWidgets.QMessageBox.warning(self, "File Write Error", f"Could not update actions.py:\n{file_err}")
                        return

                    # Define the function in the global namespace.
                    exec(code, globals())
                    # Update the in-memory dictionary and list.
                    ACTION_FUNCTIONS[new_func_name] = globals()[new_func_name]
                    FUNCTION_DEFS.append(new_func_name)
                    # Replace the extra item with the new function's name in this combobox.
                    combo.setItemText(combo.count()-1, new_func_name)
                    combo.setCurrentText(new_func_name)




    
    def updateDefaultAndOptionsCells(self, row, type_combo):
        current_type = type_combo.currentText()
        opt_button = self.table.cellWidget(row, 6)
        default_widget = self.table.cellWidget(row, 5)
        
        if current_type == "Dropdown":
            opt_button.setEnabled(True)
            if not isinstance(default_widget, QtWidgets.QComboBox):
                default_combo = QtWidgets.QComboBox()
                self.table.setCellWidget(row, 5, default_combo)
            else:
                default_combo = default_widget
            options_str = opt_button.property("options") or ""
            default_combo.clear()
            if options_str:
                options_list = [opt.strip() for opt in options_str.split(",") if opt.strip()]
                default_combo.addItems(options_list)
        else:
            opt_button.setEnabled(False)
            opt_button.setProperty("options", "")
            opt_button.setText("Edit Options")
            if not isinstance(default_widget, QtWidgets.QLineEdit):
                line_edit = QtWidgets.QLineEdit()
                self.table.setCellWidget(row, 5, line_edit)
    
    def editDropdownOptions(self, row):
        opt_button = self.table.cellWidget(row, 6)
        current_options = opt_button.property("options") or ""
        dialog = OptionsEditorDialog(initial_text=current_options, parent=self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            options_str = dialog.get_options()
            opt_button.setProperty("options", options_str)
            if options_str:
                opt_button.setText("Options: " + options_str)
            else:
                opt_button.setText("Edit Options")
            type_widget = self.table.cellWidget(row, 4)
            if type_widget.currentText() == "Dropdown":
                default_widget = self.table.cellWidget(row, 5)
                if isinstance(default_widget, QtWidgets.QComboBox):
                    options_list = [opt.strip() for opt in options_str.split(",") if opt.strip()]
                    default_widget.clear()
                    default_widget.addItems(options_list)
    
    def getAllRowsData(self):
        data = []
        row_count = self.table.rowCount()
        for row in range(row_count):
            fn_item = self.table.item(row, 2)
            def_widget = self.table.cellWidget(row, 3)
            type_widget = self.table.cellWidget(row, 4)
            default_widget = self.table.cellWidget(row, 5)
            opt_button = self.table.cellWidget(row, 6)
            desc_item = self.table.item(row, 7)
            
            fn_name = fn_item.text().strip() if fn_item else ""
            definition = def_widget.currentText().strip() if isinstance(def_widget, QtWidgets.QComboBox) else ""
            input_type = type_widget.currentText().strip() if isinstance(type_widget, QtWidgets.QComboBox) else ""
            if input_type == "Dropdown":
                default_value = default_widget.currentText().strip() if isinstance(default_widget, QtWidgets.QComboBox) else ""
            else:
                default_value = default_widget.text().strip() if isinstance(default_widget, QtWidgets.QLineEdit) else ""
            dropdown_options = opt_button.property("options") or ""
            description = desc_item.text().strip() if desc_item else ""
            
            data.append({
                "fn_name": fn_name,
                "definition": definition,
                "input_type": input_type,
                "default_value": default_value,
                "dropdown_options": dropdown_options,
                "description": description
            })
        return data
    
    def repopulateTable(self, rows_data):
        self.table.setRowCount(0)
        for row_data in rows_data:
            self.addFunctionRow(
                fn_name=row_data.get("fn_name", ""),
                definition=row_data.get("definition", ""),
                input_type=row_data.get("input_type", "None"),
                default_value=row_data.get("default_value", ""),
                options=row_data.get("dropdown_options", ""),
                description=row_data.get("description", "")
            )
    
    def moveRowUp(self, row):
        rows_data = self.getAllRowsData()
        if row <= 0:
            return
        rows_data[row], rows_data[row-1] = rows_data[row-1], rows_data[row]
        self.repopulateTable(rows_data)
    
    def moveRowDown(self, row):
        rows_data = self.getAllRowsData()
        if row >= len(rows_data) - 1:
            return
        rows_data[row], rows_data[row+1] = rows_data[row+1], rows_data[row]
        self.repopulateTable(rows_data)
    
    def deleteRow(self, row):
        # Prompt with a warning and passcode
        passcode, ok = QtWidgets.QInputDialog.getText(
            self, "Delete Confirmation", "Enter passcode to delete this row:", 
            QtWidgets.QLineEdit.Password
        )
        if not ok or passcode != PASSCODE:
            QtWidgets.QMessageBox.warning(self, "Invalid Passcode", "Incorrect passcode. Row not deleted.")
            return
        rows_data = self.getAllRowsData()
        if 0 <= row < len(rows_data):
            rows_data.pop(row)
            self.repopulateTable(rows_data)
    
    def generateXML(self):
        """
        Generates the XML configuration.
        For functions with multiple inputs, the 'Input Type' and 'Default Value'
        fields should contain semicolon-separated values.
        """
        root = ET.Element("Functions")
        row_count = self.table.rowCount()
        for row in range(row_count):
            fn_item = self.table.item(row, 2)
            def_widget = self.table.cellWidget(row, 3)
            type_widget = self.table.cellWidget(row, 4)
            default_widget = self.table.cellWidget(row, 5)
            opt_button = self.table.cellWidget(row, 6)
            desc_item = self.table.item(row, 7)
            
            if fn_item is None or def_widget is None:
                continue
            
            fn_name = fn_item.text().strip()
            definition = def_widget.currentText().strip() if isinstance(def_widget, QtWidgets.QComboBox) else ""
            description = desc_item.text().strip() if desc_item else ""
            
            # Split the input types and default values by semicolon.
            type_text = type_widget.currentText().strip()
            input_types = [t.strip() for t in type_text.split(";")] if ";" in type_text else [type_text]
            
            default_text = ""
            if isinstance(default_widget, QtWidgets.QLineEdit):
                default_text = default_widget.text().strip()
            elif isinstance(default_widget, QtWidgets.QComboBox):
                default_text = default_widget.currentText().strip()
            default_values = [d.strip() for d in default_text.split(";")] if ";" in default_text else [default_text]
            
            # Create the Function element.
            function_elem = ET.Element("Function", name=fn_name)
            def_elem = ET.SubElement(function_elem, "Definition")
            def_elem.text = definition
            inputs_elem = ET.SubElement(function_elem, "Inputs")
            
            # Determine how many inputs to create.
            num_inputs = max(len(input_types), len(default_values))
            options_str = opt_button.property("options") or ""
            for i in range(num_inputs):
                input_attribs = {}
                input_attribs["type"] = input_types[i] if i < len(input_types) else "None"
                input_attribs["default"] = default_values[i] if i < len(default_values) else ""
                if input_attribs["type"] == "Dropdown" and options_str:
                    input_attribs["options"] = options_str
                ET.SubElement(inputs_elem, "Input", **input_attribs)
            
            desc_elem = ET.SubElement(function_elem, "Description")
            desc_elem.text = description
            root.append(function_elem)
        
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        xml_str = reparsed.toprettyxml(indent="  ")
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(xml_str)
        QtWidgets.QMessageBox.information(self, "XML Generated", "XML configuration saved to:\n" + CONFIG_FILE)


    def addSecondInput(self, row):
        dialog = AdditionalInputDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            values = dialog.getValues()
            # Get the current cell widgets/items for Input Type, Default Value, Dropdown Options, and Description
            type_widget = self.table.cellWidget(row, 4)  # QComboBox for Input Type
            default_widget = self.table.cellWidget(row, 5)  # QLineEdit or QComboBox
            opt_button = self.table.cellWidget(row, 6)      # Options button
            desc_item = self.table.item(row, 7)             # QTableWidgetItem for Description
            
            # Retrieve current texts
            current_type = ""
            if isinstance(type_widget, QtWidgets.QComboBox):
                current_type = type_widget.currentText().strip()
            current_default = ""
            if isinstance(default_widget, QtWidgets.QLineEdit):
                current_default = default_widget.text().strip()
            elif isinstance(default_widget, QtWidgets.QComboBox):
                current_default = default_widget.currentText().strip()
            current_options = opt_button.property("options") or ""
            current_desc = desc_item.text().strip() if desc_item is not None else ""
            
            # Append the new values using semicolon as separator (if a current value exists)
            new_type = current_type + (";" + values["input_type"] if current_type else values["input_type"])
            new_default = current_default + (";" + values["default_value"] if current_default else values["default_value"])
            # For dropdown options, append only if new value is provided
            new_options = current_options
            if values["options"]:
                new_options = current_options + (";" + values["options"] if current_options else values["options"])
            new_desc = current_desc + (";" + values["description"] if current_desc else values["description"])
            
            # Update the cells with the new concatenated values.
            if isinstance(type_widget, QtWidgets.QComboBox):
                # Set the text in the combobox (this may require the new value to already exist in its list;
                # if not, you might convert it to a QLineEdit for free text)
                type_widget.setCurrentText(new_type)
            else:
                type_widget.setText(new_type)
            
            if isinstance(default_widget, QtWidgets.QLineEdit):
                default_widget.setText(new_default)
            elif isinstance(default_widget, QtWidgets.QComboBox):
                default_widget.setCurrentText(new_default)
            
            opt_button.setProperty("options", new_options)
            if new_options:
                opt_button.setText("Options: " + new_options)
            else:
                opt_button.setText("Edit Options")
            
            if desc_item is not None:
                desc_item.setText(new_desc)
            else:
                self.table.setItem(row, 7, QtWidgets.QTableWidgetItem(new_desc))


class AdditionalInputDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Additional Input")
        self.resize(400, 200)
        layout = QtWidgets.QFormLayout(self)
        # Input Type combobox
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(INPUT_TYPE_OPTIONS)
        layout.addRow("Input Type:", self.type_combo)
        # Default Value
        self.default_edit = QtWidgets.QLineEdit()
        layout.addRow("Default Value:", self.default_edit)
        # Dropdown Options (only relevant if type is Dropdown)
        self.options_edit = QtWidgets.QLineEdit()
        layout.addRow("Dropdown Options:", self.options_edit)
        # Description
        self.desc_edit = QtWidgets.QLineEdit()
        layout.addRow("Description:", self.desc_edit)
        # Buttons
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addRow(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
    
    def getValues(self):
        return {
            "input_type": self.type_combo.currentText(),
            "default_value": self.default_edit.text().strip(),
            "options": self.options_edit.text().strip(),
            "description": self.desc_edit.text().strip()
        }


def get_mobu_main_window():
    app = QtWidgets.QApplication.instance()
    for widget in app.topLevelWidgets():
        if widget.objectName() == "FBMainWindow":
            return widget
    return None

def launch_xml_creator():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])
    
    main_win = get_mobu_main_window()
    dialog = XMLCreatorDialog(parent=main_win)
    dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    return dialog




# Launch the XML creator tool.
# myDialog = launch_xml_creator()
