import dearpygui.dearpygui as dpg
import requests
import threading
import time
import socket
import struct
import numpy as np

API_URL = "http://127.0.0.1:8080/api"

# --- THEME CONSTANTS ---
BG_COLOR = [5, 7, 12, 255]
PANEL_COLOR = [10, 15, 26, 255]
BORDER_COLOR = [255, 255, 255, 40]
PRIMARY = [0, 255, 194, 255]      # Cyber-green
CYAN = [0, 212, 255, 255]         # Cyber-cyan
AMBER = [255, 184, 0, 255]        # Warning
MAGENTA = [255, 61, 240, 255]     # Neural
RED = [255, 56, 96, 255]          # Error
TEXT = [210, 215, 225, 255]

dpg.create_context()

def setup_theme():
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, PANEL_COLOR)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, BG_COLOR)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, BG_COLOR)
            dpg.add_theme_color(dpg.mvThemeCol_Border, BORDER_COLOR)
            dpg.add_theme_color(dpg.mvThemeCol_Button, [20, 30, 45, 255])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, CYAN)
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, BG_COLOR)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, PRIMARY)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, PANEL_COLOR)
            
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 0)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 0)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
            
    dpg.bind_theme(global_theme)

def fetch_telemetry():
    while True:
        try:
            res = requests.get(f"{API_URL}/health", timeout=1)
            if res.status_code == 200:
                dpg.set_value("status_txt", f"[ LIVE ] GPU: 42% | Mem: 12GB | Sync: OK")
                dpg.configure_item("status_txt", color=PRIMARY)
            else:
                raise Exception
        except:
            dpg.set_value("status_txt", f"[ OFFLINE ] Mocking Data")
            dpg.configure_item("status_txt", color=AMBER)
        time.sleep(2)

def receive_frames():
    width, height = 0, 0
    texture_created = False
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', 8081))
            while True:
                header = client.recv(12)
                if len(header) < 12: break
                size, w, h = struct.unpack("<LII", header)
                
                data = bytearray()
                while len(data) < size:
                    packet = client.recv(min(65536, size - len(data)))
                    if not packet: break
                    data.extend(packet)
                    
                if len(data) == size:
                    # Panda3D RGBA to Float array for DearPyGui
                    arr = np.frombuffer(data, dtype=np.uint8).astype(np.float32) / 255.0
                    arr = arr.reshape((h, w, 4))
                    arr = np.flipud(arr).flatten() # Flip vertical

                    if not texture_created or w != width or h != height:
                        width, height = w, h
                        if dpg.does_item_exist("viewport_texture"):
                            dpg.delete_item("viewport_texture")
                        if dpg.does_item_exist("viewport_image"):
                            dpg.delete_item("viewport_image")
                        with dpg.texture_registry():
                            dpg.add_dynamic_texture(width, height, arr, tag="viewport_texture")
                        dpg.add_image("viewport_texture", parent="viewport_container", tag="viewport_image", width=-1, height=-1)
                        texture_created = True
                    else:
                        dpg.set_value("viewport_texture", arr)
        except:
            time.sleep(1)

def log_msg(msg, color=TEXT):
    dpg.add_text(f"> {msg}", color=color, parent="console_window")

def command_callback(sender, app_data):
    cmd = dpg.get_value(sender)
    log_msg(f"CMD: {cmd}", CYAN)
    dpg.set_value(sender, "")
    try:
        requests.post(f"{API_URL}/command", json={"text": cmd}, timeout=1)
    except:
        pass

def btn_play(): log_msg("Simulation PLAY", PRIMARY)
def btn_pause(): log_msg("Simulation PAUSE", AMBER)
def btn_stop(): log_msg("Simulation STOP", RED)

# --- UI LAYOUT ---
with dpg.window(tag="Primary Window"):
    # TOP BAR
    with dpg.group(horizontal=True):
        dpg.add_text(" ┌ FARS OMNIVERSE STUDIO ┐ ", color=PRIMARY)
        dpg.add_button(label=" [ ⏵ ] ", callback=btn_play)
        dpg.add_button(label=" [ ⏸ ] ", callback=btn_pause)
        dpg.add_button(label=" [ ⏹ ] ", callback=btn_stop)
        dpg.add_text(" | CLOCK: 00:00:00 | ")
        dpg.add_text("[ OFFLINE ]", tag="status_txt", color=AMBER)

    dpg.add_separator()

    # MAIN SPLIT
    with dpg.group(horizontal=True):
        # LEFT RAIL
        with dpg.child_window(width=100, border=True):
            dpg.add_button(label="SCENE", width=-1)
            dpg.add_button(label="ASSETS", width=-1)
            dpg.add_button(label="TRAIN", width=-1)
            dpg.add_button(label="DEPLOY", width=-1)
            dpg.add_button(label="ANALYTICS", width=-1)

        # CENTER VIEWPORT PLACEHOLDER
        with dpg.child_window(width=-300, border=True, tag="viewport_container"):
            dpg.add_text("[ 3D VIEWPORT LIVE STREAM ]\nWaiting for Ursina Engine...", color=CYAN, tag="viewport_placeholder")

        # RIGHT PANEL
        with dpg.child_window(width=300, border=True):
            with dpg.tab_bar():
                with dpg.tab(label="OUTLINER"):
                    dpg.add_tree_node(label="World")
                    dpg.add_tree_node(label="|- Zones")
                    with dpg.tree_node(label="|- Robots"):
                        dpg.add_selectable(label="[R1] MedicBot")
                        dpg.add_selectable(label="[R2] SecurityBot")
                with dpg.tab(label="INSPECTOR"):
                    dpg.add_text("Transform", color=PRIMARY)
                    dpg.add_input_floatx(label="Pos", size=3, default_value=[0, 0, 0])
                    dpg.add_input_floatx(label="Rot", size=3, default_value=[0, 0, 0])
                    dpg.add_separator()
                    dpg.add_text("AI Policy", color=MAGENTA)
                    dpg.add_combo(items=["SAC-24hr", "PPO-Walk", "Manual"], default_value="SAC-24hr")

    # BOTTOM PANEL
    with dpg.child_window(height=200, border=True):
        with dpg.tab_bar():
            with dpg.tab(label="CONSOLE"):
                with dpg.child_window(tag="console_window", height=-30, border=False):
                    log_msg("FARS Omniverse Boot Sequence Initiated...", PRIMARY)
                dpg.add_input_text(hint="Ask the Digital Twin (LLM Command)...", width=-1, on_enter=True, callback=command_callback)
            with dpg.tab(label="TIMELINE"):
                dpg.add_slider_float(label="Scrubber", max_value=100.0, width=-1)

dpg.create_viewport(title='FARS OMNIVERSE STUDIO', width=1280, height=720)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

setup_theme()

# Start background threads
threading.Thread(target=fetch_telemetry, daemon=True).start()
threading.Thread(target=receive_frames, daemon=True).start()

dpg.start_dearpygui()
dpg.destroy_context()
