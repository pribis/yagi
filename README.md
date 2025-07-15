# YAGI
## Yet Another Gam Interface

### Introduction
YAGI stands for “Yet Another GAM Interface” and is specifically intended as an interface for 
GAM which, in turn, is google’s toolset.  GAM can be used directly, but remembering all of 
the commands and parameters can be onerous. YAGI is intended to make things easier by providing
a menu driven interface to help walk a user through the most common tasks.


I started this project to be included with a sysadmin toolchain I use at a place
I work. It was just a simple way to make things a bit easier for me. Here's
to hoping you find some use for it.


### Setup
YAGI relies on [GAM](https://github.com/GAM-team/GAM/wiki) being installed and set up correctly.
It will *NOT* work otherwise. 

The commands.yaml file has the following sections. You will need to edit the defaults section.
However, the rest of the file will probably work as-is, but feel free to make changes
as you see fit.

#### defaults
gam: the location of your gam installation.
debug: 0 shuts off debugging, 1 turns it on. There isn't much more to it than that.

#### shared_inbox
This array is specific to our company and may or may not be useful to you. Shared inboxes
are simply google accounts accessible by multiple people via delegation.

#### commands
Commands take up the bulk of the configuration and are what YAGI is all about. They have
a specific format you must follow or YAGI will break.

Here is a breakdown for adding an alias to a user's account:

**add_alias:**
name of the command

**help:**
help section used in the help menu

**key: 'add alias'**
the command phrase you will use at the prompt

**def: 'Add an alias to user.'**
explanation of command phrase

**command: 'create alias _email_ user _username_'**
the gam command (see next section)

**group : alias**
where on the help screen to group this command



#### gam command
As shown above, the command sequence has a gam command to execute. The import part are the 
placeholders, specified but a single underscore attached to the beginning and end of the 
word. These become the prompt YAGI will use to gather information from you. For example,
the above command will result in the following prompts:
> email:
> username:

If you want the placeholder to be more informative, do not use spaces, use underscores. 
Ex. _type_your_email_ will produce: 
> type your email.

[NOTE: Use at your own risk. This program is covered under the GNU GPL (v3).]
