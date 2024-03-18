#!/usr/bin/python

import sys
import string
import os
import shutil


class Model:
    # constructor reads an abaqus model from an inp file

    READNODES = 1
    READELEMS = 2
    READELSET = 3
    IGNORE = 0

    def __init__(self, fin):
        """Read the file:
        """
        readMode = Model.IGNORE

        self.Nodes = {}
        self.Elems = {}
        self.ESets = {}
        elset_name = ""
        etype = ""

        buff = self.GetLine(fin)

        while buff != None:

            buff = buff.rstrip('\n')

            # split line using comma delimiter

            vals = buff.split(',')

            # remove leading or trailing white space
            # and convert to lower case

            for i in range(0, len(vals)):
                vals[i] = vals[i].strip().lower()

            # look for *Node or *Element or *Elset
            # and set the readMode flag

            if len(vals) >= 1 and vals[0][0] == '*':
                if vals[0][0:5] == '*node':
                    readMode = Model.READNODES

                elif vals[0][0:8] == '*element':
                    if len(vals) > 1:
                        # *Element, type=c3d20
                        tmp, et = vals[1].split('=')
                        if tmp == "type":
                            etype = et.strip()
                    readMode = Model.READELEMS

                elif vals[0][0:6] == '*elset':
                    if len(vals) > 1:
                        tmp, ename = vals[1].split('=')
                        elset_name = ename.strip()
                        self.ESets[elset_name] = []
                    readMode = Model.READELSET

                elif vals[0][0:5] == '*step':
                    break
                else:
                    readMode = Model.IGNORE

            # read actual data for current readMode

            else:
                if readMode == Model.READNODES:
                    nid = int(vals[0])
                    self.Nodes[nid] = [float(vals[1]), float(vals[2]), float(vals[3])]

                elif readMode == Model.READELEMS:
                    eid = int(vals[0])
                    self.Elems[eid] = []
                    for i in range(1, len(vals)):
                        if len(vals[i]) > 0:
                            self.Elems[eid].append(vals[i])
                    if etype == "c3d20" and len(vals) < 20:
                        # read extra line if needed
                        buff = self.GetLine(fin)
                        s = buff.strip('')
                        vals = s.split(',')
                        for i in range(0, len(vals)):
                            if len(vals[i]) > 0:
                                self.Elems[eid].append(vals[i])

                elif readMode == Model.READELSET:
                    if elset_name == "":
                        readMode = Model.IGNORE
                        continue
                    for i in range(0, len(vals)):
                        if len(vals[i]) > 0:
                            self.ESets[elset_name].append(vals[i])

            buff = self.GetLine(fin)

    def MoveSection(self, sect_elset, xoff, yoff, zoff):
        elist = []
        if sect_elset in self.ESets:
            elist = self.ESets.get(sect_elset)
        else:
            print
            sect_elset, ' not found '

        unique_nids = {}
        for e in elist:
            eid = int(e)
            if eid in self.Elems:
                el_nds = self.Elems.get(eid)
                for n in el_nds:
                    nid = int(n)
                    if nid in self.Nodes:
                        unique_nids[nid] = nid
                    else:
                        print
                        nid, ' not found'
            else:
                print
                eid, ' not found'

        for nid in unique_nids:
            nd = self.Nodes.get(nid)
            nd[0] += xoff
            nd[1] += yoff
            nd[2] += zoff

    def GetLine(self, fin):
        """this is a little helper function that scans the input
           file and ignores lines starting with a '#'"""
        buff = fin.readline()
        if len(buff) == 0: return None
        while buff[0] == '#':
            buff = fin.readline()
            if len(buff) == 0: return None
        return buff

    def GetNodes(self):

        return self.Nodes

    def GetElems(self):

        return self.Elems

    def GetESets(self):

        return self.ESets


if __name__ == '__main__':

    verbose = None
    if "-v" in sys.argv: verbose = 1

    # define data for current model

    sect_elset = "PART-1-1_M2_sect"
    xoff = 0.0
    yoff = 0.0
    zoff = -3.0

    contact_output = []
    contact_output.append("*Surface Interaction, name=IntProp-1 \n")
    contact_output.append("1., \n")
    contact_output.append("*Friction, slip tolerance=0.005 \n")
    contact_output.append("0.73, \n")
    contact_output.append("*Surface Behavior, pressure-overclosure=HARD \n")
    contact_output.append("*Contact Pair, interaction=IntProp-1, small sliding, type=SURFACE TO SURFACE, adjust=0.0 \n")
    contact_output.append("p1_surf, p2_surf \n")

    constraint_output = []
    constraint_output.append("*Tie, name=Constraint-1, adjust=yes \n")
    constraint_output.append("P2_SURF, P1_SURF \n")

    # read the input file

    fin = open(sys.argv[1])

    aba_inp = Model(fin)

    # verify data exists
    nds = aba_inp.GetNodes()
    # print nds
    els = aba_inp.GetElems()
    # print els.get(5085)
    esets = aba_inp.GetESets()
    # print esets.keys()

    # move the desired section_set

    aba_inp.MoveSection(sect_elset.lower(), xoff, yoff, zoff)

    # rewind file

    fin.seek(0, 0)

    # edit node coordinates

    buff = fin.readlines()
    readMode = 0
    output = []
    for lb in buff:
        vals = lb.split(',')
        if len(vals) >= 1 and vals[0][0] == '*' and readMode != 2:
            for i in range(0, len(vals)):
                vals[i] = vals[i].strip().lower()

            if vals[0][0:5] == '*node':
                readMode = 1

            elif vals[0][0:5] == '*step':
                # add contact data to output
                # for ci in contact_output:
                #    output.append(ci)
                # add constraint data to output
                for ci in constraint_output:
                    output.append(ci)
                readMode = 2

            else:
                readMode = 0

            output.append(lb)

        else:
            if readMode == 1:
                nid = int(vals[0])
                if nid in nds:
                    nd = nds.get(nid)
                    nstring = str(nid) + ", " + str(nd[0]) + ", " + str(nd[1]) + ", " + str(nd[2]) + "\n"
                    output.append(nstring)
                else:
                    output.append(lb)

            else:
                output.append(lb)

    fin.close()

    # copy original file

    cname = sys.argv[1] + "_orig"
    shutil.move(sys.argv[1], cname)

    # write back to file

    fout = open(sys.argv[1], 'w')
    for lo in output:
        fout.write("%s" % (lo))
    fout.close()


