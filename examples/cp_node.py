#!/usr/bin/env python
from __future__ import print_function

import sys
import time
from functools import partial
sys.path.append("../")
from pysyncobj import SyncObj, replicated


class ChargePointNode(SyncObj):

    def __init__(self, selfNodeAddr, otherNodeAddrs):
        super(ChargePointNode, self).__init__(selfNodeAddr, otherNodeAddrs)
        self.__id = "001"
    
    @replicated
    def add_node_to_cluster(self):
        pass

    @replicated
    def remove_node(self):
        pass

    def get_leader(self):
        pass

    def im_the_leader(self):
        return self._isLeader


def onAdd(res, err, cnt):
    print('onAdd %d:' % cnt, res, err)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: %s self_port partner1_port partner2_port ...' % sys.argv[0])
        sys.exit(-1)

    port = int(sys.argv[1])
    partners = ['localhost:%d' % int(p) for p in sys.argv[2:]]
    o = ChargePointNode('localhost:%d' % port, partners)
    n = 0
    old_value = -1
    while True:
        # time.sleep(0.005)
        time.sleep(2)
        if o.getCounter() != old_value:
            old_value = o.getCounter()
            print(old_value)
        if o._getLeader() is None:
            continue
        # if n < 2000:
        if n < 20:
            leader = o.getStatus()["leader"]
            partners_count = o.getStatus()["partner_nodes_count"]
            raft_term = o.getStatus()["raft_term"]
            print(f"LEADER: {leader}")
            print(f"PARTNERS COUNT: {partners_count}")
            print(f"RAFT TER: {raft_term}")
            o.addValue(10, n, callback=partial(onAdd, cnt=n))
        n += 1
        
        # if n % 200 == 0:
        # if True:
        #    print('Counter value:', o.getCounter(), o._getLeader(), o._getRaftLogSize(), o._getLastCommitIndex())
