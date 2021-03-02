#######################################################
# base class to handle few netconf tasks
# Mohamed M. Morsy
# Date: Feb 20th 2020
#######################################################
#######################################################
##BGP Rib is the only method using the sros_netconf_raw
##switch back to ncclient by uncommenting the relevant lines
#######################################################

# declaring imports
import sys, os, warnings, logging
import xml.etree.ElementTree as ET
from ncclient import manager
import argparse
import json
import time
import datetime
import lxml
import os
import copy 
from sros_netconf_raw import NetconfRaw

class NetconfHandler():
    __namespaces = {"config-r13":"\"urn:alcatel-lucent.com:sros:ns:yang:conf-r13\"", 
                    "state":"\"urn:nokia.com:sros:ns:yang:sr:state\"",
                    "config-nokia":"\"urn:nokia.com:sros:ns:yang:sr:conf\""}
    
    __templates_directory = os.getcwd() + "/templates/"

    __template_files = {"get_port_stats"                  :    __templates_directory + "get_port_stats.xml",
                  "get_bgp_base_neighbor_state"     :    __templates_directory + "get_bgp_neighbor_rib.xml",
                  "config_bgp_community"            :    __templates_directory + "config_bgp_community.xml",
                  "config_bgp_route_policy"         :    __templates_directory + "config_bgp_route_policy.xml",
                  "config_bgp_neighbor"             :    __templates_directory + "config_bgp_neighbor.xml",
                  "config_port"                     :    __templates_directory + "config_port.xml",
                  "get_l3vpn_route_table"           :    __templates_directory + "get_l3vpn_routes.xml",
                  "config_router_interface"         :    __templates_directory + "config_router_interface.xml",
                  "config_interface_vlan"           :    __templates_directory + "config_router_interface_vlan.xml",
                  "config_ipv4_address"             :    __templates_directory + "config_router_interface_v4.xml",
                  "config_ipv6_address"             :    __templates_directory + "config_router_interface_v6.xml",
                  "config_srte_path"                :    __templates_directory + "config_srte_path.xml",
                  "config_srte_lsp"                 :    __templates_directory + "config_srte_lsp.xml",
                  "config_srte_path_hop"            :    __templates_directory + "config_srte_path_hop.xml"}

    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.__username = username
        self.__password = password
        self.__connection = self.connect()
    
    def connect(self):
        try:
            connection = manager.connect(host=self.hostname, username=self.__username, password=self.__password, port=830, hostkey_verify=False, timeout=1800)
            print("Netconf session established to ", self.hostname)
            #connection.async_mode=True
            return connection
        except Exception as e:
            print ("couldn't establish connection to", self.hostname)
            print(e)
            exit(-1)

    def disconnect(self):
        if self.__connection is not None:
            self.__connection.close_session()
            print("Netconf session terminated to ", self.hostname)

    def testIfConnected(self):
        return self.__connection.connected

    def lockDataStore(self):
        try:
            result = self.__connection.lock(target="candidate")
            return result.ok
        except Exception as e:
            print(e)
            return False

    def unlockDataStore(self):
        try:
            result = self.__connection.unlock(target="candidate")
            return result.ok
        except Exception as e:
            print(e)
            return False
    
    def getConfig(self):
        try:
            currentConfig = self.__connection.get_config(source='running')
            print (currentConfig)
        except Exception as e:
            return e
    
    def getState(self):
        try:
            currentState = self.__connection.get()
            print(currentState)
        except Exception as e:
            print("failed in getting state from ", self.hostname)
            return e

    def configAndCommit(self, filterRPC):
        result = self.__connection.edit_config(target='candidate', config = filterRPC)
        print(result)
        if(result.ok is True):
            self.__connection.commit()
        else:
            raise Exception

    def interfaceCounters(self, interfaces):
        for interfaceName in interfaces:
            try:
                filterFile = open(self.__template_files["get_port_stats"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["get_port_stats"])
                print("skipping...." , interfaceName)
            try:
                RPCFilter = filterFile.read()
                RPCFilter = RPCFilter.replace("PORT_ID", interfaceName)\
                    .replace("NAMESPACE",self.__namespaces["state"])
                print(RPCFilter)
                result = self.__connection.get(filter = ('subtree',RPCFilter))
                print(result)
            except Exception as e:
                print("Failed in doing the get of interface state for interface " , interfaceName)
                print(e)

    def bgpActiveRoutes(self, neighbors):
        for neighbor in neighbors:
            try:
                bgpNeighborFilterFile = open(self.__template_files["get_bgp_base_neighbor_state"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["get_bgp_base_neighbor_state"])
                print("skipping....", neighbor)
            try:
                bgpNeighborFilter = bgpNeighborFilterFile.read()
                bgpNeighborFilter = bgpNeighborFilter.replace("NEIGHBOR-IP", neighbor)\
                    .replace("NAMESPACE", self.__namespaces["state"])
                rawConnection = NetconfRaw(self.hostname, self.__username, self.__password)
                ch = rawConnection.connectionattempt()
                rawConnection.hellosender(ch)
                rawConnection.sendRPC(ch, bgpNeighborFilter)
                rawConnection.reciever(ch)
                # bgpNeighborState = self.__connection.get(filter = ('subtree',bgpNeighborFilter))
                # print(bgpNeighborState)
            except Exception as e:
                print(e)
                print("Failed in doing the get of bgp neighbor state for " , neighbor)

    def configureCommunity(self, communityNames, communityMembers):
        assert len(communityNames) == len(communityMembers), "please make sure there is a member corresponding to each community name"
        for communityName, communityMember in zip(communityNames, communityMembers):
            try:
                filterFile = open(self.__template_files["config_bgp_community"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["config_bgp_community"])
                print("skipping....", communityName)
            try:
                filterRPC = filterFile.read()
                filterRPC = filterRPC.replace("NAMESPACE", self.__namespaces["config-nokia"])\
                .replace("COMMUNITY_NAME", communityName)\
                .replace("COMMUNITY", communityMember)
                print(filterRPC)
                result = self.__connection.edit_config(target='candidate', config = filterRPC)
                print(result)
                if(result.ok is True):
                    self.__connection.commit()
                else:
                    raise Exception
            except Exception as e:
                print(e)
                print("Failed in configuring community " , communityName)

    def configureBgpPeer(self, bgpGroups, bgpPeerAddresses, bgpRemoteAses, bgpLocalAses, importPolicies, exportPolicies):
        assert len(bgpGroups) > 0 , "BGP Group name is mandatory"
        assert len(bgpLocalAses) > 0 , "BGP Local AS is mandatory for peer"
        assert len(bgpRemoteAses) > 0 , "BGP Remote AS is mandatory for peer"
        assert len(importPolicies) > 0 , "BGP import policy is currently mandatory , TEMPORARY ONLY"
        assert len(exportPolicies) > 0 , "BGP export policy is currently mandatory, TEMPORARY ONLY"
        assert len(bgpPeerAddresses) > 0 , "BGP peer address is mandatory"
        assert len(bgpPeerAddresses) == len(bgpLocalAses) == len(bgpRemoteAses) == len(importPolicies) == len(exportPolicies) == len(bgpGroups), "count of peer parameters doesn't match"
        for bgpGroup, bgpLocalAs, bgpRemoteAs, importPolicy, exportPolicy, bgpPeerAddress in zip(bgpGroups, bgpLocalAses, bgpRemoteAses, importPolicies, exportPolicies, bgpPeerAddresses):
            try:
                filterFile = open(self.__template_files["config_bgp_neighbor"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["config_bgp_neighbor"])
                print("skipping....", bgpPeerAddress)
            try:
                filterRPC = filterFile.read()
                arguments = locals()
                filterRPC = filterRPC.replace("NAMESPACE", self.__namespaces["config-nokia"])\
                .replace("GROUP-NAME", bgpGroup)\
                .replace("NEIGHBOR-ADDRESS", bgpPeerAddress)\
                .replace("LOCAL-AS", str(bgpLocalAs))\
                .replace("PEER-AS", str(bgpRemoteAs))\
                .replace("IMPORT-POLICY",importPolicy)\
                .replace("EXPORT-POLICY", exportPolicy)
                print(filterRPC)
                result = self.__connection.edit_config(target='candidate', config = filterRPC)
                print(result)
                if(result.ok is True):
                    self.__connection.commit()
                else:
                    raise Exception
            except Exception as e:
                print(e)
                print("Failed in configuring bgp peer " , bgpPeerAddress)

    def bgpRoutePolicy(self, policyNames, entryIDs, actionTypes, communityNames):
        assert len(policyNames) > 0 , "You haven't entered a policy name to configure"
        assert len(entryIDs) > 0 , "You need to enter at least one entry to create"
        assert len(entryIDs) == len(actionTypes) , "Each Entry need to have exactyly one action"
        assert len(entryIDs) == len(communityNames), "Each Entry expects to have one community"
        for policyName, entryID, actionType, communityName in zip(policyNames, entryIDs, actionTypes, communityNames):
            try:
                filterFile = open(self.__template_files["config_bgp_route_policy"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["config_bgp_route_policy"])
                print("skipping....", policyName)
            try:
                filterRPC = filterFile.read()
                filterRPC = filterRPC.replace("NAMESPACE", self.__namespaces["config-nokia"])\
                .replace("POLICY_NAME", policyName)\
                .replace("ENTRY-ID", str(entryID))\
                .replace("ACTION-TYPE", actionType)\
                .replace("COMMUNITY", communityName)
                print(filterRPC)
                result = self.__connection.edit_config(target='candidate', config = filterRPC)
                print(result)
                if(result.ok is True):
                    self.__connection.commit()
                else:
                    raise Exception
            except Exception as e:
                print(e)
                print("Failed in configuring policy " , policyName)

    def createPort(self, portIDs, portDescriptions, portEncaps, portMTUs, portModes):
        assert len(portIDs) == len(portDescriptions) == len(portEncaps) == len(portMTUs) == len(portModes)
        for portID, portDescription, portEncap, portMtu, portMode in zip(portIDs, portDescriptions, portEncaps, portMTUs, portModes):
            assert portMode == "access" or portMode == "hybrid" or portMode == "network"
            assert portEncap == "null" or portEncap == "dot1q" or portEncap == "qinq"
            try:
                filterFile = open(self.__template_files["config_port"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["config_port"])
                print("skipping....", portID)
            try:
                filterRPC = filterFile.read()
                filterRPC = filterRPC.replace("NAMESPACE", self.__namespaces["config-nokia"])\
                .replace("PORTID", portID)\
                .replace("CONNECTORID", portID + "/1")\
                .replace("DESCRIPTION", portDescription)\
                .replace("ENCAP", portEncap)\
                .replace("MTU", portMtu)\
                .replace("MODE", portMode)
                print(filterRPC)
                result = self.__connection.edit_config(target='candidate', config = filterRPC)
                print(result)
                if(result.ok is True):
                    self.__connection.commit()
                else:
                    raise Exception
            except Exception as e:
                print(e)
                print("Failed in configuring port " , portID)

    def createRouterInterface(self, interfaceNames):
        for interfaceName in interfaceNames:
            try:
                filterFile = open(self.__template_files["config_router_interface"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["config_router_interface"])
                print("skipping....", interfaceName)
            try:
                filterRPC = filterFile.read()
                filterRPC = filterRPC.replace("NAMESPACE", self.__namespaces["config-nokia"])\
                .replace("INTERFACE_NAME", interfaceName)
                print(filterRPC)
                result = self.__connection.edit_config(target='candidate', config = filterRPC)
                print(result)
                if(result.ok is True):
                    self.__connection.commit()
                else:
                    raise Exception
            except Exception as e:
                print(e)
                print("Failed in configuring port " , interfaceName)

    def createRouterInterfaceVLANs(self, interfaceNames, interfacePorts, interfaceVLANs):
        assert len(interfaceNames) == len(interfaceVLANs) == len(interfacePorts)
        for interfaceName, interfacePort, interfaceVLAN in zip(interfaceNames, interfacePorts, interfaceVLANs):
            try:
                filterFile = open(self.__template_files["config_interface_vlan"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["config_interface_vlan"])
                print("skipping....", interfaceName)
            try:
                filterRPC = filterFile.read()
                filterRPC = filterRPC.replace("NAMESPACE", self.__namespaces["config-nokia"])\
                .replace("INTERFACE_NAME", interfaceName)\
                .replace("PORTID", interfacePort + ":" + interfaceVLAN)
                print(filterRPC)
                result = self.__connection.edit_config(target='candidate', config = filterRPC)
                print(result)
                if(result.ok is True):
                    self.__connection.commit()
                else:
                    raise Exception
            except Exception as e:
                print(e)
                print("Failed in configuring port " , interfaceName)

    def assignV4Address(self, interfaceNames, addresses):
        assert len(interfaceNames) == len(addresses)
        for interfaceName, address in zip(interfaceNames, addresses):
            v4Address = address.split("/")[0]
            v4Prefix = address.split("/")[1]
            try:
                filterFile = open(self.__template_files["config_ipv4_address"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["config_ipv4_address"])
                print("skipping....", interfaceName)
            try:
                filterRPC = filterFile.read()
                filterRPC = filterRPC.replace("NAMESPACE", self.__namespaces["config-nokia"])\
                .replace("INTERFACE_NAME", interfaceName)\
                .replace("V4ADDRESS", v4Address)\
                .replace("PREFIXLENGTH", v4Prefix)
                print(filterRPC)
                result = self.__connection.edit_config(target='candidate', config = filterRPC)
                print(result)
                if(result.ok is True):
                    self.__connection.commit()
                else:
                    raise Exception
            except Exception as e:
                print(e)
                print("Failed in configuring port " , interfaceName)

    def assignV6Address(self, interfaceNames, addresses):
        assert len(interfaceNames) == len(addresses)
        for interfaceName, address in zip(interfaceNames, addresses):
            v6Address = address.split("/")[0]
            v6Address = v6Address.lower()
            v6Prefix = address.split("/")[1]
            try:
                filterFile = open(self.__template_files["config_ipv6_address"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["config_ipv6_address"])
                print("skipping....", interfaceName)
            try:
                filterRPC = filterFile.read()
                filterRPC = filterRPC.replace("NAMESPACE", self.__namespaces["config-nokia"])\
                .replace("INTERFACE_NAME", interfaceName)\
                .replace("V6ADDRESS", v6Address)\
                .replace("PREFIXLENGTH", v6Prefix)
                print(filterRPC)
                result = self.__connection.edit_config(target='candidate', config = filterRPC)
                print(result)
                if(result.ok is True):
                    self.__connection.commit()
                else:
                    raise Exception
            except Exception as e:
                print(e)
                print("Failed in configuring port " , interfaceName)

    def l3vpnRouteTable(self, l3vpns):
        for l3vpn in l3vpns:
            try:
                filterFile = open(self.__template_files["get_l3vpn_route_table"])
            except IOError as e:
                print(e)
                print("Failed to open template file in " , self.__template_files["get_l3vpn_route_table"])
                print("skipping....", l3vpn)
            try:
                filterRPC = filterFile.read()
                filterRPC = filterRPC.replace("SERVICENAME", l3vpn)\
                    .replace("NAMESPACE",self.__namespaces["state"])
                print(filterRPC)
                result = self.__connection.get(filter = ('subtree',filterRPC))
                print(result)
            except Exception as err:
                print(err)
                print("Failed in doing the get of l3 vpn route table", l3vpn)
    
    def createSrTePath(self, name, hops, actions):
        assert len(hops) == len(actions) , "please make sure each hop has exactly one action"
        try:
            pathFile = open(self.__template_files["config_srte_path"])
        except IOError as e:
            print(e)
            print("skipping....", name)    
        try:
            hopFile = open(self.__template_files["config_srte_path_hop"])
        except IOError as e:
            print(e)
            print("skipping....", name)    
        counter = 1
        builtHops = ""
        hopTemplate = hopFile.read()
        for hop, action in zip(hops, actions):            
            currentHop = copy.deepcopy(hopTemplate)
            currentHop = currentHop.replace("{{INDEX}}" , str(counter))\
                .replace("{{HOP}}", hop)\
                .replace("{{TYPE}}", action)
            counter += 1
            builtHops = builtHops + "\n" + currentHop 
        pathTemplate = pathFile.read()
        pathTemplate = pathTemplate.replace("{{NAMESPACE}}", self.__namespaces["config-nokia"])\
            .replace("{{PATHNAME}}", name)\
                .replace("{{HOP}}", builtHops)
        pathFile.close()
        hopFile.close()
        print(pathTemplate)
        try:
            result = self.__connection.edit_config(target='candidate', config = pathTemplate)
            print(result)
            if(result.ok is True):
                self.__connection.commit()
            else:
                raise Exception
        except Exception as e:
            print(e)
            print("Failed in configuring path " , name)

    def createPCCinitLsp(self, names, destinations, paths):
        assert len(names) == len(destinations) == len(paths), "please make sure each lsp has exactly one name, destination & path"
        print(names)
        print(destinations)
        print(paths)
        try:
            filterFile = open(self.__template_files["config_srte_lsp"])
        except IOError as e:
            print(e)
            print("skipping....")    
        filterRPCTemp = filterFile.read()
        for name, destination , path in zip(names, destinations, paths):            
            filterRPC = copy.deepcopy(filterRPCTemp)
            filterRPC = filterRPC.replace("{{NAMESPACE}}" , self.__namespaces["config-nokia"])\
                .replace("{{LSPNAME}}", name)\
                .replace("{{DESTINATION}}", destination)\
                .replace("{{PATHNAME}}", path)
            print(filterRPC)
            try:
                result = self.__connection.edit_config(target='candidate', config = filterRPC)
                print(result)
                if(result.ok is True):
                    self.__connection.commit()
                else:
                    raise Exception
            except Exception as e:
                print(e)
                print("Failed in configuring LSP " , name)