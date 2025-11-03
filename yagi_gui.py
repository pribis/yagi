#!/usr/bin/env python
import subprocess
import re
import sys
from operator import itemgetter
import yaml


class YagiLogic:
    def __init__(self, conf_location='./commands.yaml'):
        self.conf_location = conf_location
        self.command_dict = {}
        self.command_defaults = {}
        self.history = {}
        self.load_config()

    def load_config(self):
        try:
            with open(self.conf_location) as fh:
                # Load commands and defaults
                conf = yaml.safe_load(fh)
                self.command_defaults = conf['defaults']
                self.command_dict.update(conf['commands'])
                self.command_dict.update(conf['command_groups'])
                self.command_dict.update(conf['utils'])
        except yaml.YAMLError as err:
            print(f'There was an error opening the command configuration file: {err}')
            exit(1)
        except FileNotFoundError:
            print(f"Configuration file not found at: {self.conf_location}")
            exit(1)

    def get_grouped_commands(self):
        """Returns a dictionary of commands grouped by their 'group' key."""
        groups = {}
        for name, details in self.command_dict.items():
            group = details.get('group', 'misc')
            if group not in groups:
                groups[group] = []
            groups[group].append({
                'name': name,
                'key': details['help']['key'],
                'def': details['help']['def']
            })
        
        # Sort commands within each group by key
        for group in groups:
            groups[group] = sorted(groups[group], key=itemgetter('key'))
            
        return groups

    def show_help_screen(self):
        grouped_commands = self.get_grouped_commands()
        sorted_groups = sorted(grouped_commands.keys())

        for group in sorted_groups:
            print(f"=============={group} commands ===============")
            for command_info in grouped_commands[group]:
                print(f"{command_info['key']:20} {command_info['def']}")
            print() # Add a blank line for spacing

        print("Type quit or exit to exit yagi")
        print("\n")

    def get_command_details(self, command_key):
        for c in self.command_dict:
            if command_key == self.command_dict[c]['help']['key']:
                return self.command_dict[c]
        return None

    def get_placeholders(self, command_text):
        return re.findall('_[a-zA-Z0-9_]+_', command_text)

    def process_command_cli(self, cmd):
        # lookup command
        if cmd.lower() in ('quit', 'exit'):
            print("Good bye")
            exit(0)

        if cmd.lower() == 'help':
            self.show_help_screen()
            return

        command_details = self.get_command_details(cmd)
        if not command_details:
            print(f"Command '{cmd}' not found.")
            return

        # Execute a defined function
        if 'call_forward' in command_details:
            getattr(self, command_details['call_forward'])()
        # Execute a command set
        elif "command_set" in command_details:
            for cs_name in command_details['command_set']:
                cs_key = self.command_dict[cs_name]['help']['key']
                print(f"\n--- Running command: {cs_key} ---")
                self.process_command_cli(cs_key)
        # Default to executing a single command.
        else:
            command_template = command_details['command']
            placeholders = self.get_placeholders(command_template)
            values = {}
            for ph in placeholders:
                if ph in self.history:
                    prompt = f"{ph.replace('_', ' ')} ({self.history[ph]}): "
                else:
                    prompt = f"{ph.replace('_', ' ')}: "

                ans = input(prompt)

                if ans == '' and ph in self.history:
                    values[ph] = self.history[ph]
                elif ans != '':
                    values[ph] = ans
                    self.history[ph] = ans
                else:
                    print('Empty responses not allowed here.')
                    return
            
            final_command = command_template
            for ph, val in values.items():
                final_command = final_command.replace(f'_{ph}_', val)

            self.execute_gam(final_command)

    def showHistory(self):
        print(self.history)

    def resetHistory(self):
        print('Resetting history table')
        self.history = {}

    def execute_gam(self, command, confirmation_prompt=True):
        if confirmation_prompt:
            ans = input(f"Execute: 'gam {command}'? [y/N]: ")
            if ans.lower() != 'y':
                print("Abandoning ship.")
                return None

        full_command = f"{self.command_defaults['gam']} {command}"
        print(f"Executing: {full_command}")
        return subprocess.run(full_command, shell=True, capture_output=True, text=True)


def run_cli():
    yagi = YagiLogic(conf_location='./commands.yaml')
    print('yagi commands\n')
    yagi.show_help_screen()
    while True:
        command = input('Enter command: ')
        yagi.process_command_cli(command)


if __name__ == "__main__":
    run_cli()