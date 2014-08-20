#!/usr/bin/env python
from __future__ import print_function

import sys
import json

next_id = 1

def new_id():
    global next_id
    out, next_id = next_id, next_id + 1
    return out

class Object(object):
    pass

class Atom(Object):

    def __init__(self, inner):
        self.inner = inner

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, repr(self.inner))

    def evaluate(self):
        return self

    def __hash__(self):
        return hash(self.inner)

    def __eq__(self, other):
        if isinstance(other, Atom):
            return self.inner == other.inner

class YinException(Exception):
    pass

class World(object):

    def __init__(self):
        self._map = {}
        self._new_ids = []

    def __setitem__(self, ID, val):
        if ID in self._map:
            raise YinException("ID {0} already defined to be {1}".format(ID,
                self._map[ID]))
        self._new_ids.append(ID)
        self._map[ID] = val

    def __getitem__(self, ID):
        return self._map[ID]

    def __contains__(self, ID):
        return ID in self._map

    def items(self):
        return list(self._map.items())

    def pop_new_ids(self):
        ids, self._new_ids = self._new_ids, []
        return ids

    def __repr__(self):
        return '<World {0} {1}>'.format(repr(self._map), repr(self._new_ids))


class Root(Object):

    def send(self, msg):
        if isinstance(msg, AlienFunction):
            msg.execute()


class Alien(Atom):
    pass


class Symbol(Atom):
    pass


class Int(Atom):
    pass


class AlienFunction(Alien):

    def send(self, msg):
        return AlienFunction((self.inner[0], tuple(self.inner[1] + [msg])))

    def execute(self):
        #print('executing', self)
        self.inner[0](*self.inner[1])


class Map(object):

    def __init__(self, mapping, nxt):
        self._next = nxt
        self._map = mapping

    def send(self, msg):
        v = msg.evaluate()
        try:
            return self._map[v]
        except KeyError:
            return self._next.send(v)

    def __repr__(self):
        return 'Map({0}, {1})'.format(repr(self._map), repr(self._next))


class Event(Object):
    pass


class Send(Event):

    def __init__(self, target, msg, dest):
        self.target = target
        self.msg = msg
        self.dest = dest

    def __repr__(self):
        return 'Send(target={0}, msg={1}, dest={2})'.format(repr(self.target),
                repr(self.msg),
                repr(self.dest))


class Make(Event):

    def __init__(self, target, send):
        self.target = target
        self.send = send

    def __repr__(self):
        return 'Make(target={0}, send={1})'.format(repr(self.target),
                repr(self.send))


class Change(Event):

    def __init__(self, target, source):
        self.target = target
        self.source = source

    def __repr__(self):
        return 'Change(target={0}, source={1})'.format(repr(self.target),
                repr(self.source))


def add_obj(wrld, obj):
    ID = new_id()
    wrld[ID] = obj
    return ID


def do_send(world, s_i):
    send = world[s_i]
    if send.target not in world or send.msg not in world:
        for i, s in world.items():
            if isinstance(s, Send) and (s.dest == send.target or s.dest ==
                    send.msg):
                do_send(world, i)
    #print(world[send.target])
    world[send.dest] = world[send.target].send(world[send.msg])


def main():
    with open(sys.argv[1]) as f:
        program = json.load(f)
    world = World()
    root = Root()
    ground = Map({Symbol('print'): AlienFunction((print, []))}, root)
    ground_id = add_obj(world, ground)

    inter = new_id()
    s3_id = add_obj(world, Send(ground_id, inter, 0))

    target = new_id()
    msg = new_id()
    s_id = add_obj(world, Send(target, msg, inter))
    p_id = add_obj(world, Symbol('print'))
    s2_id = add_obj(world, Send(ground_id, p_id, target))
    world[msg] = Int(1)
    #print(world)
    #do_send(world, s_id)
    do_send(world, s3_id)

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
# data World = 'Map(ID, Object)
# data Object = Map | Event | Atom | TypeMap
# data Atom = Symbol | Int | Alien
# data Symbol = 'String
# data Int = 'Int
# data ID = 'Int
# data Event = Send | Make | Change
# data Send = { target : ID; msg : ID; dest : ID; }
# data Make = { target : ID; send : ID; }
# data Change = { target : ID; source : ID; }
# data Map = { 'Map(Object, ID); next : ID }
# data TypeMap = { int : ID; alien : ID; symbol : ID; next : ID }

# Steps to process [["print", 1]]
# Construct world, root, ground
# Visit ["print", 1]
# Begin constructing send
#   New ID for target
#   target = new_id()
#   msg = new_id()
#   s_id = add_obj(world, Send{target=target, dest=ground.ID, msg=msg})
#   Construct target of send.
#     Begin constructing send.
#     Create Symbol
#     p_id = add_obj(world, Symbol("print"))
#     Send{target=ground.ID, dest=target, msg=p_id}
#   Done constructing target of send.
#   Construct msg of send.
#     add_obj(world, Int(1), msg)
#   Done constructing msg of send.
# Done constructing send.
# Root expression fully constructed, evaluate.
#   Check s_id is evaluatable. No, target does not exist.
#   Evaluate Send where send.dest == world.get(s_id).target.
#     Target of send is a Map, so evaluate the msg.
#     msg is an Atom, and thus already evaluated.
#     Lookup Symbol("print") in the 'Map.
#     store result of lookup into send.dest
#   Done evaluating inner Send.
#   Check if send world[s_id] is evaluatable. Target exists, so perform the send.
#   Target is a Alien. Call the underlying send method, which returns another
#   Alien (an "action"). Send that Alien to the dest (ground).
#   Call the underlying ground is a Map, so evaluate the msg. 
#   The msg is an alien, call it's eval method.
#   Take the result of calling the eval method, and attempt to match it with
#   ground.
#   No match, so proceed to ground.next -> root.
#   Call root.send with alien. Root performs actual printing.
# Evaluating complete.
