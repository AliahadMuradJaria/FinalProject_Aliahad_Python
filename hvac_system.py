import tkinter as tk
from tkinter import scrolledtext

# Safe operating bounds
MIN_SAFE_TEMP = 60.0
MAX_SAFE_TEMP = 85.0
CRITICAL_TEMP = 90.0

def parse_telemetry(raw_string):
    """Parses 'ZONE-01:TEMP=78.5:OCC=1, ZONE-02:TEMP=65.0:OCC=0' into a list of dicts."""
    zones = []
    records = raw_string.split(",")

    for record in records:
        record = record.strip()
        if not record:
            continue
        try:
            parts = record.split(":")
            zone_id = parts[0]
            temp_str = parts[1].split("=")[1]
            occ_str = parts[2].split("=")[1]

            zone_dict = {
                "id": zone_id,
                "temp": float(temp_str),
                "occupied": bool(int(occ_str))
            }
            zones.append(zone_dict)
        except (IndexError, ValueError):
            print(f"Skipping malformed record: {record}")

    return zones

def calculate_zone_average(zone_list):
    if not zone_list:
        return 0.0
    total = 0.0
    for zone in zone_list:
        total += zone["temp"]
    return total / len(zone_list)

def get_last_reading(zone_list):
    if not zone_list:
        return None
    return zone_list[-1]  

def determine_mode(avg_temp, target_temp=72.0, eco_mode=False):
    if eco_mode:
        return "ECO"
    elif avg_temp >= CRITICAL_TEMP:
        return "CRITICAL_ALERT"
    elif avg_temp > target_temp:
        return "COOLING"
    elif avg_temp < target_temp:
        return "HEATING"
    else:
        return "ECO"

def apply_mode_action(mode):
    match mode:
        case "HEATING":
            return "System engaging HEATING mode."
        case "COOLING":
            return "System engaging COOLING mode."
        case "ECO":
            return "System running in ECO mode."
        case "CRITICAL_ALERT":
            return "!!! CRITICAL ALERT: Temperature outside safe bounds !!!"
        case _:
            return "Unknown mode."

def generate_gauge_bar(power_level, max_level=20):
    power_level = max(0, min(power_level, max_level))
    return "[" + ("=" * power_level) + (" " * (max_level - power_level)) + "]"

class HVACControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HVAC Control System")
        self.zones = []  # master list of zone dicts

        # --- Input row ---
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(input_frame, text="Telemetry Input:").pack(side="left")
        self.telemetry_entry = tk.Entry(input_frame, width=60)
        self.telemetry_entry.pack(side="left", padx=5)

        # --- Optional settings row ---
        settings_frame = tk.Frame(root)
        settings_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(settings_frame, text="Target Temp:").pack(side="left")
        self.target_temp_entry = tk.Entry(settings_frame, width=6)
        self.target_temp_entry.insert(0, "72.0")
        self.target_temp_entry.pack(side="left", padx=5)

        self.eco_var = tk.BooleanVar()
        tk.Checkbutton(settings_frame, text="Eco Mode", variable=self.eco_var).pack(side="left", padx=5)

        # --- Button row ---
        button_frame = tk.Frame(root)
        button_frame.pack(padx=10, pady=5, fill="x")

        tk.Button(button_frame, text="Process", command=self.process_input).pack(side="left", padx=5)
        tk.Button(button_frame, text="Analyze", command=self.analyze_zones).pack(side="left", padx=5)
        tk.Button(button_frame, text="Purge", command=self.purge_logs).pack(side="left", padx=5)

        # --- Output box ---
        self.output_box = scrolledtext.ScrolledText(root, width=80, height=25)
        self.output_box.pack(padx=10, pady=10)
    def process_input(self):
        raw_text = self.telemetry_entry.get()
        if not raw_text.strip():
            self.output_box.insert(tk.END, "No telemetry input provided.\n")
            return

        try:
            new_zones = parse_telemetry(raw_text)
            self.zones.extend(new_zones)
            self.output_box.insert(tk.END, f"Processed {len(new_zones)} zone record(s).\n")
        except Exception as e:
            self.output_box.insert(tk.END, f"Error processing input: {e}\n")

        self.telemetry_entry.delete(0, tk.END)

    def analyze_zones(self):
        if not self.zones:
            self.output_box.insert(tk.END, "No zone data to analyze.\n")
            return

        try:
            target_temp = float(self.target_temp_entry.get())
        except ValueError:
            target_temp = 72.0
            self.output_box.insert(tk.END, "Invalid target temp, using default 72.0.\n")

        eco_mode = self.eco_var.get()

        self.output_box.insert(tk.END, "\n--- ZONE REPORT ---\n")
        for zone in self.zones:
            power_level = int(zone["temp"] / 5)  # scale temp into a bar length
            bar = generate_gauge_bar(power_level)
            occ_status = "OCCUPIED" if zone["occupied"] else "EMPTY"
            self.output_box.insert(
                tk.END,
                f"{zone['id']}: {zone['temp']}°F [{occ_status}] {bar}\n"
            )

        avg_temp = calculate_zone_average(self.zones)
        mode = determine_mode(avg_temp, target_temp=target_temp, eco_mode=eco_mode)
        action_msg = apply_mode_action(mode)

        last_zone = get_last_reading(self.zones)

        self.output_box.insert(tk.END, f"\nAverage Temp: {avg_temp:.1f}°F\n")
        self.output_box.insert(tk.END, f"Mode: {mode}\n")
        self.output_box.insert(tk.END, f"{action_msg}\n")
        self.output_box.insert(tk.END, f"Last Reported Zone: {last_zone['id']}\n")
        self.output_box.insert(tk.END, "--------------------\n\n")

    def purge_logs(self):
        self.zones = []
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, "All zone logs purged.\n")    

def main():
    root = tk.Tk()
    app = HVACControlApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()