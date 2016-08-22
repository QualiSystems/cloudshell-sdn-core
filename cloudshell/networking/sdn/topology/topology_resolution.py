import json
import networkx as nx

import inject
from cloudshell.networking.sdn.configuration.cloudshell_controller_configuration import CONTROLLER_HANDLER

class SDNRoutingResolution(object):

    def __init__(self, controller_handler=None, logger=None):

        self._controller = controller_handler
        self.switches_list = []
        self.graph = None
        self.diGraph = None
        self.edges = None
        self.topology = None
        self.switches_ports = dict()


    @property
    def logger(self):
        if self._logger is None:
            try:
                self._logger = inject.instance('logger')
            except:
                raise Exception('SDNRoutingResolution', 'Logger is none or empty')
        return self._logger


    @property
    def controller(self):
        if self._controller is None:
            try:

                self._controller = inject.instance(CONTROLLER_HANDLER)
            except:
                raise Exception('SDNRoutingResolution', 'controller handler is none or empty')
        return self._controller

    def build_graph(self):
        self.graph = nx.Graph()
        self.diGraph = nx.DiGraph()

        self.get_topology()
        self.get_switches()
        self.get_edges()

        nodeProperties = json.loads(self.switches_list.text)
        nodes = nodeProperties['nodeProperties']

        for node in nodes:
            self.graph.add_node(node['node']['id'])
            self.diGraph.add_node(node['node']['id'])

    def get_topology(self):
        self.topology = self.controller.get_query('topology', 'default')

    def get_switches(self):
        self.switches_list = self.controller.get_query('switchmanager', '/nodes')

    def get_edges(self):
        edgeProperties = json.loads(self.topology.text)
        self.edges = edgeProperties['edgeProperties']

        for edge in self.edges:
            e = (edge['edge']['headNodeConnector']['node']['id'], edge['edge']['tailNodeConnector']['node']['id'])
            self.graph.add_edge(*e)
            self.diGraph.add_edge(*e)

    def get_leaf_switches(self):
        return self.lowest_centrality(nx.betweenness_centrality(self.graph, endpoints=True))


    def lowest_centrality(self,centrality_dict):
        cent_items = [(b, a) for (a, b) in centrality_dict.iteritems() if b == min(centrality_dict.values())]
        cent_items.sort()
        return tuple((cent_items))


    def get_routing_path_between_two_endpoints(self,srcNode,dstNode):
        path = nx.dijkstra_path(self.graph, srcNode, dstNode)
        return path


    def get_switches_ports(self):
        for edge in self.edges:
            headedge_id = edge['edge']['headNodeConnector']['node']['id']
            tailedge_id = edge['edge']['tailNodeConnector']['node']['id']
            if(self.switches_ports.get(headedge_id)==""):
                self.switches_ports[headedge_id] = {}
            self.switches_ports[headedge_id][edge['properties']['name']['value']] = {'bandwidth':headedge_id['properties']['bandwidth']['value']}
            if(self.switches_ports.get(tailedge_id)==""):
                self.switches_ports[tailedge_id] = {}
            self.switches_ports[tailedge_id][edge['properties']['name']['value']] = {'bandwidth':tailedge_id['properties']['bandwidth']['value']}








