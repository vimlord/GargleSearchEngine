
from sklearn.neighbors import *

import numpy as np

import uuid

import heapq

class Node:
    def __init__(self, name, val, nxt=None):
        self.name = name
        self.val = val
        self.next = nxt

class OrderedVectorList:
    def __init__(self, idx):
        self.head = None
        self.idx = idx
        self.saved_pages = {}

    def add(self, name, x):
        i = self.idx
        if self.head is None:
            self.head = Node(name, x)
        else:
            node = self.head
            prev = None
            while node is not None and node.val[i] > x[i]:
                prev, node = node, node.next

            if prev is None:
                self.head = Node(name, x, head)
            else:
                prev.next = Node(name, x, node)

    def page(self, pg_num=0, pg_size=10, nxt_token=None):
        if next_token in self.saved_pages:
            node = self.saved_pages[next_token]
        else:
            node = self.head
            for i in range(pg_num * pg_size):
                if node is None: break
                else: node = node.next

        if node is None:
            return [], None
        
        result = []
        tail = node
        for i in range(pg_size):
            result.append((tail.name, tail.val))
            tail = tail.next
            if tail is None:
                break

        if tail is None:
            nxt_token = None
        else:
            nxt_token = uuid.uuid5()
            self.saved_pages[nxt_token] = tail

        return result, nxt_token

    def update(self, name, x):
        self.remove(name)
        self.add(name, x)

    def remove(self, name):
        if self.head is None:
            return
        elif self.head.name is name:
            self.head = self.head.next
        else:
            prev, node = self.head, self.head.next
            while node != None:
                if node.name == name:
                    # Remove the entry
                    prev.next = node.next
                    break
                else:
                    # Continue
                    prev, node = node, node.next

class Searcher:
    def __call__(self, x):
        return self.search(x)

    def search(self, x, **args):
        # Searches the search space for given arguments
        raise NotImplemented

    def add(self, fnames, xs, **args):
        # Indexes a document in the searcher.
        # Returns true if the insertion was successful
        return False

    def remove(self, fnames, **args):
        # Return true if the deletion was successful
        return False

class SklearnTreeSearcher:
    def __init__(self):
        self.files = []
        self.inv_files = {}
        self.data = None
        
        self.tree = None

    def _new_tree(self, data):
        raise NotImplemented

    def _build_tree(self):
        if len(self.data) == 0:
            self.tree = None
            return
        else:
            self.tree = self._new_tree(self.data)

    def search(self, x, ct, return_distance=False):
        if not isinstance(x, list) and len(x.shape) == 1:
            x = [x]

        vs = self.tree.query(x, k=ct, return_distance=return_distance)

        if return_distance:
            d, idx = vs
            d = d[0]
        else:
            idx = vs

        # Grab the files required
        f = [self.files[i] for i in idx[0]]
        
        if return_distance:
            return f, d
        else:
            return f

    def add(self, fnames, xs):
        assert len(fnames) == len(xs)
        self.files += fnames
        for f in fnames:
            self.inv_files[f] = len(self.inv_files)

        if self.data is None:
            self.data = xs
        else:
            self.data = np.concatenate(self.data, xs, axis=0)

        # Our inefficient implementation rebuilds the tree every time
        self._build_tree()

        return True

    def remove(self, fnames):
        for f in fnames:
            if f not in self.inv_files: continue

            i = self.inv_files[f]
            
            # Swap data into its place
            if len(files) == len(inv_files) and i < len(self.files):
                self.files[i] = self.files[-1]
                self.data[i] = self.data[-1]
            
            # Free memory
            del self.files[-1]
            del self.data[-1:]
            del self.inv_files[f]
        
        # Again, my laziness compels me to rebuild the tree
        self._build_tree()
        
        return True

class SetBasedCosineSimilaritySearcher(Searcher):
    def __init__(self, n_dims=1024):
        self.data = {}
        self.files = []
        self.inv_files = {}

    def add(self, fnames, xs):
        for f, x in zip(fnames, xs):
            if f not in self.data:
                # New file
                self.inv_files[f] = len(self.inv_files)
                self.files.append(f)

            self.data[f] = x

    def search(self, x, ct, return_distance=False):
        heap = []
        
        # Search the entire database
        for f in self.data:
            v = np.dot(x, self.data[f])
            heapq.heappush(heap, (-v, f))

            # Ensure the growth doesn't get out of control
            if len(heap) > ct:
                del heap[-1]
        
        # Sort the values
        res = [heapq.heappop(heap) for _ in range(len(heap))]
        
        # Provide results
        if return_distance:
            return [(f, -v) for (v, f) in res]
        else:
            return [f for (v, f) in res]

    
    def remove(self, fnames):
        for f in fnames:
            if f not in self.data: continue
            
            # Remove file from array
            i = self.inv_files[f]
            if i < len(self.files):
                self.files[i] = self.files[-1]
                del self.files[-1]
            
            # Remove filename index
            del self.inv_files[f]

            # Remove data
            del self.data[f]
        
class KDTreeSearcher(SklearnTreeSearcher):
    def __init__(self):
        super().__init__()

    def _new_tree(self, data):
        return KDTree(data)
        
class BallTreeSearcher(SklearnTreeSearcher):
    def __init__(self, leaf_size=40):
        super().__init__()
        self.leaf_size = leaf_size

    def _new_tree(self, data):
        return BallTree(data, leaf_size=self.leaf_size)

