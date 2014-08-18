#!/usr/bin/env python
from __future__ import print_function

import json
import sys
from collections import namedtuple

NULL = None

class YinObj(namedtuple('YinObj', ['place', 'parent', 'ctxt', 'data'])):

    def send(self, wrld, msg, tgt):
        pass

    def run(self, wrld, tgt):
        pass

    def gen(self, wrld, **kwargs):
        new_place = wrld.place()
        return new_place, self._replace(**kwargs)

class DoBlock(YinObj):

    def send(self, wrld, msg, tgt):
        nmsg_tgt, nmsg = msg.gen(parent=self.parent)
        nmsg.run(wrld, nmsg_tgt)
        wrld.write(tgt, self._replace(parent=nmsg_tgt))

class World(object):

    class Place(namedtuple('Place', ['wrld', 'loc'])):
        pass

    def __init__(self):
        self.objs = {}
        self.last_loc = 0

    def write(self, k, v):
        self.objs[k] = v

    def _read(self, loc):
        return self.objs[loc]

    def place(self):
        loc, self.last_loc = self.last_loc, self.last_loc + 1
        return Place(wrld=self, loc=loc)


class Context(object):

    def __init__(self):
        self.reads = []
        self.sends = []
        self.makes = []
        self.diffs = []

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

def wrap(op, wrld, ctxt):
    if isinstance(op, list):
        # message send
        pass

def main():
    with open(sys.argv[1]) as f:
        program = json.load(f)
    print(program)
    ctxt = Context()
    wrld = World()
    place = wrld.place()
    do = DoBlock(place=place, parent=None, ctxt=ctxt, data=None)
    for op in program:
        do.send(wrld, wrap(op, wrld, ctxt), place)

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

# First, create the event graph completely. No evaluation is done in the
# process. Then, search for ready sends (a send where the destination and
# source are both filled). Evaluate these sends in no particular order.
# Are reads actually necessary?
# Then,
# perform a tradition evaluation process (transform into head
# normal form).


# Recursively transofrm the ast into a event-graph.
# All of the events in the event graph are conceptually in the same world.
# Worlds can be implemented later as distinct evaluation queues or something,
# so there's no need to record which world any event belongs to.
# We do, however, need to record the lexical context in which each variable
# appears. The real question is how we record the details of the graph
# structure, including the lexical path.

# Attempt 1:
# data World = Map ID Object
# data Object = Composite | Event | Atom
# data Atom = Symbol | Int | Alien
# data Symbol = String -- (in the underlying language)
# data Int = int -- (in the underlying language)
# data Event = Send | Make | Change
# data Send = { target :: ID; msg :: ID; dest :: ID; ctxt :: ID; }
# data Make = { target :: ID; send :: ID; ctxt :: ID; }
# data Change = { target :: ID; source :: ID; ctxt :: ID; }
# data Composite = { lazy :: ID; strict :: ID; byValue :: Map Object ID;
# byType :: Map Object ID; int :: ID; alien :: ID; symbol :: ID; id :: ID; }
# The type of byValue implies that it is not possible to apply a Change to the
# key of a Composite. This is an acceptable limitation, since the Composite
# itself should probably be changed instead.
# Originally, this design used SortedMaps instead of Maps, and defined a whole
# bunch of arbitrary orderings. After some thought, this is not needed in the
# core.
# Composites, Events, and Atoms
# have arbitrary orderings w.r.t. each other. Within Events, there is a stable
# (w.r.t. value) (but arbitrary) ordering. Each type of Atom has a consistent
# ordering within itself. Int's are ordered by value. Alien's are ordered by
# an override field. Symbol's are ordered arbitrarily.
