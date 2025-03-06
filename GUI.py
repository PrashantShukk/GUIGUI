from PySide6 import QtWidgets, QtCore, QtGui
import sys
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom  # Import minidom for pretty-printing
import random

# Ensure QApplication is running (MotionBuilder manages the event loop)
app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)


# Get the absolute path of the folder containing 'Functions'
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "Functions"))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "Tool"))

# Add this path to sys.path
sys.path.append(parent_dir)

from xmlcreator import launch_xml_creator
import actionsList


# Define global variables
import pyfbsdk  # Ensure MotionBuilder SDK is available        
system = pyfbsdk.FBSystem()
saved_state = {}
active_layer_val = None



def loadFunctionDefinitionsFromXML(xml_file):
    """Load function definitions from the given XML file.
    
    Each <Function> element in the XML is converted to a dictionary with keys:
    - name: the Function name attribute
    - definition: the text inside the <Definition> element
    - input_type: from the <Input> element's type attribute (if present)
    - default_value: from the <Input> element's default attribute (if present)
    - options: from the <Input> element's options attribute (if present)
    """
    functions = []
    if os.path.exists(xml_file):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for f in root.findall("Function"):
                fn_name = f.get("name", "").strip()
                definition = f.findtext("Definition", "").strip()
                description = f.findtext("Description", "").strip()
                inputs = []
                for input_elem in f.findall("./Inputs/Input"):
                    inputs.append({
                        "input_type": input_elem.get("type", "None").strip(),
                        "default_value": input_elem.get("default", "").strip(),
                        "options": input_elem.get("options", "").strip()
                    })
                functions.append({
                    "name": fn_name,
                    "definition": definition,
                    "description": description,
                    "inputs": inputs
                })
        except Exception as e:
            print(f"Error loading XML: {e}")
    return functions



class GUIGUI(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(GUIGUI, self).__init__(parent)
        self.xml_file = os.path.join(os.path.expanduser("~/Documents"), "functions_config.xml")
        self.function_definitions = loadFunctionDefinitionsFromXML(self.xml_file)
        self.setWindowTitle("GUI GUI")


        self.ui_hidden = False  # Initialize the attribute here
        # Remove top bar (frameless) but keep it on top
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)


       # Set up the main layout and let it auto-size to fit the content
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.setFixedWidth(350)


        self.main_layout.setSpacing(2)

        # --- Top Row: Title + Plus Button + Settings Button + Close Button ---
        self.top_layout = QtWidgets.QHBoxLayout()  # ✅ Define it before use
        self.top_layout.setSpacing(2)


        # Store last entered text
        self.last_entered_text = ""

        # Define 10 color options
        self.colors = [
            "#D8BFD8",  # Thistle (Soft Purple)
            "#AFEEEE",  # Pale Turquoise (Soft Blue)
            "#E6E6FA",  # Lavender (Light Purple)
            "#D3D3D3",  # Light Gray
            "#F5F5DC",  # Beige
            "#F0E68C",  # Khaki (Muted Yellow)
            "#C1E1C1",  # Tea Green (Muted Green)
            "#FAEBD7",  # Antique White
            "#E0FFFF",  # Light Cyan
            "#F4A460"   # Sandy Brown (Soft Orange)
        ]


        # Choose a random color once and store it
        self.name_input_color = random.choice(self.colors)  

        # Set up the name input field
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setText("GUI GUI")
        self.name_input.setFixedHeight(25)
        self.name_input.setMinimumWidth(125)
        self.name_input.setAlignment(QtCore.Qt.AlignCenter)  # Center the text
        self.name_input.setStyleSheet(f"color: {self.name_input_color}; font-weight: bold;")  # Use stored color
        self.name_input.installEventFilter(self)
        self.name_input.textChanged.connect(self.updateRunButtonName)



        self.plus_button = QtWidgets.QPushButton("➕")
        self.plus_button.clicked.connect(self.addDropdownInputRow)

        self.settings_button = QtWidgets.QPushButton("⚙️")
        self.settings_button.clicked.connect(self.toggleSettingsPanel)

        self.close_button = QtWidgets.QPushButton("❌")
        self.close_button.clicked.connect(self.close)

        self.top_layout.addWidget(self.name_input)
        self.top_layout.addStretch(1)
        self.top_layout.addWidget(self.plus_button)
        self.top_layout.addWidget(self.settings_button)
        self.top_layout.addWidget(self.close_button)
        self.main_layout.addLayout(self.top_layout)

        # Ensure the name input does not start in input mode
        self.setFocus()  # Forces the focus to the main window, preventing the input box from being in edit mode


        # --- Dropdown Container ---
        self.dropdown_container_widget = QtWidgets.QWidget(self)
        self.dropdown_input_container = QtWidgets.QVBoxLayout(self.dropdown_container_widget)
        self.dropdown_input_container.setSpacing(2)
        self.main_layout.addWidget(self.dropdown_container_widget)

        # Initialize action rows list and add first dropdown row
        self.action_rows = []
        self.addDropdownInputRow(force_update=True)


         # Connect dropdown interactions to reset the name input
        for row in self.action_rows:
            row["dropdown"].currentIndexChanged.connect(self.resetNameInput)





        self.run_layout = QtWidgets.QHBoxLayout()
        self.run_button = QtWidgets.QPushButton("Run")
        self.run_button.setFixedHeight(25)
        self.run_button.clicked.connect(self.runAllActions)
        
        self.hide_ui_button = QtWidgets.QPushButton("Hide UI")
        self.hide_ui_button.setFixedHeight(25)
        self.hide_ui_button.clicked.connect(self.toggleUIVisibility)
        
        self.run_layout.addWidget(self.run_button)
        self.run_layout.addWidget(self.hide_ui_button)
        
        self.main_layout.addLayout(self.run_layout)
        
        # Output Bar (Floating, Attached to Window Edges)
        self.output_bar = QtWidgets.QLabel("")
        self.output_bar.setFixedHeight(20)
        self.output_bar.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.output_bar.setStyleSheet("background-color: #1A1A2E; color: white; font-size: 12px; border: none; margin: 0px; padding: 0px;")
        self.main_layout.addWidget(self.output_bar)





        # Enable window dragging
        self.drag_position = None


 



    def resetNameInput(self):
        """Resets the input field to 'GUI GUI' if it's empty and not currently focused."""
        if not self.name_input.hasFocus() and not self.name_input.text().strip():
            self.name_input.setText("GUI GUI")
            self.name_input.setStyleSheet(f"color: {self.name_input_color}; font-weight: bold;")  # Keep stored color


    def updateInputField(self, row_data):
        dropdown = row_data["dropdown"]
        layout = row_data["inputs_container_layout"]

        # Clear any previous input widgets.
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        selected_action = dropdown.currentText()
        func_def = next((f for f in self.function_definitions if f["name"] == selected_action), None)

        # Update tooltip for dropdown.
        if func_def:
            dropdown.setToolTip(func_def.get("description", ""))
        else:
            dropdown.setToolTip("")

        # If no function definition, add a default text input.
        if not func_def:
            single_input = QtWidgets.QLineEdit()
            single_input.setPlaceholderText("Enter value...")
            layout.addWidget(single_input)
            row_data["input_widgets"] = [single_input]
            return

        inputs = func_def.get("inputs", [])
        if not inputs:
            # No inputs defined: show one default text input.
            single_input = QtWidgets.QLineEdit()
            single_input.setPlaceholderText("Enter value...")
            layout.addWidget(single_input)
            row_data["input_widgets"] = [single_input]
            return

        # If there is exactly one input defined, create one widget.
        # If two or more are defined, create exactly two separate widgets.
        row_data["input_widgets"] = []
        num_to_create = 1 if len(inputs) == 1 else 2

        for i in range(num_to_create):
            inp_def = inputs[i]  # We assume the XML defines these in order.
            if inp_def["input_type"] == "Dropdown":
                widget = QtWidgets.QComboBox()
                widget.setFixedHeight(22)
                if inp_def["options"]:
                    opts = [o.strip() for o in inp_def["options"].split(",") if o.strip()]
                    widget.addItems(opts)
                if inp_def["default_value"] and inp_def["default_value"] in [widget.itemText(j) for j in range(widget.count())]:
                    widget.setCurrentText(inp_def["default_value"])
            else:
                widget = QtWidgets.QLineEdit()
                widget.setFixedHeight(22)
                widget.setPlaceholderText("Enter value...")
                if inp_def["default_value"]:
                    widget.setText(inp_def["default_value"])

            # Here we set a fixed width for each input widget so that when two exist they share the space.
            widget.setFixedWidth(80)  # Adjust this value as needed.
            layout.addWidget(widget)
            row_data["input_widgets"].append(widget)





        def save_current_state(self):
            """Saves the current take, effector, active layer, and frame number before running actions."""
            global saved_state, active_layer_val

            # Get current take name and find its index
            take = pyfbsdk.FBSystem().CurrentTake
            take_name = take.Name if take else "None"

            # Manually find the index of the current take
            take_index = -1
            if take:
                for i, t in enumerate(pyfbsdk.FBSystem().Scene.Takes):
                    if t == take:
                        take_index = i
                        break

            # Get currently selected effector
            selected_effector = None
            for eff in pyfbsdk.FBSystem().Scene.Components:
                if isinstance(eff, pyfbsdk.FBModel):  # Change to FBModel for effectors
                    if eff.Selected:
                        selected_effector = eff.LongName
                        break  # Stop at the first selected effector


            active_layer = pyfbsdk.FBSystem().CurrentTake.GetCurrentLayer()
            # Since active_layer is now an integer, convert it to a string.
            active_layer_val = str(active_layer) if active_layer is not None else "None"


            # Get current frame number
            current_frame = pyfbsdk.FBSystem().LocalTime.GetFrame()

            if active_layer is not None:
                active_layer_val = str(active_layer)
            else:
                active_layer_val = "None"

            self.saved_state = {
                "take_name": take_name,
                "take_index": take_index,
                "selected_effector": selected_effector or "None",
                "active_layer": active_layer_val,
                "current_frame": current_frame
            }


            print("✅ Saved State:", self.saved_state)  # Debug log




    def restore_saved_state():        
        # Restore the original take by name.
        original_take_name = saved_state.get("take_name", None)
        if original_take_name:
            for t in system.Scene.Takes:
                if t.Name == original_take_name:
                    system.CurrentTake = t
                    break
            else:
                print("Original take not found; it may have been renamed or deleted.")
        
        # Now restore active layer
        current_take = system.CurrentTake
        if current_take and "active_layer" in saved_state:
            try:
                current_layer_index = int(saved_state["active_layer"])
                # Try using a setter method or property (depending on your SDK version)
                try:
                    current_take.SetCurrentLayer(current_layer_index)
                except AttributeError:
                    current_take.CurrentLayer = current_layer_index
            except Exception as e:
                print("Error restoring active layer:", e)
        
        # Restore current frame
        if "current_frame" in saved_state:
            try:
                frame = int(saved_state["current_frame"])
                time = pyfbsdk.FBTime(0, 0, frame)
                pyfbsdk.FBPlayerControl().Goto(time)
            except Exception as e:
                print("Error restoring current frame:", e)
        
        # Restore selected effector
        if "selected_effector" in saved_state:
            desired_effector = saved_state["selected_effector"]
            for comp in system.Scene.Components:
                if hasattr(comp, "LongName"):
                    comp.Selected = (comp.LongName == desired_effector)











    def safe_get_text(self, widget):
        """Safely gets text from a widget, handling both QLineEdit and QComboBox."""
        try:
            if isinstance(widget, QtWidgets.QLineEdit):
                return widget.text().strip()
            elif isinstance(widget, QtWidgets.QComboBox):
                return widget.currentText().strip()
            return ""  # Default case if widget type is unknown
        except RuntimeError:
            return ""






    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_position and event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()




        

    
    def toggleSettingsPanel(self):
        if not hasattr(self, "settings_panel"):
            self.settings_panel = SettingsPanel(self)
        self.settings_panel.adjustSize()  # Force size calculation
        button_pos = self.settings_button.mapToGlobal(QtCore.QPoint(0, 0))
        self.settings_panel.move(button_pos.x() - self.settings_panel.width(), button_pos.y())
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
        else:
            self.settings_panel.show()



    
    def updateDropdownFromIndex(self, text, index_input, dropdown, *args):
        """Update the dropdown selection based on index input.
        If a number greater than the maximum is entered, reset to maximum and print a message."""
        try:
            value = int(text.strip())
        except ValueError:
            return  # ignore invalid input
        max_index = dropdown.count() - 1
        if value > max_index:
            index_input.setText(str(max_index))
            dropdown.setCurrentIndex(max_index)
            self.output_bar.setText("Maximum functions are: " + str(max_index))
        elif value < 0:
            index_input.setText("0")
            dropdown.setCurrentIndex(0)
            self.output_bar.setText("Index cannot be negative. Resetting to 0.")
        else:
            dropdown.setCurrentIndex(value)

            
    # Event filter to handle focus in/out for name_input
    def eventFilter(self, obj, event):
        if obj == self.name_input:
            if event.type() == QtCore.QEvent.FocusIn:
                # ✅ Restore last entered text instead of "GUI GUI"
                if self.name_input.text() == "GUI GUI":
                    self.name_input.setText(self.last_entered_text)  # Restore last text
                    self.name_input.setStyleSheet("color: white;")  # Set white while editing

            elif event.type() == QtCore.QEvent.FocusOut:
                # ✅ Save the last entered text (only if it's not empty)
                if self.name_input.text().strip():
                    self.last_entered_text = self.name_input.text()  # Store last input for next edit

                # ✅ Reset only the input field, not the Run button
                self.name_input.setText("GUI GUI")
                self.name_input.setStyleSheet(f"color: {self.name_input_color}; font-weight: bold;")  # Keep stored color

        return super().eventFilter(obj, event)






    # Update Run button text live from name_input (if not default)
    def updateRunButtonName(self, text):
        if text and text != "GUI GUI":
            self.run_button.setText(text)


    def toggleUIVisibility(self):
        self.ui_hidden = not self.ui_hidden

        # Hide or show the main UI elements
        for widget in [self.name_input, self.plus_button, self.settings_button,
                    self.dropdown_container_widget, self.close_button]:
            widget.setVisible(not self.ui_hidden)

        if self.ui_hidden:
            self.hide_ui_button.setText("Unhide UI")
            # Shrink the output bar and clear text when UI is hidden
            self.output_bar.setFixedHeight(5)
            self.output_bar.setText("")
        else:
            self.hide_ui_button.setText("Hide UI")
            # Restore normal output bar height and default text when UI is unhidden
            self.output_bar.setFixedHeight(20)
            # Reset the output bar to its default style and text (or leave it as is)
            self.output_bar.setStyleSheet("background-color: #1A1A2E; color: white; font-size: 12px; border: none; margin: 0px; padding: 0px;")
            self.output_bar.setText("Success")
        self.adjustSize()
        self.setFixedWidth(self.width())
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        QtWidgets.QApplication.processEvents()










    # Add a new Action row (Delete button, Dropdown, Input)
    def addDropdownInputRow(self, force_update=True):
        # Create a container widget for the entire action row.
        row_container_widget = QtWidgets.QWidget()
        row_container_layout = QtWidgets.QVBoxLayout(row_container_widget)
        row_container_layout.setContentsMargins(2, 2, 2, 2)
        row_container_layout.setSpacing(2)

        # Add a divider on top of the row.
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.HLine)
        divider.setStyleSheet("color: gray;")
        row_container_layout.addWidget(divider)

        # Create the main horizontal layout for the row.
        main_row_widget = QtWidgets.QWidget()
        main_row_layout = QtWidgets.QHBoxLayout(main_row_widget)
        main_row_layout.setContentsMargins(0, 0, 0, 0)
        main_row_layout.setSpacing(4)

        # Delete button.
        delete_button = QtWidgets.QPushButton("🗑️")
        delete_button.setFixedSize(25, 22)

        # Index input.
        index_input = QtWidgets.QLineEdit()
        index_input.setPlaceholderText("#")
        index_input.setFixedSize(30, 22)
        index_input.setText("0")

        # Function dropdown.
        dropdown = QtWidgets.QComboBox()
        dropdown.setFixedHeight(22)
        dropdown.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        dropdown.addItems([entry["name"] for entry in self.function_definitions])
        for idx, func in enumerate(self.function_definitions):
            dropdown.setItemData(idx, func.get("description", ""), QtCore.Qt.ToolTipRole)
        dropdown.currentIndexChanged.connect(lambda idx: index_input.setText(str(idx)))
        index_input.textChanged.connect(lambda text, inp=index_input, dd=dropdown: self.updateDropdownFromIndex(text, inp, dd))

        # Add the controls to the main row.
        main_row_layout.addWidget(delete_button)
        main_row_layout.addWidget(index_input)
        main_row_layout.addWidget(dropdown, 1)

        # Create a container for input widgets (will hold 1 or 2 widgets side by side).
        inputs_container_widget = QtWidgets.QWidget()
        inputs_container_layout = QtWidgets.QHBoxLayout(inputs_container_widget)
        inputs_container_layout.setContentsMargins(0, 0, 0, 0)
        inputs_container_layout.setSpacing(4)
        main_row_layout.addWidget(inputs_container_widget)

        row_container_layout.addWidget(main_row_widget)
        self.dropdown_input_container.addWidget(row_container_widget)

        # Save references in row_data.
        row_data = {
            "row_container_widget": row_container_widget,
            "delete_btn": delete_button,
            "index_input": index_input,
            "dropdown": dropdown,
            "inputs_container_widget": inputs_container_widget,
            "inputs_container_layout": inputs_container_layout,
            "input_widgets": []  # to hold the actual input widgets
        }
        self.action_rows.append(row_data)

        # Connect signals.
        delete_button.clicked.connect(lambda: self.removeDropdownInputRow(row_data))
        dropdown.currentIndexChanged.connect(lambda: self.updateInputField(row_data))
        dropdown.currentIndexChanged.connect(self.resetNameInput)

        self.updateInputField(row_data)

        if force_update:
            self.adjustSize()
            QtWidgets.QApplication.processEvents()











    def getXMLFilePath(self):
        """Returns a safe file path for saving XML data in the user's Documents folder."""
        documents_folder = os.path.expanduser("~/Documents")
        file_path = os.path.join(documents_folder, "saved_stacks.xml")
        return file_path




    def saveStack(self, stack_name):
        file_path = self.getXMLFilePath()

        # Load or create XML tree
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
            except ET.ParseError:
                print("Error: XML file corrupted. Creating a new one.")
                root = ET.Element("Stacks")
                tree = ET.ElementTree(root)
        else:
            root = ET.Element("Stacks")
            tree = ET.ElementTree(root)

        # Remove existing stack with the same name before saving
        for existing_stack in root.findall("Stack"):
            if existing_stack.get("name") == stack_name:
                root.remove(existing_stack)

        # Create a new stack element
        stack_element = ET.SubElement(root, "Stack", name=stack_name)

        # Iterate over existing action rows
        for row in self.action_rows:
            action_name = row["dropdown"].currentText().strip()
            action_index = row["dropdown"].currentIndex()  # Get dropdown index
            action_value = ""

            if "input" in row and row["input"] is not None:
                action_value = self.safe_get_text(row["input"])
            elif "text_input" in row and row["text_input"] is not None:
                action_value = self.safe_get_text(row["text_input"])
            elif "dropdown_widget" in row and row["dropdown_widget"] is not None:
                try:
                    action_value = row["dropdown_widget"].currentText().strip()
                except RuntimeError:
                    action_value = ""

            # Save both the function name and index
            ET.SubElement(stack_element, "Action", name=action_name, index=str(action_index), value=action_value)

        # Pretty-print and save XML
        ET.indent(root, space="  ", level=0)
        pretty_xml = ET.tostring(root, encoding="unicode")
        pretty_xml = "\n".join([line for line in pretty_xml.split("\n") if line.strip()])

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)

        print(f"✅ Stack '{stack_name}' saved successfully!")        
        self.output_bar.setText(f"Saved Stack: '{stack_name}'" )

        # **REFRESH THE LOAD MENU AFTER SAVING**
        if hasattr(self, "load_popup"):  
            self.load_popup.loadSavedStacks()  # Refresh the saved stacks










    def addActionToStack(self, stack_name, action_name, index, value):
        """ Ensures valid actions are stored without empty fields. """
        if not stack_name or not action_name:  
            return  # ✅ Ignore invalid actions

        if stack_name not in self.stored_stacks:
            self.stored_stacks[stack_name] = []

        self.stored_stacks[stack_name].append({
            "name": action_name,
            "index": index.strip() or None,  # ✅ Avoid empty strings
            "value": value.strip() or None
        })



    def clearAllActions(self):
        """ Removes all existing actions from the UI before loading a new stack. """
        
        # Remove each widget in the action_rows list
        while self.action_rows:
            row_data = self.action_rows.pop()
            if "widget" in row_data and row_data["widget"]:
                row_data["widget"].setParent(None)
                row_data["widget"].deleteLater()
        
        # Also clear the container layout
        while self.dropdown_input_container.count():
            item = self.dropdown_input_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        QtWidgets.QApplication.processEvents()






    def restoreStack(self, stack_name):
        """Loads actions from the XML and restores them into the UI."""
        file_path = r"C:\Users\Documents\saved_stacks.xml"

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            print("⚠️ No saved stacks found.")
            return

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError:
            print("❌ Error: XML file is corrupted!")
            return

        stack_element = next((s for s in root.findall("Stack") if s.get("name") == stack_name), None)

        if not stack_element:
            print(f"❌ Stack '{stack_name}' not found in XML!")
            return

        self.clearAllActions()  # Ensure UI is cleared before loading new actions

        for action_element in stack_element.findall("Action"):
            action_name = action_element.get("name")
            action_index = action_element.get("index", "")
            action_value = action_element.get("value", "")

            # Add action to UI
            self.addActionToUI(action_name, action_index, action_value)

        # ✅ After all actions are added, update input fields to reflect correct types
        for row in self.action_rows:
            row["dropdown"].setCurrentIndex(int(row["index_input"].text()))  # Ensures index is correctly set
            self.updateInputField(row)  # ✅ Force update input field to match dropdown selection

        print(f"✅ Stack '{stack_name}' loaded successfully!")
        self.output_bar.setText(f"Loaded Stack: '{stack_name}'")










    def addActionToUI(self, action_name, action_index="0", action_value=""):
        row_widget = QtWidgets.QWidget()
        row_layout = QtWidgets.QHBoxLayout(row_widget)
        row_layout.setContentsMargins(5, 5, 5, 5)
        row_layout.setSpacing(10)
            
        delete_button = QtWidgets.QPushButton("🗑️")
            
        index_input = QtWidgets.QLineEdit()
        index_input.setPlaceholderText("#")
        index_input.setFixedWidth(30)
        index_input.setFixedHeight(22)
        index_input.setText(action_index)
            
        dropdown = QtWidgets.QComboBox()
        dropdown.addItems([entry["name"] for entry in self.function_definitions])
        dropdown.setCurrentText(action_name)
            
        input_container = QtWidgets.QStackedWidget()
        input_container.setFixedHeight(22)
            
        input_field = QtWidgets.QLineEdit()
        input_field.setPlaceholderText("Enter value here...")
        input_field.setText(action_value)
        input_container.addWidget(input_field)
            
        row_layout.addWidget(delete_button)
        row_layout.addWidget(index_input)
        row_layout.addWidget(dropdown)
        row_layout.addWidget(input_container)
            
        self.dropdown_input_container.addWidget(row_widget)
            
        row_data = {
            "widget": row_widget,
            "layout": row_layout,
            "delete_btn": delete_button,
            "index_input": index_input,
            "dropdown": dropdown,
            "input_container": input_container,
            "input": input_field,
            "saved_value": action_value
        }

        self.action_rows.append(row_data)
        
        # Set up the connections for index synchronization
        dropdown.currentIndexChanged.connect(lambda index: index_input.setText(str(index)))
        index_input.textChanged.connect(lambda text, inp=index_input, dd=dropdown: self.updateDropdownFromIndex(text, inp, dd))
        
        dropdown.currentIndexChanged.connect(lambda: self.updateInputField(row_data))
        delete_button.clicked.connect(lambda: self.removeDropdownInputRow(row_data))
        
        print(f"✅ Action '{action_name}' added to UI successfully!")










    # Remove an action row
    def removeDropdownInputRow(self, row_data):
        """Removes a row and updates the UI height dynamically."""
        if row_data in self.action_rows:
            self.action_rows.remove(row_data)
            # Remove all widgets in the row and delete them
            for key, widget in row_data.items():
                if isinstance(widget, QtWidgets.QWidget):
                    widget.setParent(None)
                    widget.deleteLater()
            # Force the layout to update its geometry
            self.adjustSize()
            self.updateGeometry()
            self.resize(self.sizeHint())

            # If the UI is unhidden, remove any fixed height so the window can shrink
            if not self.ui_hidden:
                # Remove fixed height by allowing the height to be determined by the layout
                self.setMinimumHeight(0)
                self.setMaximumHeight(16777215)
                # Optionally, you can also update the widget’s size policy
                self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
                # And then force an update so the new size is applied
                self.updateGeometry()
                self.adjustSize()
            else:
                # When hidden, fix the height to the compressed size
                self.setFixedHeight(self.sizeHint().height())
        QtWidgets.QApplication.processEvents()










    def adjustOutputBar(self, event=None):
        gap = 5  # gap between the run buttons and output bar
        self.output_bar.setFixedWidth(self.width())
        self.output_bar.move(0, self.height() - self.output_bar.height() - gap)


    
    def runAllActions(self):
        self.save_current_state()  # Save state before executing actions
        base_style = "background-color: #1A1A2E; border: none; margin: 0px; padding: 0px; font-size: 12px;"
        
        if self.ui_hidden:
            self.output_bar.setStyleSheet(base_style)
            self.output_bar.setText("")
        else:
            self.output_bar.setStyleSheet(base_style + " color: white;")
            self.output_bar.setText("Running actions...")
        
        success = True
        warnings = []
        log_messages = []

        for row in self.action_rows:
            friendly_name = row["dropdown"].currentText().strip()
            func_def = next((f for f in self.function_definitions if f["name"] == friendly_name), None)
            if func_def is None:
                warnings.append(f"No function definition found for '{friendly_name}'")
                continue
            lookup_key = func_def["definition"].strip()
            action_func = actionsList.ACTION_FUNCTIONS.get(lookup_key)
            if action_func is None:
                warnings.append(f"No function found for key '{lookup_key}'")
                continue
            try:
                # Gather input values based on whether there are multiple inputs or a single one.
                if "input_widgets" in row and row["input_widgets"]:
                    input_values = []
                    for widget in row["input_widgets"]:
                        if isinstance(widget, QtWidgets.QLineEdit):
                            input_values.append(widget.text().strip())
                        elif isinstance(widget, QtWidgets.QComboBox):
                            input_values.append(widget.currentText().strip())
                    result = action_func(*input_values)
                elif "input" in row and row["input"] is not None:
                    input_value = row["input"].text().strip()
                    result = action_func(input_value) if input_value else action_func()
                else:
                    result = action_func()

                if result is not None:
                    log_messages.append(str(result))
            except Exception as e:
                success = False
                row["widget"].setStyleSheet("background-color: rgba(255, 0, 0, 100);")
                if self.ui_hidden:
                    self.output_bar.setStyleSheet("background-color: red;")
                    self.output_bar.setText("")
                else:
                    self.output_bar.setStyleSheet(base_style + " color: red;")
                    self.output_bar.setText(f"Error in {friendly_name}: {str(e)}")
                return

        if warnings:
            if self.ui_hidden:
                self.output_bar.setStyleSheet("background-color: yellow;")
                self.output_bar.setText("")
            else:
                self.output_bar.setStyleSheet(base_style + " color: yellow;")
                self.output_bar.setText(" | ".join(warnings))
        elif success:
            if self.ui_hidden:
                self.output_bar.setStyleSheet("background-color: green;")
                self.output_bar.setText("")
            else:
                self.output_bar.setStyleSheet(base_style + " color: green;")
                output_text = "\n".join(log_messages) if log_messages else "Success"
                self.output_bar.setText(output_text)


    restore_saved_state() 














class LoadStackPopup(QtWidgets.QFrame):
    def __init__(self, parent_logic=None):  # Accept parent
        super().__init__(
            None,
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Popup |
            QtCore.Qt.WindowStaysOnTopHint
        )
        self.parent_logic = parent_logic  # Store reference to GUIGUI

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 200);
                border: 1px solid #555;
                border-radius: 5px;
            }
            QLabel {
                font-size: 12px;
                color: white;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: red;
                border-radius: 2px;  # Make buttons sharper
                padding: 2px;
            }
            QPushButton:hover {
                color: #ff5555;
            }
        """)

        self.setMinimumWidth(250)  # Widen the pop-up
        self.setMaximumHeight(8 * 35)  # Adjust height for more items

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.scroll_area)

        self.list_container = QtWidgets.QWidget()
        self.list_layout = QtWidgets.QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(2, 2, 2, 2)
        self.list_layout.setSpacing(4)
        self.scroll_area.setWidget(self.list_container)

        self.loadSavedStacks()





    def loadSavedStacks(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for stack_name in self.getSavedStacks():
            item = self.createStackItem(stack_name)  # Now this function exists
            self.list_layout.addWidget(item)
        self.list_layout.addStretch()

    def createStackItem(self, stack_name):
        item_widget = QtWidgets.QWidget()
        hlayout = QtWidgets.QHBoxLayout(item_widget)
        hlayout.setContentsMargins(4, 4, 4, 4)
        hlayout.setSpacing(6)
        
        # Label for the stack name
        label = QtWidgets.QLabel(stack_name)
        label.setStyleSheet("color: white; font-weight: bold;")
        hlayout.addWidget(label)
        
        # Duplicate button
        duplicate_button = QtWidgets.QPushButton("Dup")
        duplicate_button.setFixedSize(30, 30)
        duplicate_button.setStyleSheet("background-color: transparent; color: lightblue;")
        duplicate_button.clicked.connect(lambda: self.duplicateStack(stack_name))
        hlayout.addWidget(duplicate_button)
        
        # Delete button
        delete_button = QtWidgets.QPushButton("Del")
        delete_button.setFixedSize(30, 30)
        delete_button.setStyleSheet("background-color: transparent; color: red;")
        delete_button.clicked.connect(lambda: self.deleteStack(stack_name))
        hlayout.addWidget(delete_button)
        
        # Clicking the label will also restore the stack.
        label.mousePressEvent = lambda event: self.restoreStack(stack_name)
        
        return item_widget

    def duplicateStack(self, stack_name):
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Duplicate Stack", "Enter new name for duplicated stack:")
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        file_path = r"C:\Users\Documents\saved_stacks.xml"
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            stack_node = next((s for s in root.findall("Stack") if s.get("name") == stack_name), None)
            if stack_node is None:
                QtWidgets.QMessageBox.warning(self, "Error", f"Stack '{stack_name}' not found.")
                return
            # Create a duplicate element with new name.
            new_stack = ET.Element("Stack", name=new_name)
            for child in stack_node:
                new_stack.append(child)
            root.append(new_stack)
            ET.indent(root, space="  ", level=0)
            new_xml = ET.tostring(root, encoding="unicode")
            new_xml = "\n".join([line for line in new_xml.split("\n") if line.strip()])
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_xml)
            QtWidgets.QMessageBox.information(self, "Success", f"Stack '{stack_name}' duplicated as '{new_name}'.")
            self.loadSavedStacks()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error duplicating stack:\n{e}")



    def restoreStack(self, stack_name):
        """Ensure index updates properly when loading any stack."""
        if self.parent_logic and hasattr(self.parent_logic, "restoreStack"):
            self.parent_logic.restoreStack(stack_name)
            for row in self.parent_logic.action_rows:
                row["index_input"].setText(str(row["dropdown"].currentIndex()))
            print(f"✅ Stack '{stack_name}' loaded successfully!")

            self.hide()

            if hasattr(self.parent_logic, "settings_panel") and self.parent_logic.settings_panel:
                self.parent_logic.settings_panel.hide()

        else:
            print(f"❌ ERROR: Parent does not have restoreStack! Stack '{stack_name}' not loaded.")





    def getSavedStacks(self):
        stacks = []
        file_path = r"C:\Users\Documents\saved_stacks.xml"
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                for stack in root.findall("Stack"):
                    name = stack.get("name")
                    if name:
                        stacks.append(name)
            except Exception as e:
                print("Error loading XML:", e)
        return stacks

    def deleteStack(self, stack_name):
        file_path = r"C:\UsersDocuments\saved_stacks.xml"
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                for stack in root.findall("Stack"):
                    if stack.get("name") == stack_name:
                        root.remove(stack)

                xml_str = ET.tostring(root, encoding="utf-8")
                dom = xml.dom.minidom.parseString(xml_str)
                pretty_xml = dom.toprettyxml(indent="  ")
                pretty_xml = "\n".join([line for line in pretty_xml.split("\n") if line.strip()])

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(pretty_xml)
            except Exception as e:
                print("Error deleting stack:", e)
        self.loadSavedStacks()





class SettingsPanel(QtWidgets.QWidget):
    def __init__(self, parent_logic=None):
        super().__init__(parent_logic)
        self.parent_logic = parent_logic 
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Popup)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.save_stack_button = QtWidgets.QPushButton("💾")
        self.save_stack_button.setFixedSize(30, 30)
        self.save_stack_button.clicked.connect(self.promptSaveStack)
        layout.addWidget(self.save_stack_button)

        self.load_stack_button = QtWidgets.QPushButton("📂")
        self.load_stack_button.setFixedSize(30, 30)
        layout.addWidget(self.load_stack_button)

        # Replace the close button with an "Add Function" button.
        self.add_function_button = QtWidgets.QPushButton("➕")
        self.add_function_button.setFixedSize(30, 30)
        # When clicked, this button will open the XML Creator popup.
        self.add_function_button.clicked.connect(lambda: self.launchXMLCreatorPopup())
        layout.addWidget(self.add_function_button)


        # Pass parent to LoadStackPopup so it can call restoreStack
        self.load_popup = LoadStackPopup(self.parent_logic)

        self.load_stack_button.clicked.connect(self.showLoadPopup)

        def launchXMLCreatorPopup(self):
            # Import and launch the XML creator popup.
            # Adjust the import path if needed.
            launch_xml_creator()


    def launchXMLCreatorPopup(self):
        from xmlcreator import launch_xml_creator
        launch_xml_creator()
        

    def promptSaveStack(self):
        """Uses Run button name as the stack name, or asks for a name if it's 'Run'."""
        run_button_name = self.parent_logic.run_button.text().strip()

        if run_button_name.lower() == "run":
            # If name is "Run", ask the user
            stack_name, ok = QtWidgets.QInputDialog.getText(
                self, "Save Stack", "Enter stack name:"
            )
            if not ok or not stack_name.strip():
                return  # Cancelled, do nothing
            stack_name = stack_name.strip()
        else:
            # Use Run button name directly
            stack_name = run_button_name

        self.parent_logic.saveStack(stack_name)



    def showLoadPopup(self):
        """Show the load popup adjacent to the load button."""
        global_pos = self.load_stack_button.mapToGlobal(QtCore.QPoint(0, 0))

        # Position the popup to the left of the load button
        x = global_pos.x() - self.load_popup.width()
        y = global_pos.y()
        self.load_popup.move(x, y)
        self.load_popup.show()

    def eventFilter(self, source, event):
        if source == self.load_stack_button:
            if event.type() == QtCore.QEvent.Enter:
                pos = self.load_stack_button.mapToGlobal(QtCore.QPoint(-self.load_popup.width(), 0))
                self.load_popup.move(pos)
                self.load_popup.show()
            elif event.type() == QtCore.QEvent.Leave:
                QtCore.QTimer.singleShot(300, self.hideLoadPopup)
        return super(SettingsPanel, self).eventFilter(source, event)

    def hideLoadPopup(self):
        if not self.load_popup.underMouse():
            self.load_popup.hide()

            
   

# Create and show the tool as a standalone window
tool = GUIGUI()
tool.show()
