# sros_netconf_demo

This repo is a group of some sample methods to execute remote commands on Nokia SROS nodes via netconf, it is meant for someone who would like to see the RPCs as exchanged between a client & a netconf server (SROS in this case).

The methods rely mainly either on ncclient library or in some cases runs on top of paramiko directly without using ncclient.

To use:

python3 -m pip install -r requirements.txt

Netconf would need to be enabled & a user with netconf access need to be configured on the server & used from the client.

python3 -m netconf.py --help

This will list the currently available methods to expirement with

## Summary of what can be used:

* get running config
* get whole state of a box
* get counters from interfaces
* get v4 & v6 unicast route table from a VRF
* get BGP RIB of a box (Note that this doesn't use ncclient but rather done via paramiko, reasons related to running in asynchronous vs synchronous mode in ncclient, depending on how big is the RIB this operation could take some time, netconf is not ideal for such operation)
* configure a BGP peer group with communities & export & import policies
* configure interfaces with v4 & v6 addresses & bind them to vlans or null interfaces
* configure SR-TE LSPs & SR-TE path definitions (assuming SR-TE is enabled & running on the target node); configures only PCC initiated LSPs


## List of available commands

  -h, --help            show this help message and exit
  --node_ip IPADDRESS   IP address of the DUT
  --username USERNAME   Username of the DUT
  --password PASSWORD   Password of the DUT
  --get_config [GET_CONFIG [GET_CONFIG ...]]
                        enable to print out running config
  --get_state [GET_STATE [GET_STATE ...]]
                        enable to print out state
  --get_interface_stats GET_INTERFACE_STATS [GET_INTERFACE_STATS ...]
                        trigger interface counter collection ; input an
                        interface name to pull counters , physical port
                        numbering only is accepted
  --get_bgp_neighbor_rib GET_BGP_NEIGHBOR_RIB [GET_BGP_NEIGHBOR_RIB ...]
                        bgp neighbor address to pull recieved & active routes
  --get_l3vpn_route_table GET_L3VPN_ROUTE_TABLE [GET_L3VPN_ROUTE_TABLE ...]
                        name of l3 vpn to pull its active routes
  --config_community CONFIG_COMMUNITY [CONFIG_COMMUNITY ...]
                        pass community name to configure
  --config_comm_members CONFIG_COMM_MEMBERS [CONFIG_COMM_MEMBERS ...]
                        pass members of community to configure
  --config_bgp_peer CONFIG_BGP_PEER [CONFIG_BGP_PEER ...]
                        bgp peer address to configure
  --config_bgp_peer_local_as CONFIG_BGP_PEER_LOCAL_AS [CONFIG_BGP_PEER_LOCAL_AS ...]
                        local as number for the bgp peer to configure
  --config_bgp_peer_remote_as CONFIG_BGP_PEER_REMOTE_AS [CONFIG_BGP_PEER_REMOTE_AS ...]
                        peer as number for the bgp peer to configure
  --config_bgp_import_policy CONFIG_BGP_IMPORT_POLICY [CONFIG_BGP_IMPORT_POLICY ...]
                        name of bgp import policy to apply for the peer
  --config_bgp_export_policy CONFIG_BGP_EXPORT_POLICY [CONFIG_BGP_EXPORT_POLICY ...]
                        name of bgp export policy to apply for the peer
  --config_bgp_peer_group_name CONFIG_BGP_PEER_GROUP_NAME [CONFIG_BGP_PEER_GROUP_NAME ...]
                        name of the bgp group to use for bgp peer
  --config_policy_statement CONFIG_POLICY_STATEMENT [CONFIG_POLICY_STATEMENT ...]
                        policy statement name to configure
  --config_policy_statement_entry CONFIG_POLICY_STATEMENT_ENTRY [CONFIG_POLICY_STATEMENT_ENTRY ...]
                        Entry ID for policy statement to configure
  --config_policy_statement_action CONFIG_POLICY_STATEMENT_ACTION [CONFIG_POLICY_STATEMENT_ACTION ...]
                        Entry action for policy statement to configure
  --config_policy_statement_comm CONFIG_POLICY_STATEMENT_COMM [CONFIG_POLICY_STATEMENT_COMM ...]
                        bgp community name to use in the policy statement
                        action
  --config_phy_port CONFIG_PHY_PORT [CONFIG_PHY_PORT ...]
                        name of the physical port to configure
  --config_phy_port_mode CONFIG_PHY_PORT_MODE [CONFIG_PHY_PORT_MODE ...]
                        mode of the port to configure, hybrid or access or
                        network
  --config_phy_port_mtu CONFIG_PHY_PORT_MTU [CONFIG_PHY_PORT_MTU ...]
                        MTU of the port to configure
  --config_phy_port_encap CONFIG_PHY_PORT_ENCAP [CONFIG_PHY_PORT_ENCAP ...]
                        encapsulation of port, null, dot1q or qinq
  --config_port_description CONFIG_PORT_DESCRIPTION [CONFIG_PORT_DESCRIPTION ...]
                        description to apply on physical interface
  --config_layer3_router_interface CONFIG_LAYER3_ROUTER_INTERFACE [CONFIG_LAYER3_ROUTER_INTERFACE ...]
                        Router interface name to configure
  --config_interface_vlan CONFIG_INTERFACE_VLAN [CONFIG_INTERFACE_VLAN ...]
                        vlan to apply on interface
  --config_interface_port CONFIG_INTERFACE_PORT [CONFIG_INTERFACE_PORT ...]
                        port to use for the interface
  --config_ipv4_address CONFIG_IPV4_ADDRESS [CONFIG_IPV4_ADDRESS ...]
                        IPv4 address to apply on sub-interface
  --config_ipv6_address CONFIG_IPV6_ADDRESS [CONFIG_IPV6_ADDRESS ...]
                        IPv6 address to apply on sub-interface
  --config_pcc_lsp_name CONFIG_PCC_LSP_NAME [CONFIG_PCC_LSP_NAME ...]
                        name to use for PCC init LSPs
  --config_pcc_lsp_destination CONFIG_PCC_LSP_DESTINATION [CONFIG_PCC_LSP_DESTINATION ...]
                        create PCC init LSPs to a remote destination
  --config_pcc_lsp_path CONFIG_PCC_LSP_PATH [CONFIG_PCC_LSP_PATH ...]
                        primary path for PCC init LSP
  --config_srte_path_name CONFIG_SRTE_PATH_NAME
                        name of SR-TE path to create
  --config_srte_path_hops CONFIG_SRTE_PATH_HOPS [CONFIG_SRTE_PATH_HOPS ...]
                        hop IP address
  --config_srte_path_hop_type CONFIG_SRTE_PATH_HOP_TYPE [CONFIG_SRTE_PATH_HOP_TYPE ...]
                        loose or strict hop type
                        
                        
  Any command that starts with "get" will be basically targeting a state datastore so basically a get rpc, any command starting with config will be used for configuration on the candidate datastore then committed to running datastore (edit-config rpc)
  
  ## example
  
  python3 netconf.py --node_ip $(YOUR_NODE_IP) --username $(YOUR_NETCONF_USER) --password $(YOUR_NETCONF_PASS) --get_interface_stats 1/1/c1/1


<state xmlns="urn:nokia.com:sros:ns:yang:sr:state" >
<port>
    <port-id>1/1/c1/1</port-id>
    <ethernet>
        <statistics>
        </statistics>
    </ethernet>
</port>
</state>
<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply message-id="urn:uuid:d72809e9-0d33-453e-838e-c3bb8f95cc0b" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <data>
        <state xmlns="urn:nokia.com:sros:ns:yang:sr:state">
            <port>
                <port-id>1/1/c1/1</port-id>
                <ethernet>
                    <statistics>
                        <in-broadcast-packets>0</in-broadcast-packets>
                        <in-multicast-packets>0</in-multicast-packets>
                        <in-unicast-packets>0</in-unicast-packets>
                        <in-errors>0</in-errors>
                        <in-octets>0</in-octets>
                        <in-utilization>0</in-utilization>
                        <out-broadcast-packets>0</out-broadcast-packets>
                        <out-multicast-packets>0</out-multicast-packets>
                        <out-unicast-packets>0</out-unicast-packets>
                        <out-errors>0</out-errors>
                        <out-octets>0</out-octets>
                        <out-utilization>0</out-utilization>
                        <collisions>0</collisions>
                        <crc-align-errors>0</crc-align-errors>
                        <drop-events>0</drop-events>
                        <fragments>0</fragments>
                        <jabbers>0</jabbers>
                        <oversize-packets>0</oversize-packets>
                        <undersize-packets>0</undersize-packets>
                        <total-broadcast-packets>0</total-broadcast-packets>
                        <total-multicast-packets>0</total-multicast-packets>
                        <total-octets>0</total-octets>
                        <total-packets>0</total-packets>
                        <ethernet-like-medium>
                            <frame-too-long>0</frame-too-long>
                            <collision>
                                <excessive>0</excessive>
                                <late>0</late>
                                <multiple>0</multiple>
                                <single>0</single>
                            </collision>
                            <error>
                                <alignment>0</alignment>
                                <carrier-sense>0</carrier-sense>
                                <fcs>0</fcs>
                                <internal-mac-transmitted>0</internal-mac-transmitted>
                                <sqe-test>0</sqe-test>
                                <symbol>0</symbol>
                            </error>
                            <pause>
                                <frames-received>0</frames-received>
                                <frames-transmitted>0</frames-transmitted>
                            </pause>
                        </ethernet-like-medium>
                        <packet-size>
                            <octets-64>0</octets-64>
                            <octets-65-to-127>0</octets-65-to-127>
                            <octets-128-to-255>0</octets-128-to-255>
                            <octets-256-to-511>0</octets-256-to-511>
                            <octets-512-to-1023>0</octets-512-to-1023>
                            <octets-1024-to-1518>0</octets-1024-to-1518>
                            <octets-1519-to-max>0</octets-1519-to-max>
                        </packet-size>
                    </statistics>
                </ethernet>
            </port>
        </state>
    </data>
</rpc-reply>