import os
import re
from collections import defaultdict
from configparser import RawConfigParser
from graphviz import Digraph


include_regex = re.compile('\s*[^/]\s*#include\s+["<](.*)[">]')
valid_extensions = ['.cpp', '.h']

colors = ['yellow', 'indianred2', 'springgreen', 'turquoise1', 'red', 'olivedrab1',
          'magenta', 'green2', 'dodgerblue1', 'aquamarine2', 'gray54', 'green4',
          'hotpink1', 'olivedrab2', 'peru']


standard_headers = ['cstdlib', 'csignal', 'csetjmp', 'cstdarg', 'typeinfo',
                    'typeindex', 'type_traits', 'bitset', 'functional',
                    'utility', 'ctime', 'chrono', 'cstddef', 'initializer_list',
                    'tuple', 'new', 'memory', 'scoped_allocator', 'climits',
                    'cfloat', 'cstdint', 'cinttypes', 'limits', 'exception',
                    'stdexcept', 'cassert', 'system_error', 'cerrno', 'cctype',
                    'cwctype', 'cstring', 'cwstring', 'cwchar', 'cuchar', 'string',
                    'array', 'vector', 'deque', 'list', 'forward_list', 'set',
                    'map', 'unordered_set', 'unordered_map', 'stack', 'queue',
                    'algorithm', 'iterator', 'cmath', 'complex', 'valarray',
                    'random', 'numeric', 'ratio', 'cfenv', 'iosfwd', 'ios',
                    'istream', 'ostream', 'iostream', 'fstream', 'sstream',
                    'strstream', 'iomanip', 'streambuf', 'cstdio', 'locale',
                    'clocale', 'codecvt', 'regex', 'atomic', 'thread', 'mutex',
                    'future', 'condition_variable', 'ciso646', 'ccomplex', 'ctgmath',
                    'cstdalign', 'cstdbool']


def normalize(path, join=False):
    """ Return the name of the node that will represent the file at path. """
    filename = os.path.basename(path)
    if join:
        return os.path.splitext(filename)[0]
    else:
        return filename


def get_extension(path):
    """ Return the extension of the file at path. """
    return path[path.rfind('.'):]


def find_all_files(path, recursive=True):
    """
    Return a list of paths to all the files in the folder.
    If recursive is True, the function will search recursively.

    """
    files = []
    for entry in os.scandir(path):
        if entry.is_dir() and recursive:
            files += find_all_files(entry.path)
        elif get_extension(entry.path) in valid_extensions and entry.is_file():
            files.append(entry.path)
    return files


def find_neighbors(path, join):
    """ Find all the other nodes included by the file targeted by path. """
    f = open(path)
    code = f.read()
    return [normalize(include, join) for include in include_regex.findall(code)]


def assign_colors(folder_to_files, colors, set_colors):
    """ Assign colors to each folder. """
    color_for_folder = set_colors
    used_colors = list()
    for key in color_for_folder:
        used_colors.append(color_for_folder[key])
    i = 0
    for folder in folder_to_files:
        if folder not in color_for_folder.keys():
            try:
                while colors[i] in used_colors:
                    i += 1
                color_for_folder[folder] = colors[i]
                i += 1
            except IndexError:
                print("Sorry, not enough colors")
    return color_for_folder


def choose_color(node, folder, color_to_folder):
    """ Choose color for given node. """
    node_color = color_to_folder[folder]
    if node in standard_headers:
        node_color = color_to_folder['STL']
    # need to find a better way to find 'Qt' color
    elif node[0] == 'Q':
        for folder in color_to_folder:
            if normalize(folder) == 'Qt':
                node_color = color_to_folder[folder]
    elif 'windows' in node:
        node_color = color_to_folder['Windows API']
    return node_color


def choose_shape(node):
    """ Choose shape for given node  """
    if get_extension(node) == '.h' or node in standard_headers or node[0] == 'Q':
        return 'polygon'
    else:
        return 'ellipse'


def add_label(graph, color_to_folder):
    """ Add label  """
    with graph.subgraph(name='cluster_label',
                        graph_attr={'bgcolor': 'grey93', 'label': 'Label',
                                    'labelfontsize': '18', 'pencolor': 'grey93',
                                    'penwidth': '20.0', 'style': 'rounded'}) as label:
        for folder in color_to_folder:
            label.node(f'label_{normalize(folder)}', normalize(folder), style='filled',
                       fillcolor=color_to_folder[folder])


def create_graph(folder, config):
    # declare some things
    create_cluster = config.getboolean('settings', 'cluster')
    join = config.getboolean('settings', 'join')
    files_to_ignoge = config['ignore']
    set_colors = dict(config.items('colors'))
    # Find nodes and clusters
    files = find_all_files(folder)
    folder_to_files = defaultdict(list)
    for path in files:
        folder_to_files[os.path.dirname(path)].append(path)
    nodes = {normalize(path, join) for path in files}
    # assign colors to clusters
    color_to_folder = assign_colors(folder_to_files, colors, set_colors)
    # Create graph
    graph = Digraph('G', graph_attr={'ranksep': '2.5 equally', 'rankdir': 'BT'})
    # Find edges and create clusters
    for folder in folder_to_files:
        with graph.subgraph(name=f'cluster_{folder}') as cluster:
            for path in folder_to_files[folder]:
                new_node = normalize(path, join)
                if new_node not in files_to_ignoge:
                    node_color = choose_color(new_node, folder, color_to_folder)
                    node_shape = choose_shape(new_node)
                    if create_cluster:
                        graph.graph_attr.update({'ranksep': '10.0 equally'})
                        cluster.node(new_node, style='filled', shape=node_shape, fillcolor=node_color)
                    else:
                        graph.node(new_node, style='filled', shape=node_shape, fillcolor=node_color)
                    neighbors = find_neighbors(path, join)
                    for neighbor in neighbors:
                        if neighbor != new_node and neighbor not in files_to_ignoge:
                            if neighbor not in nodes:
                                neighbor_color = choose_color(neighbor, folder, color_to_folder)
                                neighbor_shape = choose_shape(neighbor)
                                graph.node(neighbor, style='filled', shape=neighbor_shape,
                                           fillcolor=neighbor_color)
                            graph.edge(new_node, neighbor, color=node_color)
    add_label(graph, color_to_folder)
    return graph


if __name__ == '__main__':
    config = RawConfigParser(allow_no_value=True, delimiters=('='))
    config.optionxform = lambda option: option  # Overwrite optionxform() to support case sensitivity
    config.read('settings.ini')
    graph = create_graph(config['settings']['folder'], config)
    graph.format = config['settings']['format']
    graph.save(f'{config["settings"]["filename"]}_source.dot', config['settings']['output'])
    graph.render(config["settings"]["filename"], config['settings']['output'], cleanup=True,
                 view=config.getboolean('settings', 'view'))
