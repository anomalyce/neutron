# Neutron

## Installation
```bash
cd ~/Sites

git clone git@github.com:anomalyce/neutron.git

sudo ln -s ~/Sites/projects/neutron/neutron.py /usr/bin/neutron
```

## Configuration
You may replace all of the configuration options by creating a `neutron` configuration file in one of the following locations (ordered by priority):

+ `$XDG_CONFIG_HOME/neutron`
+ `~/.config/neutron`
+ `~/.neutron`

Refer to the top of `neutron.py` for what config options are available.

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
python /usr/bin/neutron list
```

### Start Project/Switch to Project
Make sure `~/Sites/my-site` has a [neutron.yml](/neutron.yml.example) file.

```bash
python /usr/bin/neutron ~/Sites/my-site
```

### Quit Project
```bash
python /usr/bin/neutron quit
```

