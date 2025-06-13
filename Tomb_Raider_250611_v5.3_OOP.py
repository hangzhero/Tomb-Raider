from time import time

class Matter():
    def __init__(self, i, j, face):
        self.i = i
        self.j = j
        self.face = face

    def str(self):
        return f'{(self.face, self.pos())}'

    def pos(self):
        return (self.i, self.j)
        
    def __repr__(self):
        return self.str()

class Mirror(Matter):
    
    def __init__(self, i, j, face):
        super().__init__(i, j, face)    
        self.up = self.dn = self.ft = self.bk = '' # initialize the nearest matter around it as ''
        self.done_setup = False
        self.visited = []
        
    def setup(self):        
        if self.face == '/':
            self.reflect = {top: (self.ft, lt), btm: (self.bk, rt), lt: (self.up, top), rt: (self.dn, btm)}
        elif self.face == '\\':
            self.reflect = {top: (self.bk, rt), btm: (self.ft, lt), lt: (self.dn, btm), rt: (self.up, top)}
        else: # self.face == '#'
            self.reflect = {top: ('#', False), btm: ('#', False), lt: ('#', False), rt: ('#', False)}

    def mark_visit(self, d):
        return self.visited.append(d)

    def get_opp(self, d):
        return {top: btm, btm: top, lt: rt, rt: lt}[d]

    def _pointing(self, out_direction):
        if out_direction == top:
            return self.up
        elif out_direction == btm:
            return self.dn
        elif out_direction == lt:
            return self.ft
        elif out_direction == rt:
            return self.bk

    def reflecting(self, outward_d):
        if not self.done_setup: self.setup()
        return self.reflect[outward_d]

    def inward(self, in_direction):
        return self._pointing(self.get_opp(in_direction)) ## out_direction = lt, point to self.ft
       
    def outward(self, out_direction):
        return self._pointing(out_direction) ## out_direction = lt, point to self.ft

## The chain is Gargoyle to header to master, bubble up to top master by master.master where the groups information is recorded 
class Header(Matter):  ## define the header, such that header and master could be different
    def __init__(self, i, j, face):
        super().__init__(i, j, face)
        self.rotate_face = 'V' if face == 'H' else 'H'
        self.groups = {self.face: 1, self.rotate_face: 0}  # store the count of faces same as self.face or self.rotate_face
        self.blocked_face = ''
        self.master = ''
        self.type = 'master' #can be slave
        self.flipped = False #flip relationship to its upper node, aka. its master node
        ## it is now a tree structure, each node record its flip status, then accmulate it to the root node.

    def facing(self, outward_d):
        return 'V' if outward_d in (top, btm) else 'H'
        
    def rotate(self, face):
        return 'V' if face == 'H' else 'H'        

    def set_slave(self, new_master, flip):
        self.master = new_master  # link self as a child node to new_master
        self.flipped = flip
        self.type = 'slave'
        del self.blocked_face, self.groups

##    def rotate_face(self, face):
##        return 'V' if self.blocked_face == 'H' else 'V' if self.blocked_face == 'H' else ''
##    ## wrong, only master has blocked_face

    def add_blocked_face(self, d):
        new_blocked_face = self.facing(d)
        
        self_flips, self_root = self.flip_toMaster()
        ultimate_flip = (self_flips % 2 == 1)

        if ultimate_flip:
            new_blocked_face = self.rotate(new_blocked_face)
        
        if self_root.blocked_face and self_root.blocked_face != new_blocked_face:
            return True
        else:
            self_root.blocked_face = new_blocked_face
            return False


    def flip_toMaster(self):
        prev = self
        count = 0 + prev.flipped
        nxt = self.master
        while nxt:
            prev = nxt
            count += prev.flipped
            nxt = prev.master      
        return count % 2 == 1, prev

        
    def reconcile(self, h, flip):  # merge h's master into self's master, h and self both remains as header

        self_flips, self_root = self.flip_toMaster()
        h_flips, h_root = h.flip_toMaster()

        ultimate_flip = (sum([flip, self_flips, h_flips]) % 2 == 1)
        
        ### need to handle, first mirror merge into same group and flip == True
        ### second mirror, already same group, but flip == True
        ### /H
        ### V/
        ### compare the header which determine its group's flipping status to master

        if self_root == h_root:  ## same master, compare the header            
            if ultimate_flip: 
                return True
            else: # flip = False, self and h in the same group
                return False
        else: ## old ! = new, different master
##            if (flip and self not in new.peers_flipped) or (not flip and self in new.peers_flipped):

            if h_root.blocked_face:
                h_root_blocked_face = h_root.rotate(h_root.blocked_face) if ultimate_flip else h_root.blocked_face
            else:
                h_root_blocked_face = ''
           
            if self_root.blocked_face and h_root_blocked_face and (self_root.blocked_face != h_root_blocked_face):
                return True  # only same blocked face allowed, different just die
            else:
                self_root.blocked_face = self_root.blocked_face or h_root_blocked_face  # inherit one of the blocked face

            if ultimate_flip:               
                self_root.groups[self_root.face] += h_root.groups[self_root.rotate_face]           
                self_root.groups[self_root.rotate_face] += h_root.groups[self_root.face]              
          
            else: ## (not flip and self not in new.peers_flipped) or (flip and self not in new.peers_flipped)
                self_root.groups[self_root.face] += h_root.groups[self_root.face]
                self_root.groups[self_root.rotate_face] += h_root.groups[self_root.rotate_face]

            h_root.set_slave(self_root, ultimate_flip)  # must locate at the end
                                    #important step, keep the head, but changed the master           
            return False

def initialize(m, r, c): # to get who is the neighbour of each element s

    mirror_faces = ('\\', '/', '#')
    
    mds = []    # [(mirror, outward_d)]
    gms = []    # [header], could be master or slave
    
    aboves = [ '.' for j in range(c) ]  ## above, prev is the header tracker

    for i in range(r):
        prev = '.'
        for j in range(c):
            s = m[i][j]
            if s != '.':
                above = aboves[j]
                prev_isg = isinstance(prev, Header)
                prev_ism = isinstance(prev, Mirror)
                above_isg = isinstance(above, Header)                
                above_ism = isinstance(above, Mirror)
               
                if s in mirror_faces: # ('\\', '/', '#')
                    
                    s = Mirror(i,j,s)
                    ## if above, prev is not mirror, not goargoyle, it is '.', can be skipped
                    ## mirror up, dn, ft, bk
                    if above_ism:
                        above.dn = s
                        s.up = above
                    elif above_isg:
                        s.up = above
                        mds.append((s, top))
                        
                    if prev_ism:
                        prev.bk = s
                        s.ft = prev
                    elif prev_isg:
                        s.ft = prev
                        mds.append((s, lt))

                    prev = s
                    aboves[j] = s
                   

                else: ## s == 'V' or s == 'H':
                    
                    # when prev_isg or above_isg is True, s is Gargoyle
                    if prev_isg: #prev_isg True
                        if above_isg: #prev_isg True, above_isg True
                            above.groups[s] += 1  # without mirror, always homogenious
                            above.reconcile(prev, False) #merge group
                            s = above
                        else: # prev_isg True, above_isg False
                            prev.groups[s] += 1
                            s = prev                              
                    elif above_isg: # prev_isg False, above_isg True
                        above.groups[s] += 1                        
                        s = above

                    # when prev_isg is False, above_isg is False, s is Header
                    else: # prev_isg False, above_isg False
                        s = Header(i,j,s)
                        gms.append(s)
                        
                    if above_ism:
                        above.dn = s
                        mds.append((above, btm))
                        
                    if prev_ism:                        
                        prev.bk = s
                        mds.append((prev, rt))
                
                    prev = s
                    aboves[j] = s

        if isinstance(prev, Mirror): prev.bk = '.'

    for j in range(c):
        above = aboves[j]
        if isinstance(above, Mirror): above.dn = '.'
     

    return mds, gms


def assess(mds, gms):

    total = 0
    die = False

    ## must be head, and need to locate its master before action
##    print(f'mds = {mds}')
##    print(f'gms = {gms}')
    ## mds: mirrors who connected to at least one Gargoyle
    ## gms: Headers who used to be a master, now may not
    
    while mds:
        (mr, d) = mds.pop()
        if d in mr.visited: continue
        
        g = mr.outward(d) ## it must be a Gargoyle's header per initialization     
        h, nxt_d = mr.reflecting(d)  ## check what is at the other side           
        prev_mr = mr
        while nxt_d and isinstance(h, Mirror): ## could be '#', nxt_d = False
            prev_mr = h
            nxt_d = h.get_opp(nxt_d)
            h, nxt_d = h.reflecting(nxt_d)

        if isinstance(h, Header):
##          mds.remove((prev_mr, nxt_d))   ## slow operation to search the list
            prev_mr.mark_visit(nxt_d)      ## use a memory to mark visited
            flip = False if nxt_d in (d, mr.get_opp(d)) else True ## flip case
            die = g.reconcile(h, flip)
        elif h == '#':
            die = g.add_blocked_face(d)
            
        if die:
            return -1
    while gms:
        g = gms.pop()
        if g.type == 'master':
            if g.blocked_face:
                total += g.groups[g.blocked_face]
            else:
                total += min(g.groups.values())
                    
    return total
    
def main():
    
    global top, btm, lt, rt
    
    top = 'top'
    btm = 'bottom'
    lt = 'left'
    rt = 'right'
    
    r, c = map(int, input().split())

    m = [ [] for i in range(r)]

    for i in range(r):
        m[i] = list(input())
        
    start = time()
  
    mirrors, masters = initialize(m, r, c)
   
    after_init = time()

    total = assess(mirrors, masters)

    end = time()

    print(f'time spend in initialize {after_init - start:.6f}, in assess {end - after_init:.6f}, overall {end - start:.6f}')
    return total

if __name__ == '__main__':

    print(main())


