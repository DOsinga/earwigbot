# -*- coding: utf-8  -*-

"""
EarwigBot's JSON Config File Parser

This handles all tasks involving reading and writing to our config file,
including encrypting and decrypting passwords and making a new config file from
scratch at the inital bot run.

Usually you'll just want to do "from core import config" and access config data
from within config's four global variables and one function:

* config.components  - a list of enabled components
* config.wiki        - a dict of information about wiki-editing
* config.irc         - a dict of information about IRC
* config.metadata    - a dict of miscellaneous information
* config.schedule()  - returns a list of tasks scheduled to run at a given time

Additionally, functions related to config loading:
* config.load()     - loads and parses our config file, returning True if
                      passwords are stored encrypted or False otherwise
* config.decrypt()  - given a key, decrypts passwords inside our config
                      variables; won't work if passwords aren't encrypted
"""

import json
from os import path

import blowfish

script_dir = path.dirname(path.abspath(__file__))
root_dir = path.split(script_dir)[0]
config_path = path.join(root_dir, "config.json")

_config = None  # Holds data loaded from our config file

# Set our four easy-config-access global variables to None
components, wiki, irc, metadata = None, None, None, None

def _load():
    """Load data from our JSON config file (config.json) into _config."""
    global _config
    with open(config_path, 'r') as fp:
        try:
            _config = json.load(fp)
        except ValueError as error:
            print "Error parsing config file {0}:".format(config_path)
            print error
            exit(1)

def _make_new():
    """Make a new config file based on the user's input."""
    encrypt = raw_input("Would you like to encrypt passwords stored in config.json? [y/n] ")
    if encrypt.lower().startswith("y"):
        is_encrypted = True
    else:
        is_encrypted = False

    return is_encrypted

def is_loaded():
    """Return True if our config file has been loaded, otherwise False."""
    return _config is not None

def load():
    """Load, or reload, our config file.

    First, check if we have a valid config file, and if not, notify the user.
    If there is no config file at all, offer to make one, otherwise exit.

    Store data from our config file in four global variables (components, wiki,
    irc, metadata) for easy access (as well as the internal _config variable).

    If everything goes well, return True if stored passwords are
    encrypted in the file, or False if they are not.
    """
    global components, wiki, irc, metadata

    if not path.exists(config_path):
        print "You haven't configured the bot yet!"
        choice = raw_input("Would you like to do this now? [y/n] ")
        if choice.lower().startswith("y"):
            return _make_new()
        else:
            exit(1)

    _load()

    components = _config.get("components", [])
    wiki = _config.get("wiki", {})
    irc = _config.get("irc", {})
    metadata = _config.get("metadata", {})

    # Are passwords encrypted?
    return metadata.get("encryptPasswords", False)

def decrypt(key):
    """Use the key to decrypt passwords in our config file.
    
    Call this if load() returns True. Catch password decryption errors and
    report them to the user.
    """
    global irc, wiki

    try:
        item = wiki.get("password")
        if item:
            wiki["password"] = blowfish.decrypt(key, item)

        item = irc.get("frontend").get("nickservPassword")
        if item:
            irc["frontend"]["nickservPassword"] = blowfish.decrypt(key, item)

        item = irc.get("watcher").get("nickservPassword")
        if item:
            irc["watcher"]["nickservPassword"] = blowfish.decrypt(key, item)

    except blowfish.BlowfishError as error:
        print "\nError decrypting passwords:"
        print "{0}: {1}.".format(error.__class__.__name__, error)
        exit(1)

def schedule(minute, hour, month_day, month, week_day):
    """Return a list of tasks scheduled to run at the specified time.

    The schedule data comes from our config file's 'schedule' field, which is
    stored as _config["schedule"]. Call this function as config.schedule(args).
    """
    # Tasks to run this turn, each as a list of either [task_name, kwargs], or
    # just the task_name:
    tasks = []

    now = {"minute": minute, "hour": hour, "month_day": month_day,
            "month": month, "week_day": week_day}

    data = _config.get("schedule", [])
    for event in data:
        do = True
        for key, value in now.items():
            try:
                requirement = event[key]
            except KeyError:
                continue
            if requirement != value:
                do = False
                break
        if do:
            try:
                tasks.extend(event["tasks"])
            except KeyError:
                pass

    return tasks