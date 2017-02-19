# -*- python -*-
#
#       Copyright 2015 INRIA - CIRAD - INRA
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
# ==============================================================================
import os
import json
import pickle

from networkx.readwrite.json_graph import (node_link_data, node_link_graph)
from networkx.readwrite.gpickle import (read_gpickle, write_gpickle)
# ==============================================================================


class VoxelGraph(object):

    def __init__(self, graph, voxels_size):
        self.graph = graph
        self.voxels_size = voxels_size

    def write_to_json(self, filename):
        if (os.path.dirname(filename) and not os.path.exists(
                os.path.dirname(filename))):
            os.makedirs(os.path.dirname(filename))

        with open(filename, 'w') as f:

            data = dict()
            data['graph'] = node_link_data(self.graph)
            data['voxels_size'] = self.voxels_size
            json.dump(data, f)

    @staticmethod
    def read_from_json(filename):

        with open(filename, 'rb') as f:

            data = json.load(f)

            data_graph = data['graph']
            for node in data_graph['nodes']:
                node['id'] = tuple(node['id'])

            graph = node_link_graph(data_graph)
            voxels_size = data['voxels_size']

            return VoxelGraph(graph, voxels_size)

    # def write_to_pickle(self, filename):
    #     if (os.path.dirname(filename) and not os.path.exists(
    #             os.path.dirname(filename))):
    #         os.makedirs(os.path.dirname(filename))
    #
    #     with open(filename, 'wb') as f:
    #
    #         data = dict()
    #         data['graph'] = node_link_data(self.graph)
    #         data['voxels_size'] = self.voxels_size
    #         pickle.dump(data, f)