import subprocess
import tkinter as tk
from tkinter import ttk

import psutil

# Dictionary of disk devices and their corresponding mount points
disk_devices = {
    "system": "/",
    # "ramdisk": "/ramdisk",
    # "backup": "/backup"
}

# Dictionary of scripts to clean disk space
clean_scripts = {
    "system": "./clean_system.sh",
    # "ramdisk": "./clean_ramdisk.sh",
    # "backup": "./clean_backup.sh"
}

def trigger_script(script_path, log_window):
    # Enable the log window to allow modifications
    log_window.config(state=tk.NORMAL)

    # Clear the log window before displaying new logs
    log_window.delete("1.0", tk.END)

    # Execute the corresponding Linux script based on the button clicked
    process = subprocess.Popen([script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # Get the output from the script and display it in the log window
    output = stdout.decode("utf-8")
    error_output = stderr.decode("utf-8")

    # Display output in log window
    log_window.insert(tk.END, output)

    # Display error messages in log window
    if error_output:
        log_window.insert(tk.END, error_output)

    # Disable the log window again to prevent modifications
    log_window.config(state=tk.DISABLED)

def clear_log(log_window):
    # Enable the log window to allow modifications
    log_window.config(state=tk.NORMAL)

    # Clear the log window
    log_window.delete("1.0", tk.END)

    # Disable the log window again to prevent modifications
    log_window.config(state=tk.DISABLED)

def copy_to_clipboard(log_window):
    # Get the content of the log window
    content = log_window.get("1.0", tk.END)

    # Copy the content to the clipboard
    log_window.clipboard_clear()
    log_window.clipboard_append(content)

def update_disk_space_labels(progress_bars):
    for device, progress_bar in progress_bars.items():
        # Get disk usage information for the device
        disk_usage = psutil.disk_usage(disk_devices[device])
        used = disk_usage.used
        total = disk_usage.total
        percent = disk_usage.percent

        # Update the progress bar with disk space information
        progress_bar['value'] = percent

# Create the main window
window = tk.Tk()
window.title("TOOLBOX")  # Set the desired window title

# Configure the grid column and row weights
window.grid_columnconfigure(0, weight=1)
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1)
window.grid_rowconfigure(2, weight=0)

# Create a frame for the buttons and titles
frame = tk.Frame(window)
frame.grid(row=0, column=0, padx=10, pady=10, sticky="w")

# Create a log window using the Text widget
log_window = tk.Text(window, height=10, state=tk.DISABLED)
log_window.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

# Create a scrollbar for the log window
scrollbar = tk.Scrollbar(log_window)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_window.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=log_window.yview)

# Dictionary of button texts and script paths grouped by titles
button_script_map = {
    "MAINTENANCE": [
        ("./restart_wrapper.sh", "Restart Wrapper"),
        ("./test2.sh", "test2"),
        ("/path/to/your/script3.sh", "script 3"),
        ("/path/to/your/script4.sh", "script 4"),
        ("/path/to/your/script5.sh", "script 5"),
        ("/path/to/your/script6.sh", "script 6")
    ],
    "INSTALLATION": [
        ("./backup_disk_creation.sh", "Create Backup disk"),
        ("./ramdisk_disk_creation.sh", "Create Ramdisk disk"),
        ("/path/to/your/script9.sh", "script 9"),
        ("/path/to/your/script10.sh", "script 10"),
        ("/path/to/your/script11.sh", "script 11"),
        ("/path/to/your/script12.sh", "script 12")
    ]
    # Add more titles and associated button-text:script-path mappings as needed
}

# Create a grid of buttons using the button-script map
row = 0
for title, buttons in button_script_map.items():
    title_label = tk.Label(frame, text=title, font=("Arial", 14, "bold"))
    title_label.grid(row=row, column=0, columnspan=3, pady=10, sticky="w")
    row += 1

    for index, (script_path, button_text) in enumerate(buttons):
        button = tk.Button(frame, text=button_text, command=lambda script_path=script_path, log=log_window: [clear_log(log), trigger_script(script_path, log)],
                           width=15, height=3)  # Set the desired width and height for the button
        button.grid(row=row, column=index % 3, padx=5, pady=5)

        if (index + 1) % 3 == 0:
            row += 1

    row += 1

# Create a "Copy" button
copy_button = tk.Button(window, text="Copy logs", command=lambda: copy_to_clipboard(log_window))
copy_button.grid(row=row, column=0, pady=10, sticky="w")

# Create labels and buttons for disk space information
progress_bars = {}
clean_buttons = {}
for index, (device, mount_point) in enumerate(disk_devices.items()):
    label = tk.Label(window, text=f"{device.capitalize()}:")
    label.grid(row=row+index+1, column=0, padx=10, pady=5, sticky="w")
    progress_bar = ttk.Progressbar(window, length=200, mode='determinate')
    progress_bar.grid(row=row+index+1, column=1, padx=10, pady=2, sticky="w")
    clean_button = tk.Button(window, text="Clean", command=lambda device=device, log=log_window: [clear_log(log), trigger_script(clean_scripts[device], log)])
    clean_button.grid(row=row+index+1, column=2, padx=10, pady=2, sticky="w")
    progress_bars[device] = progress_bar
    clean_buttons[device] = clean_button

# Update disk space labels and buttons periodically
update_disk_space_labels(progress_bars)
window.after(1000, lambda: update_disk_space_labels(progress_bars))

# Center the window on the screen
window.update_idletasks()
window_width = window.winfo_width()
window_height = window.winfo_height()
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Start the GUI event loop
window.mainloop()
