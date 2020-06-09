from __future__ import annotations
import _ast, ast, astor
import graphviz as gv
from typing import Dict, List, Tuple, Set, Optional, Type

# TODO later: graph
'''
1. add a color dictionary for condition calls
2. node shape (may be added into class Block)
'''
class SingletonMeta(type):
    _instance: Optional[BlockId] = None

    def __call__(self) -> BlockId:
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance


class BlockId(metaclass=SingletonMeta):
    counter: int = 0

    def gen(self) -> int:
        self.counter += 1
        return self.counter


class BasicBlock:

    def __init__(self, bid: int):
        self.bid: int = bid
        self.stmts: List[Type[_ast.AST]] = []
        self.calls: List[str] = []
        self.prev: List[int] = []
        self.next: List[int] = []

    def is_empty(self) -> bool:
        return len(self.stmts) == 0

    def has_next(self) -> bool:
        return len(self.next) != 0

    def remove_from_prev(self, prev_bid: int) -> None:
        if prev_bid in self.prev:
            self.prev.remove(prev_bid)

    def remove_from_next(self, next_bid: int) -> None:
        if next_bid in self.next:
            self.next.remove(next_bid)

    def stmts_to_code(self) -> str:
        code = ''
        for stmt in self.stmts:
            line = astor.to_source(stmt)
            code += line.split('\n')[0] + "\n" if type(stmt) in [ast.If, ast.For, ast.While, ast.FunctionDef,
                                                                 ast.AsyncFunctionDef] else line
        return code

    def calls_to_code(self) -> str:
        return '\n'.join(self.calls)


class CFG:

    def __init__(self, name: str):
        self.name: str = name

        # I am sure that in original code variable asynchr is not used
        # And I think list finalblocks is also not used.

        self.start: Optional[BasicBlock] = None
        self.func_calls: Dict[str, CFG] = {}
        self.blocks: Dict[int, BasicBlock] = {}
        self.edges: Dict[Tuple[int, int], Type[_ast.AST]] = {}
        self.graph: Optional[gv.dot.Digraph] = None

    def _traverse(self, block: BasicBlock, visited: Set[int] = set(), calls: bool = True) -> None:
        if block.bid not in visited:
            visited.add(block.bid)
            self.graph.node(str(block.bid), label=block.stmts_to_code())
            if calls and block.calls:
                self.graph.node(str(block.bid) + '_call', label=block.calls_to_code(), _attributes={'shape': 'box'})
                self.graph.edge(str(block.bid), str(block.bid) + '_call', label="calls",
                                _attributes={'style': 'dashed'})

            for next_bid in block.next:
                self._traverse(self.blocks[next_bid], visited, calls=calls)
                self.graph.edge(str(block.bid), str(next_bid),
                                label=astor.to_source(self.edges[(block.bid, next_bid)]) if self.edges[
                                    (block.bid, next_bid)] else '')

    def _show(self, fmt: str = 'pdf', calls: bool = True) -> gv.dot.Digraph:
        self.graph = gv.Digraph(name=self.name, format=fmt, graph_attr={'label': self.name})
        self._traverse(self.start, calls=calls)
        for k, v in self.func_calls.items():
            self.graph.subgraph(v._show(fmt, calls))
        return self.graph

    def show(self, filepath: str = './output', fmt: str = 'pdf', calls: bool = True, show: bool = True) -> None:
        self._show(fmt, calls)
        self.graph.render(filepath, view=show)


class CFGVisitor(ast.NodeVisitor):
    invertComparators: Dict[Type[_ast.AST], Type[_ast.AST]] = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE,
                                                               ast.LtE: ast.Gt,
                                                               ast.Gt: ast.LtE, ast.GtE: ast.Lt, ast.Is: ast.IsNot,
                                                               ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}

    def __init__(self):
        super().__init__()
        self.loop_stack: List[BasicBlock] = []

    def build(self, name: str, tree: Type[_ast.AST]) -> CFG:
        self.cfg = CFG(name)
        self.curr_block = self.new_block()
        self.cfg.start = self.curr_block

        self.visit(tree)
        self.remove_empty_blocks(self.cfg.start)
        return self.cfg

    def new_block(self) -> BasicBlock:
        bid: int = BlockId().gen()
        self.cfg.blocks[bid] = BasicBlock(bid)
        return self.cfg.blocks[bid]

    def add_stmt(self, block: BasicBlock, stmt: Type[_ast.AST]) -> None:
        block.stmts.append(stmt)

    def add_edge(self, frm_id: int, to_id: int, condition=None) -> None:
        self.cfg.blocks[frm_id].next.append(to_id)
        self.cfg.blocks[to_id].prev.append(frm_id)
        self.cfg.edges[(frm_id, to_id)] = condition

    def add_loop_block(self) -> BasicBlock:
        if self.curr_block.is_empty() and not self.curr_block.has_next():
            return self.curr_block
        else:
            loop_block = self.new_block()
            self.add_edge(self.curr_block.bid, loop_block.bid)
            return loop_block

    def add_subgraph(self, tree: Type[_ast.AST]) -> None:
        self.cfg.func_calls[tree.name] = CFGVisitor().build(tree.name, ast.Module(body=tree.body))

    def add_condition(self, cond1: Optional[Type[_ast.AST]], cond2: Optional[Type[_ast.AST]]) -> Optional[
        Type[_ast.AST]]:
        if cond1 and cond2:
            return ast.BoolOp(ast.And(), values=[cond1, cond2])
        else:
            return cond1 if cond1 else cond2

    # not tested
    def remove_empty_blocks(self, block: BasicBlock, visited: Set[int] = set()) -> None:
        if block.bid not in visited:
            visited.add(block.bid)
            if block.is_empty():
                for prev_bid in block.prev:
                    prev_block = self.cfg.blocks[prev_bid]
                    for next_bid in block.next:
                        next_block = self.cfg.blocks[next_bid]
                        self.add_edge(prev_bid, next_bid, self.add_condition(self.cfg.edges.get((prev_bid, block.bid)),
                                                                             self.cfg.edges.get((block.bid, next_bid))))
                        self.cfg.edges.pop((block.bid, next_bid), None)
                        next_block.remove_from_prev(block.bid)
                    self.cfg.edges.pop((prev_bid, block.bid), None)
                    prev_block.remove_from_next(block.bid)
                block.prev.clear()
                for next_bid in block.next:
                    self.remove_empty_blocks(self.cfg.blocks[next_bid], visited)
                block.next.clear()

            else:
                for next_bid in block.next:
                    self.remove_empty_blocks(self.cfg.blocks[next_bid], visited)

    # TODO: error condition a < b < c return b < a || b > c
    def invert(self, node: Type[_ast.AST]) -> Type[_ast.AST]:
        # bug
        if type(node) == ast.Compare:
            return ast.Compare(left=node.left, ops=[self.invertComparators[type(node.ops[0])]()],
                               comparators=node.comparators)
        # ?
        elif isinstance(node, ast.BinOp) and type(node.op) in inverse:
            return ast.BinOp(node.left, self.invertComparators[type(node.op)](), node.right)

        elif type(node) == ast.NameConstant and type(node.value) == bool:
            return ast.NameConstant(value=not node.value)
        else:
            return ast.UnaryOp(op=ast.Not(), operand=node)

    def generic_visit(self, node):
        if type(node) in {ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr}:
            self.add_stmt(self.curr_block, node)
        super().generic_visit(node)

    def visit_Call(self, node):
        def visit_func(node):
            if type(node) == ast.Name:
                return node.id
            elif type(node) == ast.Attribute:
                # Recursion on series of calls to attributes.
                func_name = visit_func(node.value)
                func_name += "." + node.attr
                return func_name
            elif type(node) == ast.Str:
                return node.s
            elif type(node) == ast.Subscript:
                return node.value.id

        func = node.func
        func_name = visit_func(func)
        self.curr_block.calls.append(func_name)

    # try catch raise
    def visit_Raise(self, node):
        pass

    # assert type check
    def visit_Assert(self, node):
        self.add_stmt(self.curr_block, node)
        # New block for the case in which the assertion 'fails'.
        failblock = self.new_block()
        self.add_edge(self.curr_block.bid, failblock.bid, self.invert(node.test))
        # If the assertion fails, the current flow ends, so the fail block is a
        # final block of the CFG.
        # self.cfg.finalblocks.append(failblock)
        # If the assertion is True, continue the flow of the program.
        successblock = self.new_block()
        self.add_edge(self.curr_block.bid, successblock.bid, node.test)
        self.curr_block = successblock
        self.generic_visit(node)

    # if else statement
    def visit_If(self, node):
        # Add the If statement at the end of the current block.
        self.add_stmt(self.curr_block, node)

        # Create a new block for the body of the if.
        if_block = self.new_block()
        self.add_edge(self.curr_block.bid, if_block.bid, node.test)

        # Create a block for the code after the if-else.
        afterif_block = self.new_block()

        # New block for the body of the else if there is an else clause.
        if node.orelse:
            else_block = self.new_block()
            self.add_edge(self.curr_block.bid, else_block.bid, self.invert(node.test))
            self.curr_block = else_block
            # Visit the children in the body of the else to populate the block.
            for child in node.orelse:
                self.visit(child)
            # If encountered a break, exit will have already been added
            if not self.curr_block.next:
                self.add_edge(self.curr_block.bid, afterif_block.bid)
        else:
            self.add_edge(self.curr_block.bid, afterif_block.bid, self.invert(node.test))

        # Visit children to populate the if block.
        self.curr_block = if_block
        for child in node.body:
            self.visit(child)
        if not self.curr_block.next:
            self.add_edge(self.curr_block.bid, afterif_block.bid)

        # Continue building the CFG in the after-if block.
        self.curr_block = afterif_block

    # while loop
    def visit_While(self, node):
        loop_guard = self.add_loop_block()
        self.curr_block = loop_guard
        self.add_stmt(self.curr_block, node)

        # New block for the case where the test in the while is True.
        while_block = self.new_block()
        self.add_edge(self.curr_block.bid, while_block.bid, node.test)

        # New block for the case where the test in the while is False.
        afterwhile_block = self.new_block()
        self.loop_stack.append(afterwhile_block)
        inverted_test = self.invert(node.test)
        # Skip shortcut loop edge if while True:
        if not (isinstance(inverted_test, ast.NameConstant) and inverted_test.value == False):
            self.add_edge(self.curr_block.bid, afterwhile_block.bid, inverted_test)

        # Populate the while block.
        self.curr_block = while_block
        for child in node.body:
            self.visit(child)
        if not self.curr_block.next:
            # Did not encounter a break statement, loop back
            self.add_edge(self.curr_block.bid, loop_guard.bid)

        # Continue building the CFG in the after-while block.
        self.curr_block = afterwhile_block
        self.loop_stack.pop()

    # for loop
    def visit_For(self, node):
        loop_guard = self.add_loop_block()
        self.curr_block = loop_guard
        self.add_stmt(self.curr_block, node)

        # New block for the body of the for-loop.
        for_block = self.new_block()
        self.add_edge(self.curr_block.bid, for_block.bid, node.iter)

        # Block of code after the for loop.
        afterfor_block = self.new_block()
        self.add_edge(self.curr_block.bid, afterfor_block.bid)
        self.loop_stack.append(afterfor_block)
        self.curr_block = for_block

        # Populate the body of the for loop.
        for child in node.body:
            self.visit(child)
        if not self.curr_block.next:
            # Did not encounter a break
            self.add_edge(self.curr_block.bid, loop_guard.bid)

        # Continue building the CFG in the after-for block.
        self.curr_block = afterfor_block

    def visit_Break(self, node):
        assert len(self.loop_stack), "Found break not inside loop"
        self.add_edge(self.curr_block.bid, self.loop_stack[-1].bid)

    def visit_Continue(self, node):
        pass

    def visit_Import(self, node):
        self.add_stmt(self.curr_block, node)

    def visit_ImportFrom(self, node):
        self.add_stmt(self.curr_block, node)

    def visit_FunctionDef(self, node):
        self.add_stmt(self.curr_block, node)
        self.add_subgraph(node)

    def visit_AsyncFunctionDef(self, node):
        self.add_stmt(self.curr_block, node)
        self.add_subgraph(node)

    def visit_Await(self, node):
        afterawait_block = self.new_block()
        self.add_edge(self.curr_block.bid, afterawait_block.bid)
        self.generic_visit(node)
        self.curr_block = afterawait_block

    # ToDO: final blocks to be add
    def visit_Return(self, node):
        self.add_stmt(self.curr_block, node)
        # self.cfg.finalblocks.append(self.curr_block)
        # Continue in a new block but without any jump to it -> all code after
        # the return statement will not be included in the CFG.
        self.curr_block = self.new_block()

    def visit_Yield(self, node):
        afteryield_block = self.new_block()
        self.add_edge(self.curr_block.bid, afteryield_block.bid)
        self.curr_block = afteryield_block

#     ToDo: extra visit function: lambada, try & catch, list comprihension, set comprehension, dictionary comprehesion

# ToDo: unitest
