#!/usr/bin/env python
from __future__ import print_function

import json
import sys
from collections import namedtuple

NULL = None

class YinObj(object):

    def __init__(self, data=None, prev=None, place=None):
        self.data = data
        self.prev = prev
        self.place = place
        self.vals = {}

    def set(self, i, v):
        self.vals[i] = v

    def get(self, i, depth=0):
        try:
            return self.vals[i]
        except KeyError:
            if self.prev is not None:
                return self.prev.get(i, depth + 1)
            else:
                return NULL

    def send(self, val):
        pass

    def change(self, val):
        pass


class Wrld(YinObj):
    pass


class Atom(YinObj):
    pass


class CoreNum(YinObj):
    pass


class String(YinObj):
    pass


class Program(YinObj):
    pass


class Extern(YinObj):
    pass


def make_root_obj():
    o = YinObj()
    o.set('print', Extern(print))


Operation = namedtuple('Operation', ['val', 'tgt', 'src', 'wrld', 'ctxt'])


class Read(Operation):
    pass


class Send(Operation):
    pass


class Diff(Operation):
    pass


class Make(Operation):
    pass

class Eval(Operation):
    pass

class Place(namedtuple('Place', ['wrld', 'id'])):
    pass

class DoBlock(YinObj):

    def send(self, val):
        val._replace(prev=self.prev, place=Place)

class Evaluator(object):

    def __init__(self):
        self.reads = []
        self.sends = []
        self.makes = []
        self.diffs = []
        self.wrlds = {0: Wrld()}
        self.evals = []
        self.mid = 1
        self.wrlds[0].set(0, make_root_obj())

    def new_id(self):
        o, self.mid = self.mid, self.mid + 1
        return o

    def new_read(self, tgt, src, wrld, ctxt):
        self.reads.append(Read(tgt, src, wrld, ctxt))

    def new_send(self, val, tgt, src, wrld, ctxt):
        self.sends.append(Send(val, tgt, src, wrld, ctxt))

    def new_diff(self, val, tgt, src, wrld, ctxt):
        self.diffs.append(Diff(val, tgt, src, wrld, ctxt))

    def new_make(self, val, tgt, src, wrld, ctxt):
        self.makes.append(Make(val, tgt, src, wrld, ctxt))

    def new_eval(self, val, tgt, wrld, ctxt):
        self.evals.append(Make(val, tgt, wrld, ctxt))

    def inject(self, data, wrld=0, ctxt=0):
        for field, val in data.items():
            if field[0] != '.':
                raise NotImplemented
            ID = self.new_id()
            # TODO(kzentner): Change this to sends
            self.wrlds[wrld].get(ctxt).set(field, ID)
            self.new_eval(val=val, tgt=ID, wrld=wrld, ctxt=ctxt)

    def get_wrld(self, ID):
        return self.wrlds[ID]


def main():
    with open(sys.argv[1]) as f:
        p = json.load(f)
    print(p)
    e = Evaluator()
    e.inject(p)
    while not e.done():
        e.step()

if __name__ == '__main__':
    main()



# Create root object.
# Root object has a new message sent to it.
## The new object contains a "pending reaction".
## The pending reaction is to send the result of 1 to the result of "print".
## A pending send is created.
### 1 is a number, so a CoreNum is created, and is placed in the source of the 
### send.
### print is a variable, so a send is created to the current context, with the
### target being a new location. The target of the send is set to the
### destination of a read from that send.
### print is a variable, so an Identifier in the current context is created, 
### and placed in the target of the send.

# Structuring complete. We now have a running program.
## Check all existing sends. None are free to execute.
## Check all existing reads. None are free to execute.
## Freeze root object.
## Check all existing lookups.
## Check all existing sends. None are free to execute.
## Check all existing reads. print's parent context (root) is frozen, so that 
## read can complete.


# Four basic operations:
# send: val, tgt, dest, ctxt, wrld
# read: tgt, dest, wrld
# diff: val, tgt, wrld
# make: val, tgt, dest

# Operations are defined to be performed.
