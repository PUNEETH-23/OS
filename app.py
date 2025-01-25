import tkinter as tk
from tkinter import messagebox, ttk
import psutil

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        self.is_filter_active = False
        self.filter_value = 0

        # Style updates
        self.style = ttk.Style()
        self.style.configure(
            'TButton',
            font=('Arial', 10),
            width=20,
            relief='flat',
            background='#00ADB5',  # Accent color
            foreground='#212121',  # Light text
        )
        self.style.map(
            'TButton',
            background=[('active', '#007F85')],  # Slightly darker accent
            foreground=[('active', '#EEEEEE')]
        )
        self.style.configure('TLabel', font=('Arial', 12), foreground='#EEEEEE', background='#222831')
        self.style.configure(
            'Treeview',
            font=('Arial', 10),
            rowheight=25,
            background='#393E46',  # Slightly lighter background
            foreground='#EEEEEE',  # Light text
            fieldbackground='#393E46'
        )
        self.style.map('Treeview', background=[('selected', '#00ADB5')], foreground=[('selected', '#222831')])
        self.style.configure('Treeview.Heading', font=('Arial', 11, 'bold'), background='#00ADB5', foreground='#222831')

        # Header label
        header_label = tk.Label(
            self.root,
            text="Windows System Task Manager",
            font=('Arial', 16, 'bold'),
            bg='#00ADB5',  # Accent color
            fg='#222831',  # Dark text
            pady=10
        )
        header_label.pack(fill='both')

        # Treeview with Scrollbar
        tree_frame = tk.Frame(self.root, bg='#222831')  # Dark background
        tree_frame.pack(padx=10, pady=10, fill='both', expand=True)

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll.pack(side="right", fill="y")

        self.process_tree = ttk.Treeview(
            tree_frame,
            columns=("PID", "Name", "CPU", "Memory"),
            show="headings",
            height=20,
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.process_tree.yview)

        # Configure Treeview columns
        self.process_tree.heading("PID", text="PID", command=lambda: self.sort_column("PID"))
        self.process_tree.heading("Name", text="Process Name", command=lambda: self.sort_column("Name"))
        self.process_tree.heading("CPU", text="CPU Usage (%)", command=lambda: self.sort_column("CPU"))
        self.process_tree.heading("Memory", text="Memory Usage (%)", command=lambda: self.sort_column("Memory"))
        self.process_tree.column("PID", width=100, anchor="center")
        self.process_tree.column("Name", width=200, anchor="w")
        self.process_tree.column("CPU", width=150, anchor="center")
        self.process_tree.column("Memory", width=150, anchor="center")
        self.process_tree.pack(fill='both', expand=True)

        # Buttons and Input Fields
        button_frame = tk.Frame(self.root, bg="#222831")  # Dark background
        button_frame.pack(pady=10, fill='x')

        self.refresh_button = ttk.Button(button_frame, text="Refresh", command=self.refresh_process_list)
        self.refresh_button.grid(row=0, column=0, padx=10)

        self.kill_button = ttk.Button(button_frame, text="Kill Process", command=self.kill_process)
        self.kill_button.grid(row=0, column=1, padx=10)

        self.search_label = ttk.Label(button_frame, text="Search:")
        self.search_label.grid(row=0, column=2, padx=10)
        self.search_entry = ttk.Entry(button_frame)
        self.search_entry.grid(row=0, column=3, padx=10)
        self.search_button = ttk.Button(button_frame, text="Search", command=self.search_process)
        self.search_button.grid(row=0, column=4, padx=10)

        self.filter_label = ttk.Label(button_frame, text="Filter by CPU >")
        self.filter_label.grid(row=1, column=0, padx=10, pady=5)
        self.filter_entry = ttk.Entry(button_frame)
        self.filter_entry.grid(row=1, column=1, padx=10, pady=5)
        self.filter_button = ttk.Button(button_frame, text="Apply Filter", command=self.apply_filter)
        self.filter_button.grid(row=1, column=2, padx=10, pady=5)

        self.refresh_process_list()

    def refresh_process_list(self):
        for row in self.process_tree.get_children():
            self.process_tree.delete(row)

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                self.process_tree.insert("", "end", values=(info['pid'], info['name'], info['cpu_percent'], round(info['memory_percent'], 2)))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if self.is_filter_active:
            self.apply_filter()

        self.root.after(10000, self.refresh_process_list)

    def kill_process(self):
        selected_item = self.process_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a process to kill.")
            return

        pid = self.process_tree.item(selected_item)['values'][0]
        if messagebox.askyesno("Kill Process", f"Are you sure you want to kill the process with PID {pid}?"):
            try:
                psutil.Process(pid).terminate()
                messagebox.showinfo("Success", f"Process with PID {pid} has been terminated.")
                self.refresh_process_list()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                messagebox.showerror("Error", f"Failed to terminate process with PID {pid}.")

    def search_process(self):
        search_term = self.search_entry.get().strip().lower()
        if not search_term:
            messagebox.showwarning("Search", "Please enter a search term.")
            return

        found = False
        for row in self.process_tree.get_children():
            values = self.process_tree.item(row)['values']
            pid = str(values[0])
            process_name = values[1].lower()

            if search_term in process_name or search_term == pid:
                self.process_tree.selection_add(row)
                self.process_tree.see(row)
                found = True

        if not found:
            messagebox.showinfo("Search", "No matching process found.")

    def apply_filter(self):
        filter_value = self.filter_entry.get()
        if not filter_value:
            messagebox.showwarning("Filter", "Please enter a value to filter.")
            return

        try:
            self.filter_value = float(filter_value)
        except ValueError:
            messagebox.showwarning("Filter", "Please enter a valid numeric value.")
            return

        self.is_filter_active = True
        for row in self.process_tree.get_children():
            cpu_usage = float(self.process_tree.item(row)['values'][2])
            if cpu_usage <= self.filter_value:
                self.process_tree.detach(row)

    def sort_column(self, col):
        data = [(self.process_tree.item(item)["values"], item) for item in self.process_tree.get_children("")]
        if col == "PID":
            data.sort(key=lambda x: x[0][0])
        elif col == "Name":
            data.sort(key=lambda x: x[0][1].lower())
        elif col == "CPU":
            data.sort(key=lambda x: x[0][2], reverse=True)
        elif col == "Memory":
            data.sort(key=lambda x: x[0][3], reverse=True)

        for i, (values, item) in enumerate(data):
            self.process_tree.item(item, values=values)

if __name__ == "__main__":
    root = tk.Tk()
    task_manager = TaskManager(root)
    root.mainloop()
