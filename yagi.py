import argparse
import readline
import subprocess
import re
import sys
import os
from pprint import pprint
import signal
from operator import itemgetter, attrgetter
import yaml


conf_location = 'commands.yaml'

command_dict = {}
command_defaults = {}
history = {}

def loadConfig():
    global conf_location
    global command_dict
    global command_defaults
    
    with open(conf_location) as fh:
        try:
            #Load commands and defaults
            conf = yaml.safe_load(fh)
            command_defaults = conf['defaults']
            command_dict.update(conf['commands'])
            command_dict.update(conf['command_groups'])
            command_dict.update(conf['utils'])

        except yaml.YAMLError as err:
            print('There was an error opening the command configuration file: ' + err)
            exit(1)
    
def showHelpScreen():
    global command_dict
    group_idx = {}
    help = {}

    #Gather all of the help keys and defs
    for g in command_dict:
        group_idx[g] =  command_dict[g]['group']

    group_idx = sorted(group_idx.items(), key=itemgetter(1))
    
    group = 'alias' #our first group. What do we do if a user defines a different first group?
    group_count = 0
    for command in group_idx:

        if(group != command_dict[command[0]]['group']):
            group = command_dict[command[0]]['group']
            group_count = 0
        

        if(group_count == 0):
            print(f"=============={group} commands ===============")
        
        print(f"{command_dict[command[0]]['help']['key']:20} {command_dict[command[0]]['help']['def']}")

        group_count += 1
    print("Type quit or exit to exit gamu")
    print("\n")


def formatCommand(cmd):
    global command_dict
    command = command_dict[cmd]

    
def processCommand(cmd):
    global command_dict
    global history
    
    #lookup command
    if(cmd.lower() == 'quit' or cmd.lower() == 'exit'):
        print("Good bye")
        exit(0)

    if(cmd.lower() == 'help'):
        showHelpScreen()
        return
    
    for c in command_dict:
        
        if cmd == command_dict[c]['help']['key']:
            #Execute a defined function
            if 'call_forward' in command_dict[c]:
                current_module = sys.modules[__name__]
                getattr(current_module, command_dict[c]['call_forward'])()
            #Execute a command set
            elif "command_set" in  command_dict[c]:
                for cs in command_dict[c]['command_set']:
                    processCommand(command_dict[cs]['help']['key'])
            #Default to executing a single command. A command set will
            #call these one after another.
            else:
                command = re.split('\s', command_dict[c]['command'])
                idx = 0
                for i in command:
                    prompt = re.search('_(.+)_', i)
                    if prompt:

                        hx_idx = prompt.group(1).replace('_','')
                        prompt = prompt.group(1).replace('_', ' ')
                        if hx_idx in history:
                            prompt = prompt + '(' + history[hx_idx] + ')'

                        ans = input( prompt + ": ")

                        if ans == '' and hx_idx not in history:
                            print('Empty responses not allowed here.')
                            return
                        
                        if ans != '':
                            history[hx_idx] = ans
                        command[idx] = history[hx_idx]
                    idx += 1
                command = ' '.join(command)
                executeGam(command)

def showHistory():
    global history
    print(history)

def resetHistory():
    global history
    print('Resetting history table')
    history = {}
    
def executeGam(command):
    global command_defaults
    ans = input("Execute: 'gam " + command + "'? [y/N]: ")
    if ans.lower() == 'y':
        #execute
        subprocess.call(command_defaults['gam'] + " " + command, shell=True)
        
    else:
        print("Abandoning ship.")
        

if __name__ == "__main__":
    loadConfig()
    print('GamU Commands\n')
    showHelpScreen()
    
    
    while(1):

        command = input('Enter command: ')
        processCommand(command)
    #Loop here
