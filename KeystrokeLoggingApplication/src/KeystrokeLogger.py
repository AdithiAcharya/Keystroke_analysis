import tkinter as tk
from tkinter import messagebox
import time
import os
import csv
from dataclasses import dataclass

# A data class to hold press and release times for a single key event.
@dataclass
class TypedKeyObject:
    press_time_ms: int = 0
    release_time_ms: int = 0
    press_time_ns: int = 0
    release_time_ns: int = 0

# Stores a sequence of key events and processes them to extract timing features.
class KeyDataStore:
    def __init__(self):
        self.store: list[TypedKeyObject] = []

    def initialize(self):
        self.store.clear()

    def store_typed_object(self, typed_key_object: TypedKeyObject):
        self.store.append(typed_key_object)

    def get_key(self, index: int) -> TypedKeyObject | None:
        if 0 <= index < len(self.store):
            return self.store[index]
        return None

    def process(self) -> list[float] | None:
        """Calculates Hold, Down-Down, and Up-Down timings in milliseconds."""
        if len(self.store) < 2:
            return None

        strokes = []
        for i in range(len(self.store) - 1):
            current = self.store[i]
            next_key = self.store[i+1]
            key1_hold_time = (current.release_time_ms - current.press_time_ms) / 1000.0
            key1_key2_down_time = (next_key.press_time_ms - current.press_time_ms) / 1000.0
            key1_key2_up_down_time = (next_key.press_time_ms - current.release_time_ms) / 1000.0
            strokes.extend([key1_hold_time, key1_key2_down_time, key1_key2_up_down_time])

        last_key = self.store[-1]
        last_keys_hold_time = (last_key.release_time_ms - last_key.press_time_ms) / 1000.0
        strokes.append(last_keys_hold_time)
        return strokes
    
    def process_in_nano(self) -> list[int] | None:
        """Calculates Hold, Down-Down, and Up-Down timings in nanoseconds."""
        if len(self.store) < 2:
            return None
            
        strokes = []
        for i in range(len(self.store) - 1):
            current = self.store[i]
            next_key = self.store[i+1]
            key1_hold_time = current.release_time_ns - current.press_time_ns
            key1_key2_down_time = next_key.press_time_ns - current.press_time_ns
            key1_key2_up_down_time = next_key.press_time_ns - current.release_time_ns
            strokes.extend([key1_hold_time, key1_key2_down_time, key1_key2_up_down_time])

        last_key = self.store[-1]
        last_keys_hold_time = last_key.release_time_ns - last_key.press_time_ns
        strokes.append(last_keys_hold_time)
        return strokes

# The main GUI application class.
class KeystrokeGuiApp:
    
    # --- Configuration ---
    SAMPLES_PER_USER = 20
    TARGET_PASSWORD = ".tie5Roanl"
    
    # --- UPDATED: Added "target" column to the end of the header ---
    FILE_HEADER = [
        "User", "H.period", "DD.period.t", "UD.period.t", "H.t", "DD.t.i", "UD.t.i", "H.i", 
        "DD.i.e", "UD.i.e", "H.e", "DD.e.five", "UD.e.five", "H.five", "DD.five.Shift.r", 
        "UD.five.Shift.r", "H.Shift.r", "DD.Shift.r.o", "UD.Shift.r.o", "H.o", "DD.o.a", 
        "UD.o.a", "H.a", "DD.a.n", "UD.a.n", "H.n", "DD.n.l", "UD.n.l", "H.l", 
        "DD.l.Return", "UD.l.Return", "H.Return", "target"
    ]
    
    MODIFIER_KEYS = {"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock"}

    def __init__(self, root):
        self.root = root
        self.root.title("Keystroke Data Collector")
        
        self.store = KeyDataStore()
        self.press_index = 0
        self.release_index = 0
        self.sample_counts = {}

        # --- GUI components ---
        tk.Label(root, text="Username:").pack(pady=(10,0))
        self.username_entry = tk.Entry(root, width=50)
        self.username_entry.pack(pady=5)
        self.username_entry.insert(0, "default_user")

        # --- RE-ADDED: Radio buttons for selecting the target label ---
        self.target_var = tk.StringVar(value="Genuine")
        label_frame = tk.Frame(root)
        tk.Label(label_frame, text="Select Target Label:").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(label_frame, text="Genuine", variable=self.target_var, value="Genuine").pack(side=tk.LEFT)
        tk.Radiobutton(label_frame, text="Imposter", variable=self.target_var, value="Imposter").pack(side=tk.LEFT)
        label_frame.pack(pady=5)

        tk.Label(root, text=f"Type the password '{self.TARGET_PASSWORD}' and press Enter:").pack(pady=5)
        self.typing_area = tk.Entry(root, width=50, font=("Courier", 12))
        self.typing_area.pack(pady=5, padx=10)

        self.display_area = tk.Label(root, text="Ready for input.", wraplength=480)
        self.display_area.pack(pady=5)

        self.count_label = tk.Label(root, text="", font=("Helvetica", 10, "italic"), fg="navy")
        self.count_label.pack(pady=5)

        # Bind events
        self.typing_area.bind("<KeyPress>", self.key_pressed)
        self.typing_area.bind("<KeyRelease>", self.key_released)
        self.username_entry.bind("<KeyRelease>", self.update_counter_display)
        
        self.username_entry.focus_set()
        self.update_counter_display()

    def update_counter_display(self, event=None):
        username = self.username_entry.get().strip()
        if username:
            count = self.sample_counts.get(username, 0)
            self.count_label.config(text=f"Samples collected for '{username}': {count} / {self.SAMPLES_PER_USER}")
        else:
            self.count_label.config(text="")

    def _reset_state(self):
        self.typing_area.delete(0, tk.END)
        self.store.initialize()
        self.press_index = 0
        self.release_index = 0

    def key_pressed(self, event):
        if event.keysym in self.MODIFIER_KEYS:
            return

        if event.keysym == "BackSpace":
            self._reset_state()
            self.display_area.config(text="State cleared. Please start over.")
            return

        if event.keysym == "Return":
            username = self.username_entry.get().strip()
            typed_text = self.typing_area.get()
            target_label = self.target_var.get() # Get selected label

            if not username:
                messagebox.showerror("Input Error", "Username cannot be empty.")
                return

            if typed_text == self.TARGET_PASSWORD:
                key_params_ms = self.store.process()
                key_params_ns = self.store.process_in_nano()

                if key_params_ms and key_params_ns:
                    # Pass the label to the CSV generation functions
                    self.generate_csv(key_params_ms, username, target_label)
                    self.generate_csv_in_nano(key_params_ns, username, target_label)
                    
                    self.sample_counts[username] = self.sample_counts.get(username, 0) + 1
                    self.update_counter_display()
                    self.display_area.config(text=f"Sample saved for '{username}' with target '{target_label}'.")
                else:
                    self.display_area.config(text="Not enough keys typed to save a sample.")
            else:
                messagebox.showerror("Input Error", "Password does not match. Please try again.")
                self.display_area.config(text="Incorrect input. Please try again.")

            self._reset_state()
            return
            
        typed_key = TypedKeyObject()
        current_ns = time.time_ns()
        typed_key.press_time_ns = current_ns
        typed_key.press_time_ms = current_ns // 1_000_000
        
        self.store.store_typed_object(typed_key)
        self.press_index += 1

    def key_released(self, event):
        if event.keysym in self.MODIFIER_KEYS or event.keysym in ("BackSpace", "Return"):
            return

        key_object = self.store.get_key(self.release_index)
        if key_object:
            current_ns = time.time_ns()
            key_object.release_time_ns = current_ns
            key_object.release_time_ms = current_ns // 1_000_000
            self.release_index += 1

    # UPDATED: Appends the target label to the end of the row
    def generate_csv(self, key_params: list[float], username: str, target_label: str):
        filename = "Keystrokes.csv"
        file_exists = os.path.isfile(filename)

        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(self.FILE_HEADER)
            writer.writerow([username] + key_params + [target_label])
        print(f"Appended millisecond data to {filename}")

    # UPDATED: Appends the target label to the end of the row
    def generate_csv_in_nano(self, key_params: list[int], username: str, target_label: str):
        filename = "KeystrokesInNano.csv"
        file_exists = os.path.isfile(filename)

        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(self.FILE_HEADER)
            writer.writerow([username] + key_params + [target_label])
        print(f"Appended nanosecond data to {filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KeystrokeGuiApp(root)
    root.mainloop()