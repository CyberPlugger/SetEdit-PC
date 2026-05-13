import winreg
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog

# --- Диалог редактирования значения ---
class ValueEditorDialog(simpledialog.Dialog):
    """Диалог для добавления/редактирования значения реестра с темной темой и шрифтом Consolas."""
    def __init__(self, parent, title, value_name=None, value_type=None, value_data="", edit_mode=True):
        self.edit_mode = edit_mode
        self.value_name = value_name
        self.value_type = value_type
        self.value_data_str = value_data
        self.result = None
        super().__init__(parent, title)

    def body(self, parent):
        self.initial_value = self.value_data_str

        tk.Label(parent, text="Name:", bg="#181825", fg="white", font=("Consolas", 11)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.name_entry = tk.Entry(parent, width=40, bg="#45475a", fg="white", font=("Consolas", 11), insertbackground="white")
        if self.value_name:
            self.name_entry.insert(0, self.value_name)
        self.name_entry.config(state="normal" if not self.edit_mode else "readonly")
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(parent, text="Type:", bg="#181825", fg="white", font=("Consolas", 11)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.type_var = tk.StringVar(parent)
        self.type_combobox = ttk.Combobox(parent, textvariable=self.type_var,
                                          values=["REG_SZ", "REG_EXPAND_SZ", "REG_MULTI_SZ", "REG_DWORD", "REG_BINARY"],
                                          state="readonly", font=("Consolas", 11))
        self.type_var.set(self.value_type if self.value_type else "REG_SZ")
        self.type_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.type_combobox.bind("<<ComboboxSelected>>", self.update_data_entry_state)

        tk.Label(parent, text="Data:", bg="#181825", fg="white", font=("Consolas", 11)).grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        self.data_text = tk.Text(parent, height=5, width=40, bg="#45475a", fg="white", font=("Consolas", 11), insertbackground="white")
        self.data_text.insert(tk.END, self.value_data_str)
        self.data_text.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        self.update_data_entry_state()
        return self.name_entry

    def update_data_entry_state(self, event=None):
        selected_type = self.type_var.get()
        self.data_text.config(state="normal")
        self.data_text.delete("1.0", tk.END)

        if selected_type == "REG_DWORD":
            self.data_text.config(height=1)
            try:
                self.data_text.insert(tk.END, str(int(self.initial_value)))
            except:
                self.data_text.insert(tk.END, "0")
        elif selected_type == "REG_BINARY":
            self.data_text.config(height=3)
            if isinstance(self.initial_value, bytes):
                self.data_text.insert(tk.END, ' '.join(f'{b:02X}' for b in self.initial_value))
            else:
                self.data_text.insert(tk.END, str(self.initial_value))
        else:
            self.data_text.config(height=5)
            if selected_type == "REG_MULTI_SZ" and isinstance(self.initial_value, list):
                self.data_text.insert(tk.END, " | ".join(self.initial_value))
            else:
                self.data_text.insert(tk.END, str(self.initial_value))

    def apply(self):
        name = self.name_entry.get().strip()
        type_str = self.type_var.get()
        data = self.data_text.get("1.0", tk.END).strip()
        if not name:
            messagebox.showerror("Error", "Name cannot be empty.", parent=self)
            return
        self.result = (name, type_str, data)
        self.destroy()


# --- Главный класс приложения ---
class SetEditPC:
    def __init__(self, root):
        self.root = root
        self.root.title("👑 SetEdit PC (Unofficial)")
        self.root.configure(bg="#1e1e2e")
        self.current_key_path = r"HKEY_CURRENT_USER"
        self.setup_ui()
        self.load_registry_keys(self.current_key_path)

    def setup_ui(self):
        # --- Информационный текст сверху ---
        info_text = (
            "SetEdit PC (Unofficial)\n"
            "------------------------------------\n"
            "This is a graphical editor of Windows registry.\n"
            "You can view, add, delete and edit the keys and attributes.\n"
            "⚠️ Warning! One mistake and your system can be in danger!\n"
            "Use it on your own risk.\n"
            "Guide:\n"
            " - Select a key\n"
            " - Check the values on the right\n"
            " - Add/Edit/Delete values with the buttons under the treeview.\n"
            "We and the app is not responsible for your consequences."
        )
        tk.Label(self.root, text=info_text, justify="left", bg="#1e1e2e", fg="#fab387", font=("Consolas", 10)).pack(fill="x", padx=5, pady=5)

        # Верхняя панель
        top_frame = tk.Frame(self.root, bg="#181825", pady=5)
        top_frame.pack(fill="x")
        tk.Button(top_frame, text="⬆️ Parent", command=self.go_up_directory, bg="#45475a", fg="white").pack(side="left", padx=5)
        self.path_label = tk.Label(top_frame, text=self.current_key_path, bg="#181825", fg="#cdd6f4", anchor="w")
        self.path_label.pack(fill="x", expand=True, padx=5)

        # Слева: дерево ключей
        self.tree_frame = tk.Frame(self.root, bg="#1e1e2e", width=250)
        self.tree_frame.pack(side="left", fill="y", padx=5, pady=5)
        tk.Label(self.tree_frame, text="Registry Keys", font=("Consolas", 12, "bold"), bg="#1e1e2e", fg="#fab387").pack(pady=5)
        self.keys_listbox = tk.Listbox(self.tree_frame, bg="#313244", fg="#cdd6f4", font=("Consolas", 10), selectbackground="#fab387")
        self.keys_listbox.pack(fill="both", expand=True)
        self.keys_listbox.bind("<<ListboxSelect>>", self.on_key_select)

        # Правая панель: значения + кнопки
        self.values_frame = tk.Frame(self.root, bg="#1e1e2e")
        self.values_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        tk.Label(self.values_frame, text="Registry Values", font=("Consolas", 12, "bold"), bg="#1e1e2e", fg="#fab387").pack(pady=5)

        # Контейнер для Treeview
        tree_container = tk.Frame(self.values_frame, bg="#1e1e2e")
        tree_container.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview", background="#000000", foreground="white", rowheight=25,
                        font=("Consolas", 11), fieldbackground="#000000")
        style.map("Dark.Treeview", background=[("selected", "#4444ff")], foreground=[("selected", "white")])

        self.values_tree = ttk.Treeview(tree_container, columns=("Name", "Type", "Data"), show="headings", style="Dark.Treeview")
        for col, width in [("Name", 200), ("Type", 80), ("Data", 300)]:
            self.values_tree.heading(col, text=col)
            self.values_tree.column(col, width=width, anchor="w" if col != "Type" else "center")
        self.values_tree.tag_configure("evenrow", background="#111111")
        self.values_tree.tag_configure("oddrow", background="#1a1a1a")
        self.values_tree.pack(fill="both", expand=True)
        self.values_tree.bind("<Double-1>", self.on_value_double_click)

        # Кнопки под Treeview
        btn_frame = tk.Frame(self.values_frame, bg="#1e1e2e")
        btn_frame.pack(fill="x", pady=5)
        buttons = [
            ("Add Key", self.add_key, "#a6e3a1", "black"),
            ("Delete Key", self.delete_key, "#f38ba8", "white"),
            ("Add Value", self.add_value, "#89b4fa", "white"),
            ("Edit Value", self.edit_value, "#cba6f7", "white"),
            ("Delete Value", self.delete_registry_value, "#fab387", "black")
        ]
        for text, cmd, bg, fg in buttons:
            tk.Button(btn_frame, text=text, command=cmd, bg=bg, fg=fg).pack(side="left", padx=5, pady=5)

    # --- Методы работы с реестром ---
    def get_registry_keys(self, parent_key_path):
        keys = []
        try:
            root_key_name = parent_key_path.split('\\')[0]
            reg_root = getattr(winreg, root_key_name)
            sub_path = '\\'.join(parent_key_path.split('\\')[1:])
            with winreg.OpenKey(reg_root, sub_path, 0, winreg.KEY_READ | winreg.KEY_ENUMERATE_SUB_KEYS) as key:
                i = 0
                while True:
                    try:
                        keys.append(winreg.EnumKey(key, i))
                        i += 1
                    except OSError:
                        break
        except:
            pass
        return keys

    def get_registry_values(self, parent_key_path):
        values = []
        try:
            root_key_name = parent_key_path.split('\\')[0]
            reg_root = getattr(winreg, root_key_name)
            sub_path = '\\'.join(parent_key_path.split('\\')[1:])
            with winreg.OpenKey(reg_root, sub_path, 0, winreg.KEY_READ | winreg.KEY_QUERY_VALUE) as key:
                i = 0
                while True:
                    try:
                        name, data, type_id = winreg.EnumValue(key, i)
                        type_str = self.get_value_type_str(type_id)
                        values.append((name, type_str, data))
                        i += 1
                    except OSError:
                        break
        except:
            pass
        return values

    def get_value_type_str(self, type_id):
        if type_id == winreg.REG_SZ: return "REG_SZ"
        if type_id == winreg.REG_EXPAND_SZ: return "REG_EXPAND_SZ"
        if type_id == winreg.REG_MULTI_SZ: return "REG_MULTI_SZ"
        if type_id == winreg.REG_DWORD: return "REG_DWORD"
        if type_id == winreg.REG_BINARY: return "REG_BINARY"
        return f"Unknown ({type_id})"

    def load_registry_keys(self, path):
        self.keys_listbox.delete(0, tk.END)
        for key in self.get_registry_keys(path):
            self.keys_listbox.insert(tk.END, key)
        self.path_label.config(text=path)
        self.current_key_path = path
        self.load_registry_values(path)

    def load_registry_values(self, path):
        for item in self.values_tree.get_children():
            self.values_tree.delete(item)
        values = self.get_registry_values(path)
        for i, (name, type_str, data) in enumerate(values):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            display_data = str(data)
            if type_str == "REG_BINARY" and isinstance(data, bytes):
                display_data = ' '.join(f'{b:02X}' for b in data)
            elif type_str == "REG_DWORD":
                try:
                    display_data = f"{data} (0x{int(data):08X})"
                except:
                    display_data = str(data)
            elif type_str == "REG_MULTI_SZ" and isinstance(data, list):
                display_data = " | ".join(data)
            self.values_tree.insert("", tk.END, values=(name, type_str, display_data), tags=(tag,))

    def on_key_select(self, event):
        sel = self.keys_listbox.curselection()
        if sel:
            key_name = self.keys_listbox.get(sel[0])
            self.load_registry_keys(f"{self.current_key_path}\\{key_name}")

    def go_up_directory(self):
        parts = self.current_key_path.split('\\')
        if len(parts) > 1:
            self.load_registry_keys('\\'.join(parts[:-1]))

    def on_value_double_click(self, event):
        item = self.values_tree.focus()
        if item:
            name, type_str, data_str = self.values_tree.item(item, "values")
            self.edit_value_dialog(name, type_str, data_str)

    def add_key(self):
        key_name = simpledialog.askstring("Add Key", "Enter new key name:", parent=self.root)
        if key_name:
            try:
                root_key_name = self.current_key_path.split('\\')[0]
                reg_root = getattr(winreg, root_key_name)
                sub_path = '\\'.join(self.current_key_path.split('\\')[1:])
                new_key_handle = winreg.CreateKey(reg_root, f"{sub_path}\\{key_name}")
                winreg.CloseKey(new_key_handle)
                self.load_registry_keys(self.current_key_path)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_key(self):
        sel = self.keys_listbox.curselection()
        if sel:
            key_name = self.keys_listbox.get(sel[0])
            if messagebox.askyesno("Delete Key", f"Delete '{key_name}'?"):
                try:
                    root_key_name = self.current_key_path.split('\\')[0]
                    reg_root = getattr(winreg, root_key_name)
                    sub_path = '\\'.join(self.current_key_path.split('\\')[1:])
                    winreg.DeleteKey(reg_root, f"{sub_path}\\{key_name}")
                    self.load_registry_keys(self.current_key_path)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

    def add_value(self):
        dialog = ValueEditorDialog(self.root, "Add Registry Value", edit_mode=False)
        if dialog.result:
            name, type_str, data = dialog.result
            self.set_registry_value(name, type_str, data)

    def edit_value_dialog(self, name, type_str, data_str):
        dialog = ValueEditorDialog(self.root, f"Edit Value: {name}", value_name=name, value_type=type_str, value_data=data_str, edit_mode=True)
        if dialog.result:
            new_name, new_type_str, new_data = dialog.result
            self.set_registry_value(new_name, new_type_str, new_data)

    def edit_value(self):
        item = self.values_tree.focus()
        if item:
            name, type_str, data_str = self.values_tree.item(item, "values")
            self.edit_value_dialog(name, type_str, data_str)

    def delete_registry_value(self):
        item = self.values_tree.focus()
        if item:
            name, _, _ = self.values_tree.item(item, "values")
            if messagebox.askyesno("Delete Value", f"Are you sure you want to delete '{name}'?"):
                try:
                    root_key_name = self.current_key_path.split('\\')[0]
                    reg_root = getattr(winreg, root_key_name)
                    sub_path = '\\'.join(self.current_key_path.split('\\')[1:])
                    with winreg.OpenKey(reg_root, sub_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, name)
                    self.load_registry_values(self.current_key_path)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

    def set_registry_value(self, name, type_str, data):
        try:
            root_key_name = self.current_key_path.split('\\')[0]
            reg_root = getattr(winreg, root_key_name)
            sub_path = '\\'.join(self.current_key_path.split('\\')[1:])
            type_map = {"REG_SZ": winreg.REG_SZ, "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
                        "REG_MULTI_SZ": winreg.REG_MULTI_SZ, "REG_DWORD": winreg.REG_DWORD, "REG_BINARY": winreg.REG_BINARY}
            reg_type = type_map[type_str]
            processed_data = data
            if reg_type == winreg.REG_DWORD:
                processed_data = int(data)
            elif reg_type == winreg.REG_BINARY:
                processed_data = bytes.fromhex(data.replace(' ', ''))
            elif reg_type == winreg.REG_MULTI_SZ:
                processed_data = data.split(" | ")
            with winreg.OpenKey(reg_root, sub_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, name, 0, reg_type, processed_data)
            self.load_registry_values(self.current_key_path)
        except Exception as e:
            messagebox.showerror("Error", str(e))


# --- Запуск приложения ---
if __name__ == "__main__":
    root = tk.Tk()
    app = SetEditPC(root)
    root.mainloop()