import sys
import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# import PowerAnimatorScript_QT



# Get the absolute path of the folder containing 'Functions'
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "Functions"))
sys.path.append(parent_dir)
from SaveAs import SaveFile
from Functions import PlotToControlRig, gotostartframe, gotoendframe, create_named_take, remove_all_layers
from CreateNewLayer import create_animation_layer


def play_action(input_value="Default Play Value"):
    print(f"Executing Play with input: {input_value}")

def gtend_action(input_value="Default GtEnd Value"):
    print(f"Executing Fucking Play with input: {input_value}")
    gotoendframe()
    # from PowerAnimatorScript_QT import saved_state
    # PowerAnimatorScript_QT.saved_state["take_name"] = "NewTakeName"

def gtstart_action(input_value="Default GtStart Value"):
    print(f"Executing Fucking Play with input: {input_value}")
    gotostartframe()

def save_as(input_value="Hero is the current frame"):
    SaveFile()
    return f"Played with input: {input_value}"

def plot_ctrl(input_value="Hero is the current frame"):
    PlotToControlRig()


def delete_all_layer(input_value=""):
    print(f"Deleted all layers debug working ")
    remove_all_layers()

def create_empty_take(input_value="NewTake"):
    create_named_take(input_value)

def select_effector():
    print("Effector Selected")

def duplicate_take_suffix(input_value="_OLD"):
    print(f"String input received: {input_value}")

def create_new_layer(input_value):
    create_animation_layer(input_value)
    print("New Layer Created")

# Define a dictionary for easy access in PowerAnimator
ACTION_FUNCTIONS = {
    "Play": play_action,
    "GtEnd": gtend_action,
    "GtStart": gtstart_action,
    "Save_as": save_as,
    "PlotToControlRig": plot_ctrl,
    "Delete Layers": delete_all_layer,
    "Empty Take": create_empty_take,
    "Select Effector": select_effector,
    "DuplicateTake": duplicate_take_suffix,
    "Create New Layer": create_new_layer
}
