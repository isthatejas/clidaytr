import os
import sys
from textwrap import wrap
import collections
import datetime
from rich import print
from rich.console import Console
from rich.table import Table
import click
from click_default_group import DefaultGroup
import yaml
import configparser

VERSION = "0.0.0"

class Config(object):
    def __init__(self):
        self.path = os.getcwd()
        self.aliases = {}

    def read_config(self, filename):
        parser = configparser.RawConfigParser()
        parser.read([filename])
        try:
            self.aliases.update(parser.items('aliases'))
        except configparser.NoSectionError:
            pass

pass_config = click.make_pass_decorator(Config, ensure=True)

class AliasedGroup(DefaultGroup):
    #This subclass of a group supports looking up aliases in a config
    def get_command(self, ctx, cmd_name):
        #bulit-in commands as normal
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        #find the config object and ensure it's there.  This
        #will create the config object is missing.
        cfg = ctx.ensure_object(Config)
        
        #lookup an explicit command aliases in the config
        if cmd_name in cfg.aliases:
            actual_cmd = cfg.aliases[cmd_name]
            return click.Group.get_command(self, ctx, actual_cmd)
            
        #allow automatic abbreviation of the command.
        matches = [x for x in self.list_commands(ctx)
                   if x.lower().startswith(cmd_name.lower())]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

def read_config(ctx, param, value):
    #This means that the config is loaded even if the group itself never executes so our aliases stay always available.
    cfg = ctx.ensure_object(Config)
    if value is None:
        value = os.path.join(os.path.dirname(__file__), 'aliases.ini')
    cfg.read_config(value)
    return value

@click.version_option(VERSION)
@click.command(cls=AliasedGroup, default='show', default_if_no_args=True)
def clidaytr():
    """clikan: CLI personal kanban """

@clidaytr.command()
def configure():
    #place default config file in CLIDAYTR_HOME or HOME
    home = get_clidaytr_home()
    data_path = os.path.join(home, ".clidaytr.dat")
    config_path = os.path.join(home, ".clidaytr.yaml")
    if (os.path.exists(config_path) and not
            click.confirm('Config file exists. Do you want to overwrite?')):
        return
    with open(config_path, 'w') as outfile:
        conf = {'clidaytr_data': data_path}
        yaml.dump(conf, outfile, default_flow_style=False)
    click.echo("Creating %s" % config_path)

def read_data(config):
    #Read the existing data from the config datasource
    try:
        with open(config["clidaytr_data"], 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print("Ensure %s exists, as you specified it "
                      "as the clikan data file." % config['clidaytr_data'])
                print(exc)
    except IOError:
        click.echo("No data, initializing data file.")
        write_data(config, {"data": {}, "deleted": {}})
        with open(config["clidaytr_data"], 'r') as stream:
            return yaml.safe_load(stream)

def write_data(config, data):
    with open(config["clidaytr_data"], 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

def get_clidaytr_home():
    home = os.environ.get('CLIDAYTR_HOME')
    if not home:
        home = os.path.expanduser('~')
    return home

def read_config_yaml():
    # Read from ~/.clidaytr.yaml
    try:
        home = get_clidaytr_home()
        with open(home + "/.clidaytr.yaml", 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError:
                print("Ensure %s/.clidaytr.yaml is valid, expected YAML." % home)
                sys.exit()
    except IOError:
        print("Ensure %s/.clidaytr.yaml exists and is valid." % home)
        sys.exit()

def split_items(config, dd):
    todos = []
    inprogs = []
    backlogs = []
    dones = []

    for key, value in dd['data'].items():
        if value[0] == 'todo':
            todos.append("[%d] %s" % (key, value[1]))
        elif value[0] == 'inprogress':
            inprogs.append("[%d] %s" % (key, value[1]))
        elif value[0] == 'backlog':
            inprogs.append("[%d] %s" % (key, value[1]))
        else:
            dones.insert(0, "[%d] %s" % (key, value[1]))

    return todos, inprogs, backlogs,  dones

def timestamp():
    return '{:%Y-%b-%d %H:%M:%S}'.format(datetime.datetime.now())


PRIORITY_MAP = {
    'high': 1,
    'medium': 2,
    'low': 3
}

@clidaytr.command()
@click.argument('tasks', nargs=-1)
@click.option('--name', '-n', help='Name of the Table', required=True)
@click.option('--priority', type=click.Choice(['high', 'medium', 'low']), default='medium', help='Priority of the task' )
def add(tasks, priority, name):
    config = read_config_yaml()
    dd = read_data(config)

    if ('limits' in config and 'taskname' in config['limits']):
        taskname_length = config['limits']['taskname']
    else:
        taskname_length = 40

    for task in tasks:
        if len(task) > taskname_length:
            click.echo('Task must be at most %s chars, Brevity counts: %s'
                       % (taskname_length, task))
        else:
            todos, inprogs, backlogs, dones = split_items(config, dd)
            if ('limits' in config and 'todo' in config['limits'] and
                    int(config['limits']['todo']) <= len(todos)):
                click.echo('No new todos, limit reached already.')
            else:
                od = collections.OrderedDict(sorted(dd['data'].items()))
                new_id = 1
                if bool(od):
                    new_id = next(reversed(od)) + 1
                entry = ['todo', task, timestamp(), timestamp(), PRIORITY_MAP[priority],name]
                dd['data'].update({new_id: entry})
                click.echo("Creating new task w/ id: %d -> %s"
                           % (new_id, task))

    write_data(config, dd)
    if ('repaint' in config and config['repaint']):
        display()

@clidaytr.command()
@click.argument('ids', nargs=-1)
def delete(ids):
    config = read_config_yaml()
    dd = read_data(config)

    for id in ids:
        try:
            item = dd['data'].get(int(id))
            if item is None:
                click.echo('No existing task with that id: %d' % int(id))
            else:
                item[0] = 'deleted'
                item[2] = timestamp()
                dd['deleted'].update({int(id): item})
                dd['data'].pop(int(id))
                click.echo('Removed task %d.' % int(id))
        except ValueError:
            click.echo('Invalid task id')

    write_data(config, dd)
    if ('repaint' in config and config['repaint']):
        display()

@clidaytr.command()
@click.argument('ids', nargs=-1)
def promote(ids):
    config = read_config_yaml()
    dd = read_data(config)
    todos, inprogs, backlogs, dones = split_items(config, dd)

    for id in ids:
        try:
            item = dd['data'].get(int(id))
            if item is None:
                click.echo('No existing task with that id: %s' % id)
            elif item[0] == 'todo':
                if ('limits' in config and 'wip' in config['limits'] and
                        int(config['limits']['wip']) <= len(inprogs)):
                    click.echo(
                        'Can not promote, in-progress limit of %s reached.'
                        % config['limits']['wip']
                    )
                else:
                    click.echo('Promoting task %s to in-progress.' % id)
                    dd['data'][int(id)] = [
                        'inprogress',
                        item[1], timestamp(),
                        item[3],item[4],item[5]
                    ]
            elif item[0] == 'inprogress':
                click.echo('Promoting task %s to backlogs.' % id)
                dd['data'][int(id)] = ['backlog', item[1], timestamp(), item[3],item[4],item[5]]
            elif item[0] == 'backlog':
                click.echo('Promoting task %s to done.' % id)
                dd['data'][int(id)] = ['done', item[1], timestamp(), item[3],item[4],item[5]]
            else:
                click.echo('Can not promote %s, already done.' % id)
        except ValueError:
            click.echo('Invalid task id')

    write_data(config, dd)
    if ('repaint' in config and config['repaint']):
        display()

@clidaytr.command()
@click.argument('ids', nargs=-1)
def regress(ids):
    config = read_config_yaml()
    dd = read_data(config)

    todos, inprogs, backlogs, dones = split_items(config, dd)

    for id in ids:
        item = dd['data'].get(int(id))
        if item is None:
            click.echo('No existing task with id: %s' % id)
        elif item[0] == 'done':
            click.echo('Regressing task %s to backlogs.' % id)
            dd['data'][int(id)] = ['backlog', item[1], timestamp(), item[3],item[4],item[5]]
        elif item[0] == 'backlog':
            click.echo('Regressing task %s to inprogress.' % id)
            dd['data'][int(id)] = ['inprogress', item[1], timestamp(), item[3],item[4],item[5]]
        elif item[0] == 'inprogress':
            click.echo('Regressing task %s to todo.' % id)
            dd['data'][int(id)] = ['todo', item[1], timestamp(), item[3],item[4],item[5]]
        else:
            click.echo('Already in todo, can not regress %s' % id)

    write_data(config, dd)
    if ('repaint' in config and config['repaint']):
        display()

@clidaytr.command()
@click.option('--name', '-n', help='Name of the Table', required=True)
def show(name):
    console = Console()
    config = read_config_yaml()
    dd = read_data(config)
    todos, inprogs, backlogs, dones = split_items(config, dd)
    if 'limits' in config and 'done' in config['limits']:
        dones = dones[0:int(config['limits']['done'])]
    else:
        dones = dones[0:10]

    sorted_data = sorted(dd['data'].items(), key=lambda item: item[1][4])
    filtered_data = [item for item in sorted_data if item[1][5] == name]

    #filtered data
    filtered_todos = []
    filtered_inprogs = []
    filtered_backlogs = []
    filtered_dones = []
    for key, value in filtered_data:
        if value[0] == 'todo':
            filtered_todos.append("[%d] %s" % (key, value[1]))
        elif value[0] == 'backlog':
            filtered_backlogs.append("[%d] %s" % (key, value[1]))
        elif value[0] == 'inprogress':
            filtered_inprogs.append("[%d] %s" % (key, value[1]))
        else:
            filtered_dones.insert(0, "[%d] %s" % (key, value[1]))

    todos = '\n'.join([str(x) for x in filtered_todos])
    backlogs = '\n'.join([str(x) for x in filtered_backlogs])
    inprogs = '\n'.join([str(x) for x in filtered_inprogs])
    dones = '\n'.join([str(x) for x in filtered_dones])

    table = Table(show_header=True, show_footer=True)
    table.add_column(
        "[bold yellow]TO-DO[/bold yellow]",
        no_wrap=True,
        footer=name
    )
    table.add_column('[bold blue]IN-PROGRESS[/bold blue]', no_wrap=True)
    table.add_column('[bold green]BACKLOG[/bold green]', no_wrap=True, footer="I LOVE GDSC")
    table.add_column(
        '[bold magenta]DONE[/bold magenta]',
        no_wrap=True,
        footer="v.{}".format(VERSION)
    )

    table.add_row(todos, inprogs, backlogs, dones)
    console.print(table)

def display():
    console = Console()
    config = read_config_yaml()
    dd = read_data(config)
    todos, inprogs, backlogs, dones = split_items(config, dd)
    if 'limits' in config and 'done' in config['limits']:
        dones = dones[0:int(config['limits']['done'])]
    else:
        dones = dones[0:10]

    todos = '\n'.join([str(x) for x in todos])
    inprogs = '\n'.join([str(x) for x in inprogs])
    backlogs = '\n'.join([str(x) for x in backlogs])
    dones = '\n'.join([str(x) for x in dones])

    table = Table(show_header=True, show_footer=True)
    table.add_column(
        "[bold yellow]TODO[/bold yellow]",
        no_wrap=True,
        footer="I LOVE GDSC"
    )
    table.add_column('[bold blue]IN-PROGRESS[/bold blue]', no_wrap=True)
    table.add_column('[bold green]BACKLOG[/bold green]', no_wrap=True)
    table.add_column(
        '[bold magenta]DONE[/bold magenta]',
        no_wrap=True,
        footer="v.{}".format(VERSION)
    )

    table.add_row(todos, inprogs, backlogs, dones)
    console.print(table)
