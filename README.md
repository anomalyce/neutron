# i3-subl-project-manager

## Installation
```bash
cd ~/Sites

git clone git@github.com:anomalyce/i3-subl-project-manager.git

sudo ln -s ~/Sites/i3-subl-project-manager/i3-subl-pm.py /usr/bin/i3-subl-pm
```

## Configuration
You may replace all of the configuration options by creating a `i3-subl-pm` configuration file in one of the following locations (ordered by priority):

+ `$XDG_CONFIG_HOME/i3-subl-pm`
+ `~/.config/i3-subl-pm`
+ `~/.i3-subl-pm`

Refer to the top of `i3-subl-pm.py` for what config options are available.

```bash
{
    "paths": [
        "~/Sites",
        "~/Templates/Docker"
    ]
}
```

## Usage
### List Projects
```bash
python /usr/bin/i3-subl-pm list
```

### Start Project/Switch to Project
Make sure `~/Sites/my-site` has a [i3-subl-pm.yaml](/i3-subl-pm.yaml.example) file.

```bash
python /usr/bin/i3-subl-pm ~/Sites/my-site
```

### Quit Project
```bash
python /usr/bin/i3-subl-pm quit
```

