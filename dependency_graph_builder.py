import os
import re
import argparse
from collections import defaultdict
from graphviz import Digraph

include_regex = re.compile('\s*[^/]\s*#include\s+["<](.*)[">]')
valid_extensions = ['.cpp', '.h']

colors = ['yellow', 'indianred2', 'springgreen', 'turquoise1', 'red', 'olivedrab1',
          'magenta', 'green2', 'dodgerblue1', 'aquamarine']

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


def normalize(path):
    """ Return the name of the node that will represent the file at path. """
    filename = os.path.basename(path)
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


def find_neighbors(path):
    """ Find all the other nodes included by the file targeted by path. """
    f = open(path)
    code = f.read()
    return [normalize(include) for include in include_regex.findall(code)]


def assign_colors(folder_to_files, colors):
    """ Assign colors to each folder. """
    color_for_folder = defaultdict()
    i = 0
    for folder in folder_to_files:
        color_for_folder[folder] = colors[i]
        i += 1
    return color_for_folder


def choose_color(node, folder, color_to_folder):
    """ Choose color for given node. """
    node_color = color_to_folder[folder]
    if node in standard_headers:
        node_color = 'deeppink1'
    elif node[0] == 'Q':
        node_color = 'blueviolet'
    elif 'windows' in node:
        node_color = 'royalblue'
    return node_color


def add_label(graph, color_to_folder):
    """ Add label  """
    with graph.subgraph(name='cluster_label',
                        graph_attr={'bgcolor': 'grey93', 'label': 'Label',
                                    'labelfontsize': '18', 'pencolor': 'grey93',
                                    'penwidth': '20.0','style': 'rounded'}) as label:
        label.node('STL', style='filled', color='deeppink1')
        label.node('Qt', style='filled', color='blueviolet')
        label.node('Windows', style='filled', color='royalblue')
        for folder in color_to_folder:
            label.node(normalize(folder), style='filled', color=color_to_folder[folder])


def create_graph(folder, create_cluster):
    # Find nodes and clusters
    files = find_all_files(folder)
    folder_to_files = defaultdict(list)
    for path in files:
        folder_to_files[os.path.dirname(path)].append(path)
    nodes = {normalize(path) for path in files}
    # assign colors to clusters
    color_to_folder = assign_colors(folder_to_files, colors)
    # Create graph
    graph = Digraph('G', graph_attr={'ranksep': '2.3 equally'})
    # Find edges and create clusters
    for folder in folder_to_files:
        with graph.subgraph(name=f'cluster_{folder}') as cluster:
            for path in folder_to_files[folder]:
                new_node = normalize(path)
                node_color = choose_color(new_node, folder, color_to_folder)
                if create_cluster:
                    cluster.node(new_node, style='filled', color=node_color)
                else:
                    graph.node(new_node, style='filled', color=node_color)
                neighbors = find_neighbors(path)
                for neighbor in neighbors:
                    if neighbor != new_node:  # and neighbor in nodes
                        if neighbor not in nodes:
                            neighbor_color = choose_color(neighbor, folder, color_to_folder)
                            graph.node(neighbor, style='filled', color=neighbor_color)
                        graph.edge(new_node, neighbor, color=node_color)
    add_label(graph, color_to_folder)
    return graph


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', help='Path to the folder to scan')
    parser.add_argument('output', help='Path to the folder of the output file')
    parser.add_argument('filename', help='Name of the output file without extension')
    parser.add_argument('-f', '--format', help='Format of the output', default='pdf',
                        choices=['bmp', 'gif', 'jpg', 'png', 'pdf', 'svg'])
    parser.add_argument('-v', '--view', action='store_true', help='View the graph')
    parser.add_argument('-c', '--cluster', action='store_true', help='Create a cluster for each subfolder')
    args = parser.parse_args()
    graph = create_graph(args.folder, args.cluster)
    graph.format = args.format
    graph.save(f'{args.filename}.dot', args.output)
    graph.render(args.filename, args.output, cleanup=True, view=args.view)
