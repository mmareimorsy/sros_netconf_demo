#######################################################
# wrapper for argument parsing to trigger netconf ops
# Mohamed M. Morsy
# Date: Feb 20th 2020
#######################################################

from sros_netconf import NetconfHandler
import argparse
import time
import json

def checkConnectionMinimum(args):
    if (args.ipaddress is None or args.username is None or args.password is None):
        print ("Minimum for usage is --node-ip & --username & --password")
        exit(-1)
    
def main():
    ## Setting up command line arguments
    parser = argparse.ArgumentParser(description="Netconf Demo operations", usage="--help to list available commands")
    parser.add_argument("--node_ip", dest="ipaddress", type=str, help="IP address of the DUT")
    parser.add_argument("--username", dest="username", type=str, help="Username of the DUT")
    parser.add_argument("--password", dest="password", type=str, help="Password of the DUT")
    parser.add_argument("--get_config", type=bool, nargs="*", help="enable to print out running config")
    parser.add_argument("--get_state", type=bool, nargs="*", help="enable to print out state")
    parser.add_argument("--get_interface_stats", type=str, nargs="+", help="trigger interface counter collection ; input an interface name to pull counters , physical port numbering only is accepted")
    parser.add_argument("--get_bgp_neighbor_rib" , type=str, nargs="+", help="bgp neighbor address to pull recieved & active routes")
    parser.add_argument("--get_l3vpn_route_table", nargs="+", type=str, help="name of l3 vpn to pull its active routes")
    parser.add_argument("--config_community", type=str, nargs="+", help="pass community name to configure")
    parser.add_argument("--config_comm_members", type=str, nargs="+", help="pass members of community to configure")
    parser.add_argument("--config_bgp_peer", type=str,nargs="+" , help="bgp peer address to configure")
    parser.add_argument("--config_bgp_peer_local_as", type=str, nargs="+" ,help="local as number for the bgp peer to configure")
    parser.add_argument("--config_bgp_peer_remote_as", type=str, nargs="+", help="peer as number for the bgp peer to configure")
    parser.add_argument("--config_bgp_import_policy" ,  nargs="+" ,type=str, help="name of bgp import policy to apply for the peer")
    parser.add_argument("--config_bgp_export_policy" ,  nargs="+" ,type=str, help="name of bgp export policy to apply for the peer")
    parser.add_argument("--config_bgp_peer_group_name",  nargs="+" , type=str, help="name of the bgp group to use for bgp peer")
    parser.add_argument("--config_policy_statement", type=str, nargs="+" ,help="policy statement name to configure")
    parser.add_argument("--config_policy_statement_entry", type=str, nargs="+" , help="Entry ID for policy statement to configure")
    parser.add_argument("--config_policy_statement_action", type=str, nargs="+" , help="Entry action for policy statement to configure")
    parser.add_argument("--config_policy_statement_comm" , type=str, nargs="+" , help="bgp community name to use in the policy statement action")
    parser.add_argument("--config_phy_port",  nargs="+" ,type=str, help="name of the physical port to configure")
    parser.add_argument("--config_phy_port_mode",  nargs="+" ,type=str, help="mode of the port to configure, hybrid or access or network")
    parser.add_argument("--config_phy_port_mtu",  nargs="+" ,type=str, help="MTU of the port to configure")
    parser.add_argument("--config_phy_port_encap",  nargs="+" ,type=str, help="encapsulation of port, null, dot1q or qinq")
    parser.add_argument("--config_port_description",  nargs="+" ,type=str, help="description to apply on physical interface")
    parser.add_argument("--config_layer3_router_interface", nargs= "+", type=str, help="Router interface name to configure")
    parser.add_argument("--config_interface_vlan" , nargs="+" , type=str, help="vlan to apply on interface")
    parser.add_argument("--config_interface_port", nargs="+", type=str, help="port to use for the interface")
    parser.add_argument("--config_ipv4_address" , nargs="+", type=str, help="IPv4 address to apply on sub-interface")
    parser.add_argument("--config_ipv6_address" , nargs= "+", type=str, help="IPv6 address to apply on sub-interface")
    parser.add_argument("--config_pcc_lsp_name" , nargs="+", type=str, help="name to use for PCC init LSPs")
    parser.add_argument("--config_pcc_lsp_destination" , nargs="+", type=str, help="create PCC init LSPs to a remote destination")
    parser.add_argument("--config_pcc_lsp_path" , nargs="+", type=str, help="primary path for PCC init LSP")
    parser.add_argument("--config_srte_path_name" , type=str, help="name of SR-TE path to create")
    parser.add_argument("--config_srte_path_hops" , nargs="+", type=str, help="hop IP address")
    parser.add_argument("--config_srte_path_hop_type" , nargs="+", type=str, help="loose or strict hop type")
    args = parser.parse_args()
    
    
    ## Checking minimum requirements of node IP , username & password then establishing connection
    checkConnectionMinimum(args)
    srosConnection = NetconfHandler(args.ipaddress, args.username, args.password)
    ## Triggering actions based on the passed command line arguments with some local validations on inputs
    ## get based functions
    if args.get_state is not None:
        srosConnection.getState()
    if(args.get_config is not None):
        srosConnection.getConfig()
    if args.get_interface_stats is not None:
        srosConnection.interfaceCounters(args.get_interface_stats)
    if args.get_bgp_neighbor_rib is not None:
        srosConnection.bgpActiveRoutes(args.get_bgp_neighbor_rib) 
    if args.get_l3vpn_route_table is not None:
        srosConnection.l3vpnRouteTable(args.get_l3vpn_route_table)   
    
    ## edit-config based functions
    if args.config_community is not None:
        srosConnection.configureCommunity(args.config_community, args.config_comm_members)
    if args.config_policy_statement is not None:
        srosConnection.bgpRoutePolicy(args.config_policy_statement, args.config_policy_statement_entry, args.config_policy_statement_action, args.config_policy_statement_comm)
    if args.config_bgp_peer is not None:
        srosConnection.configureBgpPeer(args.config_bgp_peer_group_name, args.config_bgp_peer, args.config_bgp_peer_remote_as, args.config_bgp_peer_local_as, args.config_bgp_import_policy, args.config_bgp_export_policy)
    if args.config_phy_port is not None:
        srosConnection.createPort(args.config_phy_port, args.config_port_description, args.config_phy_port_encap, args.config_phy_port_mtu, args.config_phy_port_mode)
    if args.config_layer3_router_interface is not None:
        srosConnection.createRouterInterface(args.config_layer3_router_interface)
        if args.config_interface_port is not None or args.config_interface_vlan is not None:
            assert args.config_interface_port is not None and args.config_interface_vlan is not None , "Please use interface_port & interface_vlan together"
            srosConnection.createRouterInterfaceVLANs(args.config_layer3_router_interface, args.config_interface_port, args.config_interface_vlan)
        if args.config_ipv4_address is not None:
            srosConnection.assignV4Address(args.config_layer3_router_interface, args.config_ipv4_address)
        if args.config_ipv6_address is not None:
            srosConnection.assignV6Address(args.config_layer3_router_interface, args.config_ipv6_address)
    if args.config_srte_path_name is not None:
        srosConnection.createSrTePath(args.config_srte_path_name, args.config_srte_path_hops, args.config_srte_path_hop_type)
    if args.config_pcc_lsp_name is not None:
        srosConnection.createPCCinitLsp(args.config_pcc_lsp_name, args.config_pcc_lsp_destination, args.config_pcc_lsp_path)
    
    ## close netconf session as the last action if it hasn't been closed somewhere else already
    if srosConnection.testIfConnected() is True:
        srosConnection.disconnect()

if __name__ == "__main__":
    main()