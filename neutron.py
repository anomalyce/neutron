import os
import sys
import json
import yaml
import time
import glob

# --------------------------------------------------

class ProjectManager():
    debug = False
    settingsfile = "neutron"
    configfile = "neutron.yml"
    lastproject = "/tmp/neutron.recent"
    pathseparator = "→"
    settings = {
        "paths": [
            "~/Sites"
        ],
        "i3": {
            "workspace": 3,
        },
        "launcher": {
            "command": "echo '%s' | rofi -dmenu -config $HOME/.config/rofi -p 'Project Manager'"
        },
        "terminal": {
            "command": "alacritty --title \"%s\" --class \"Project%s\" --working-directory %s",
            "targets": {
                "instance": "^Project%s$"
            }
        },
        "browser": {
            "title": "Firefox",
            "command": "firefox https://127.0.0.1",
            "targets": {
                "class": "^Firefox$"
            }
        },
        "editor": {
            "title": "Sublime Text",
            "command": "subl3 --project %s",
            "targets": {
                "class": "^Subl3$"
            }
        }
    }
    file = None
    modules = { }
    config = { }

    def __init__(self, action):
        self.loadSettings()

        if self.debug is True:
            print(json.dumps(self.settings, indent=4, sort_keys=False))

        if action.lower() == "list":
            self.projectlist()
        else:
            self.initialise(action)

    def loadSettings(self):
        if (os.getenv("XDG_CONFIG_HOME")):
            settingsfile = os.path.abspath(os.getenv("XDG_CONFIG_HOME") + "/" + self.settingsfile)
        elif (os.path.exists(os.path.expanduser("~/.config/" + self.settingsfile))):
            settingsfile = os.path.expanduser("~/.config/" + self.settingsfile)
        elif (os.path.exists(os.path.expanduser("~/." + self.settingsfile))):
            settingsfile = os.path.expanduser("~/." + self.settingsfile)
        else:
            settingsfile = None

        if settingsfile is not None and os.path.exists(settingsfile):
            f = open(settingsfile, "r")
            settings = json.load(f)
            f.close()

            self.settings.update(settings)

    def initialise(self, action):
        if self.pathseparator in action:
            parts = action.split(self.pathseparator)

            action = os.path.expanduser("%s/%s" % (parts[1].strip(), parts[0].strip()))

        self.file = self.getFilenameByAction(action)
        self.config = self.__loadConfigFile()
          
        if action.lower() == "quit" or action.lower() == "quit active project":
            self.quit()
        else:
            if os.path.exists(self.lastproject):
                self.quit()
                time.sleep(.500)

            self.execute()


    def getFilenameByAction(self, action):
        if action.lower() == "quit" or action.lower() == "quit active project":
            if not os.path.exists(self.lastproject):
                raise FileNotFoundError("No project to quit...")
            
            f = open(self.lastproject, "r")
            filename = f.read()
            f.close()

            return filename.strip()
        else:
            return os.path.abspath(action + "/" + self.configfile)

    def getSettings(self):
        return self.settings

    def getConfig(self):
        return self.config

    def __loadConfigFile(self):
        config = yaml.safe_load(open(self.file))

        # Loading modules...
        if "network" in config:
            self.registerModule("network_manager", NetworkManager(config["network"]))

        if "sublime_project" in config and config["sublime_project"] is not None:
            self.registerModule("sublime_project", SublimeProject(config["sublime_project"]))

        if "i3_workspace" in config and config["i3_workspace"] is not None:
            self.registerModule("i3_workspace", i3Workspace(config["i3_workspace"]))

        return config

    def getFullPath(self):
        return os.path.abspath(self.file)

    def getFileName(self):
        return os.path.basename(self.getFullPath())

    def getDirectory(self):
        return os.path.dirname(self.getFullPath())

    def getNamespace(self):
        return os.path.basename(self.getDirectory())

    def registerModule(self, name, module):
        self.modules[name] = module.setProjectManager(self).process()

    def getModules(self):
        return self.modules

    def getModule(self, name):
        return self.modules[name]

    def command(self, command, module, method):
        if self.debug is True:
            print("[DEBUG] %s::%s called `%s`" % (module.name(), method, command))
        else:
            output = os.popen(command).read()

            time.sleep(.100)

            return output

    def name(self):
        return type(self).__name__

    def projectlist(self):
        projects = [ ]

        homedirectory = os.path.expanduser("~")
        
        for path in self.settings["paths"]:
            fullpath = os.path.expanduser(path + "/**/**/" + self.configfile)

            for project in glob.glob(fullpath):
                namespace = os.path.basename(os.path.dirname(project))
                directory = os.path.dirname(os.path.dirname(project))
                directory = directory.replace(homedirectory, "~")

                neutronignore = "%s/.neutronignore" % os.path.dirname(project)
                
                if os.path.exists(neutronignore) is False:
                    projects.append("%s %s %s" % (namespace, self.pathseparator, directory))

        output = "|".join(projects)
        
        if os.path.exists(self.lastproject):
            output += "|quit active project"
        
        command = self.settings["launcher"]["command"] % output
        print(command)
        choice = self.command(command, self, sys._getframe().f_code.co_name)
        choice = choice.strip()

        if choice == "":
            return None

        self.initialise(choice)        

    def execute(self):
        modules = self.getModules()

        # Process any existing module pre-hooks
        for name in modules:
            module = modules[name]

            if callable(getattr(module, "preHook", None)):
                time.sleep(.100)
                module.preHook()

        time.sleep(.250)

        # Execute the modules...
        for name in modules:
            module = modules[name]

            time.sleep(.100)
            module.execute()

        time.sleep(.250)

        # Process any existing module post-hooks
        for name in modules:
            module = modules[name]

            if callable(getattr(module, "postHook", None)):
                time.sleep(.100)
                module.postHook()

        f = open(self.lastproject, 'w')
        f.write(self.getFullPath())
        f.close()

    def quit(self):
        modules = self.getModules()

        # Process any existing module quit-hooks
        for name in modules:
            module = modules[name]

            if callable(getattr(module, "quitHook", None)):
                time.sleep(.100)
                module.quitHook()

        if os.path.exists(self.lastproject):
            os.remove(self.lastproject)

# --------------------------------------------------

class ProjectManagerModule():
    project = None
    config = None

    def __init__(self, config):
        if config is None:
            raise ValueError("hello world")

        self.config = config

    def setProjectManager(self, project):
        self.project = project

        return self

    def name(self):
        return type(self).__name__

    def process(self, project):
        raise NotImplementedError(
            "Expected module method 'process' for '%s' not found" % self.name()
        )

    def execute(self):
        raise NotImplementedError(
            "Expected module method 'execute' for '%s' not found" % self.name()
        )

# --------------------------------------------------

class NetworkManager(ProjectManagerModule):
    connection = None

    def __init__(self, config):
        if config is not None:
            self.config = config
        else:
            self.config = { }

    def process(self):
        if "vpn" in self.config and self.config["vpn"] is not False:
            self.connection = self.config["vpn"]
        else:
            self.connection = os.getenv("VPN_CONNECTION", "Sweden")

        return self

    def preHook(self):
        if self.connection is not None:
            self.project.command("nordvpn disconnect", self, sys._getframe().f_code.co_name)

    def execute(self):
        return None

    def postHook(self):
        if self.connection is not None:
            self.project.command("nordvpn connect %s" % self.connection, self, sys._getframe().f_code.co_name)

# --------------------------------------------------

class SublimeProject(ProjectManagerModule):
    tmpfile = "/tmp/neutron.sublime-project"
    sublime_project = {
        "folders": [ ],
    }

    def process(self):
        for label in self.config:
            options = self.config[label]

            if label.lower() == "%project%":
                label = self.project.getNamespace()

            folder = {
                "name": label,
                "path": None,
            }

            if type(options) is str:
                folder["path"] = os.path.abspath(self.project.getDirectory() + "/" + options)
            else:
                folder["path"] = os.path.abspath(self.project.getDirectory() + "/" + options["path"])

                if "exclude" in options and len(options["exclude"]) > 0:
                    folder["folder_exclude_patterns"] = list(options["exclude"])

            self.sublime_project["folders"].append(folder)

        return self

    def preHook(self):
        if os.path.exists(self.tmpfile):
            os.remove(self.tmpfile)

        f = open(self.tmpfile, 'w')
        f.write(json.dumps(self.sublime_project, indent=4, sort_keys=False))
        f.close()

    def execute(self):
        command = "( " + self.project.settings["editor"]["command"] + " & ) &> /dev/null"

        self.project.command(command % self.tmpfile, self, sys._getframe().f_code.co_name)

# --------------------------------------------------

class i3Workspace(ProjectManagerModule):
    tmpfile = "/tmp/neutron.i3-workspace"
    i3_workspace = { "nodes": [ ] }
    commands = [ ]
    quitcommands = [ ]

    def process(self):
        self.i3_workspace = self.__parseGroups(self.i3_workspace, self.config)

        return self

    def __parseGroups(self, workspace, items):
        lastitem = list(items.keys())[-1]
        
        for label in items:
            item = items[label]
            workspace["nodes"].append(self.__handleItem(workspace, label, item, lastitem))

        return workspace

    def __handleItem(self, workspace, label, item, lastitem = None):
        if self.__isTerminal(label, item):
            return self.__handleTerminal(label, item)
        elif self.__isBrowser(label, item):
            return self.__handleBrowser(label, item)
        elif self.__isEditor(label, item):
            return self.__handleEditor(label, item)
        elif self.__isGroup(label, item):
            return self.__handleGroup(label, item, lastitem)
        else:
            return self.__handleCustomItem(label, item)

    def __handleTerminal(self, label, item):
        settings = self.project.settings["terminal"]

        swallows = [ ]
        for target in settings["targets"]:
            swallows.append({ target: settings["targets"][target] % label })

        path = os.path.abspath(self.project.getDirectory() + "/" + item["path"])

        command = settings["command"] % (label, label, path)

        if "command" in item:
            command += " -e %s" % item["command"]

        self.commands.append("( " + command + " & ) &> /dev/null")

        if "quit" in item and type(item["quit"]) is list and len(item["quit"]) > 0:
            for quitcommand in item["quit"]:
                self.quitcommands.append("( " + quitcommand + " & ) &> /dev/null")

        return { **self.__handleDefaultItem(label, item), **{
            "name": "  %s " % label,
            "swallows": swallows
        } }

    def __handleBrowser(self, label, item):
        settings = self.project.settings["browser"]

        swallows = [ ]
        for target in settings["targets"]:
            swallows.append({ target: settings["targets"][target] })

        self.commands.append("( " + settings["command"] + " & ) &> /dev/null")

        return { **self.__handleDefaultItem(label, item), **{
            "name": "  %s " % settings["title"],
            "swallows": swallows
        } }

    def __handleEditor(self, label, item):
        settings = self.project.settings["editor"]

        swallows = [ ]
        for target in settings["targets"]:
            swallows.append({ target: settings["targets"][target] })

        return { **self.__handleDefaultItem(label, item), **{
            "name": "  %s " % settings["title"],
            "swallows": swallows
        } }

    def __handleCustomItem(self, label, item):
        return { **self.__handleDefaultItem(label, item), **{
            "name": "Custom %s" % label,
        } }

    def __handleDefaultItem(self, label, item):
        return {
            "border": "pixel",
            "current_border_width": os.getenv("SETTINGS_BORDERSIZE", 1),
            "floating": "auto_off",
            "percent": 1,
            "type": "con",
            "swallows": [ ],
            "geometry": {
                "height": 0,
                "width": 0,
                "x": 0,
                "y": 0
            },
        }

    def __handleGroup(self, label, item, lastitem):
        if "height" in item:
            layout = "splith"
            percent = item["height"]
        elif "width" in item:
            layout = "splitv"
            percent = item["width"]
        else:
            layout = "tabbed"
            percent = 1

        if layout != "tabbed" and label.lower() == lastitem.lower():
            layout = "tabbed"

        response = {
            "label": label,
            "border": "pixel",
            "floating": "auto_off",
            "layout": layout,
            "percent": percent,
            "type": "con",
            "nodes": [ ]
        }
        
        if layout != "tabbed" and not self.__hasSubGroups(item["nodes"]):
            return { **response, **{ "nodes": [ self.__parseGroups({
                "border": "pixel",
                "floating": "auto_off",
                "layout": "tabbed",
                "percent": 1,
                "type": "con",
                "nodes": [ ]
            }, item["nodes"]) ] } }

        return self.__parseGroups(response, item["nodes"])

    def __hasSubGroups(self, nodes):
        subgroups = 0

        for node in nodes:
            if self.__isGroup(node, nodes[node]):
                subgroups += 1

        return subgroups

    def __isGroup(self, label, item):
        return type(item) is dict and "nodes" in item and len(item["nodes"]) > 0

    def __isTerminal(self, label, item):
        return type(item) is dict and "terminal" in item and item["terminal"] is True

    def __isBrowser(self, label, item):
        return label.lower() == "browser" and item is True

    def __isEditor(self, label, item):
        return label.lower() == "editor" and item is True

    def preHook(self):
        if os.path.exists(self.tmpfile):
            os.remove(self.tmpfile)

        f = open(self.tmpfile, 'w')
        for node in self.i3_workspace["nodes"]:
            f.write(json.dumps(node, indent=4, sort_keys=False) + "\n\n")
        f.close()

        workspace = self.project.settings["i3"]["workspace"]
        
        self.project.command("( i3-msg 'workspace %s; append_layout %s' ) &> /dev/null" % (workspace, self.tmpfile), self, sys._getframe().f_code.co_name)

    def execute(self):
        for command in self.commands:
            self.project.command(command, self, sys._getframe().f_code.co_name)

    def postHook(self):
        workspace = self.project.settings["i3"]["workspace"]

        self.project.command("( i3-msg 'workspace 1' ) &> /dev/null", self, sys._getframe().f_code.co_name)
        self.project.command("( i3-msg 'workspace %s' ) &> /dev/null" % workspace, self, sys._getframe().f_code.co_name)

    def quitHook(self):
        workspace = self.project.settings["i3"]["workspace"]

        self.quitcommands.append("( i3-msg 'workspace %s; focus parent, focus parent, focus parent, focus parent, focus parent, focus parent, focus parent, focus parent, focus parent, focus parent, kill; workspace 1' ) &> /dev/null" % workspace)

        for quitcommand in self.quitcommands:
            self.project.command(quitcommand, self, sys._getframe().f_code.co_name)

# --------------------------------------------------

project = ProjectManager(sys.argv[1])

