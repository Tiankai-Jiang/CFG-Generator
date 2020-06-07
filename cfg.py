import _ast, ast, astor
import graphviz as gv
from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Type

class SingletonMeta(type):
    _instance: Optional[BlockId] = None

    def __call__(self) -> BlockId:
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance

class BlockId(metaclass=SingletonMeta):

    counter: int = 0

    def gen(self):
        self.counter+=1
        return self.counter

class BasicBlock:

    def __init__(self, bid):
        self.bid: int = bid
        self.stmts: List[Type[_ast.AST]] = []
        self.calls: List[str] = []
        self.prev: List[int] = []
        self.next: List[int] = []

class CFG:

    def __init__(self, name):
        self.name: str = name

        # I am sure that variable asynchr is not used
        # list finalblocks is also not used?

        self.start: Optional[BasicBlock] = None
        self.func_calls: Dict[str, CFG] = {}
        self.blocks: Dict[int, BasicBlock] = {}
        self.edges: Dict[Tuple[int, int], Type[_ast.AST]] = {}

class CFGVisitor(ast.NodeVisitor):

    def __init__(self):
        super().__init__()
        self.loop_stack: List[BasicBlock] = []

    def build(self, name: str, tree: Type[_ast.AST]) -> CFG:
        self.cfg = CFG(name)

        self.curr_block = self.new_block()
        self.cfg.start = self.curr_block

        self.visit(tree)
        # self.clean()
        return self.cfg

    def new_block(self) -> BasicBlock:
        bid: int = BlockId().gen()
        self.cfg.blocks[bid] = BasicBlock(bid)
        return self.cfg.blocks[bid]

    def add_stmt(self, block: BasicBlock, stmt: Type[_ast.AST]) -> None:
        block.stmts.append(stmt)

    def add_edge(self, frm: BasicBlock, to: BasicBlock, condition=None) -> None:
        frm.next.append(to.bid)
        to.prev.append(frm.bid)
        self.cfg.edges[(frm.bid, to.bid)] = condition

    


