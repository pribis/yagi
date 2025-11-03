#!/usr/bin/env python
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext
import collections
import sys

from yagi_gui import YagiLogic, run_cli

class CenteredQueryDialog(simpledialog.Dialog):
    """A custom dialog that is centered on its parent."""
    def __init__(self, parent, title, prompt, initialvalue=None):
        self.prompt = prompt
        self.initialvalue = initialvalue
        super().__init__(parent, title)

    def body(self, master):
        self.label = ttk.Label(master, text=self.prompt, justify=tk.LEFT)
        self.label.pack(padx=5, pady=5)
        self.entry = ttk.Entry(master, name="entry")
        if self.initialvalue:
            self.entry.insert(0, self.initialvalue)
            self.entry.select_range(0, tk.END)
        self.entry.pack(padx=5, pady=5)
        return self.entry # initial focus

    def _center_on_parent(self):
        self.update_idletasks()
        parent = self.master
        main_x = parent.winfo_x()
        main_y = parent.winfo_y()
        main_width = parent.winfo_width()
        main_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x_pos = main_x + (main_width - dialog_width) // 2
        y_pos = main_y + (main_height - dialog_height) // 2
        self.geometry(f"+{x_pos}+{y_pos}")

    def buttonbox(self):
        super().buttonbox()
        self.bind("<Return>", self.ok)
        self._center_on_parent()

    def apply(self):
        self.result = self.entry.get()


class YagiGUI(tk.Tk):
    def __init__(self, yagi_logic):
        super().__init__()
        self.yagi = yagi_logic

        # Initialize instance variables
        self.selected_command_key = None

        self.title("YAGI - Yet Another GAM Interface")
        self.geometry("800x600")

        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=3)

        # --- Left side: Command Tree ---
        tree_frame = ttk.LabelFrame(main_frame, text="Commands", padding="10")
        tree_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.populate_command_tree()
        self.tree.bind("<<TreeviewSelect>>", self.on_command_select)

        # --- Right side: Details and Output ---
        details_frame = ttk.LabelFrame(main_frame, text="Details", padding="10")
        details_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 5))
        details_frame.grid_columnconfigure(0, weight=1)

        self.details_label = ttk.Label(details_frame, text="Select a command from the list.", wraplength=400)
        self.details_label.pack(anchor="w")

        self.run_button = ttk.Button(details_frame, text="Run Command", state=tk.DISABLED, command=self.run_command)
        self.run_button.pack(pady=5, anchor="e")

        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=1, column=1, sticky="nsew")
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def populate_command_tree(self):
        grouped_commands = self.yagi.get_grouped_commands()
        # Sort groups alphabetically for consistent order
        sorted_groups = collections.OrderedDict(sorted(grouped_commands.items()))

        for group_name, commands in sorted_groups.items():
            group_id = self.tree.insert("", "end", text=group_name.capitalize(), open=False)
            for command in commands:
                self.tree.insert(group_id, "end", text=command['key'], values=(command['def'], command['key']))

    def on_command_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        # Only leaf nodes (commands) are selectable
        if self.tree.parent(selection[0]):
            command_def, command_key = item['values']
            self.details_label.config(text=f"Description: {command_def}")
            self.run_button.config(state=tk.NORMAL)
            self.selected_command_key = command_key
        else: # It's a group
            self.details_label.config(text="Select a command from the list.")
            self.run_button.config(state=tk.DISABLED)
            self.selected_command_key = None

    def log_output(self, message):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def run_command(self):
        if not self.selected_command_key:
            return

        command_details = self.yagi.get_command_details(self.selected_command_key)
        if not command_details:
            messagebox.showerror("Error", f"Could not find details for command: {self.selected_command_key}")
            return

        self.log_output(f"--- Running: {self.selected_command_key} ---")

        if 'call_forward' in command_details:
            # Special handling for utils
            func_name = command_details['call_forward']
            if func_name == 'resetHistory':
                self.yagi.resetHistory()
                self.log_output("History has been cleared.")
            elif func_name == 'showHistory':
                history_str = str(self.yagi.history)
                self.log_output("Current History:")
                self.log_output(history_str)
            else:
                 self.log_output(f"GUI does not currently support util function: {func_name}")

        elif 'command_set' in command_details:
            for cs_name in command_details['command_set']:
                cs_key = self.yagi.command_dict[cs_name]['help']['key']
                self.selected_command_key = cs_key
                self.run_command() # Recursive call for each command in the set

        elif 'command' in command_details:
            command_template = command_details['command']
            placeholders = self.yagi.get_placeholders(command_template)
            values = {}

            for ph in placeholders:
                prompt = ph.strip('_').replace('_', ' ').capitalize()
                default_val = self.yagi.history.get(ph, '')
                dialog = CenteredQueryDialog(self, "Input Required", f"Enter value for '{prompt}':", initialvalue=default_val)
                user_input = dialog.result

                if user_input is None: # User cancelled
                    self.log_output("Command cancelled by user.")
                    return
                
                values[ph] = user_input
                self.yagi.history[ph] = user_input

            final_command = command_template
            for ph, val in values.items():
                final_command = final_command.replace(ph, val)

            full_gam_command = f"gam {final_command}"
            if messagebox.askyesno("Confirm Execution", f"Execute the following command?\n\n{full_gam_command}"):
                self.log_output(f"Executing: {full_gam_command}")
                self.update_idletasks() # Update GUI before blocking call

                result = self.yagi.execute_gam(final_command, confirmation_prompt=False)
                
                if result:
                    if result.stdout:
                        self.log_output("--- STDOUT ---")
                        self.log_output(result.stdout.strip())
                    if result.stderr:
                        self.log_output("--- STDERR ---")
                        self.log_output(result.stderr.strip())
                    self.log_output(f"--- Process finished with exit code {result.returncode} ---")
                else:
                    self.log_output("Execution failed or was skipped.")
            else:
                self.log_output("Execution cancelled by user.")
        
        self.log_output("-" * (len(self.selected_command_key) + 14) + "\n")


if __name__ == "__main__":
    if '-nw' in sys.argv:
        # Run in CLI mode (No Window)
        try:
            run_cli()
        except KeyboardInterrupt:
            print("\nGood bye")
        except Exception as e:
            print(f"An unexpected error occurred in CLI mode: {e}")
    else:
        # Run in GUI mode (Default)
        try:
            yagi_logic = YagiLogic(conf_location='./commands.yaml')
            app = YagiGUI(yagi_logic)
            app.mainloop()
        except FileNotFoundError:
            messagebox.showerror("Config Error", "Could not find 'commands.yaml'. Please make sure it is in the same directory as the script.")
        except Exception as e:
            messagebox.showerror("Fatal Error", f"An unexpected error occurred: {e}")
