################################################################
##connect to nodes & send crafted RPC using paramiko directly
##This version doesn't print to terminal but only to file
##Mohamed M. Morsy 
################################################################
##Only used for BGP RIB currently since ncclient waits for 
##full result so the client will likely overflow its buffers
##if results are so large
################################################################

import paramiko
import socket
import argparse
import sys,signal
import time
import xml.etree.ElementTree as ET

class NetconfRaw():

    ##standard RPCs to use with different calls
    CLOSE = """
    <?xml version="1.0" encoding="UTF-8"?>
    <rpc>
      <close-session/>
    </rpc>
    ]]>]]>
    """
    HELLO = """
    <?xml version="1.0" encoding="UTF-8"?>
    <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <capabilities>
    <capability>urn:ietf:params:netconf:base:1.0</capability>
    </capabilities>
    </hello>
    ]]>]]>
    """

    def __init__(self, ipaddress, username, password):
        self.ROUTER_IP = ipaddress
        self.USERNAME = username
        self.PASSWORD = password
        self.fileName = "bgp_routes_"+self.ROUTER_IP+".xml"

    def connectionattempt(self):
        ##attempting netconf session establishment using paramiko SSHClient
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            socketopen = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            socketopen.connect((self.ROUTER_IP, 830))
            trans = paramiko.Transport(socketopen)
            trans.connect(username=self.USERNAME, password=self.PASSWORD)
            #CREATE CHANNEL FOR DATA COMM
            ch = trans.open_session()
            # name = ch.set_name('netconf')
            #Invoke NETCONF
            ch.invoke_subsystem('netconf')
            print("connection attempt Ok")
            return ch
        except:
            print ("Failed to connect to target device")
            exit()

    def hellosender(self, ch):
        data = ch.recv(128)
        print("Hello sender Ok")
        while data:
            data = ch.recv(128)
            if data.decode("utf8").count("</hello>") == 1:
                ch.send(self.HELLO)
                break
            
    def sendRPC(self, ch, inRPC):
        Template = """
        <?xml version="1.0" encoding="UTF-8"?>
        <rpc message-id="bgp-rib" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <get>
            <filter type="subtree">
              RPCFILTER
          </filter>
        </get>
        </rpc>
        ]]>]]>
        """ 
        RPC = Template.replace("RPCFILTER", inRPC)
        print(RPC)
        fhandler = open(self.fileName,"w")
        ch.send(RPC)
        data = ch.recv(128)
        fhandler.write(data.decode("utf8"))
        fhandler.flush()
        fhandler.close()
        print("send RPC Ok")
        return True

    def reciever(self, ch):
        fhandler = open(self.fileName,"a")
        print("recieving")
        data = ch.recv(128)
        while "</rpc-reply>" not in data.decode("utf8"):
            data = ch.recv(128)
            fhandler.write(data.decode("utf8"))
            fhandler.flush() 
        fhandler.close()
        print("Done collecting")
        exit()    
