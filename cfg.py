from __future__ import annotations
import ast, astor
import graphviz as gv
from typing import Dict, List, Tuple, Set, Optional, Type
from astpretty import pprint
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
        self.stmts: List[Type[ast.AST]] = []
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
        self.edges: Dict[Tuple[int, int], Type[ast.AST]] = {}
        self.graph: Optional[gv.dot.Digraph] = None

    def _traverse(self, block: BasicBlock, visited: Set[int] = set(), calls: bool = True) -> None:
        if block.bid not in visited:
            visited.add(block.bid)
            self.graph.node(str(block.bid), label=block.stmts_to_code())
            if calls and block.calls:
                self.graph.node(str(block.bid) + '_call', label=block.calls_to_code(), _attributes={'shape': 'box'})
                self.graph.edge(str(block.bid), str(block.bid) + '_call', label="calls", _attributes={'style': 'dashed'})

            for next_bid in block.next:
                self._traverse(self.blocks[next_bid], visited, calls=calls)
                self.graph.edge(str(block.bid), str(next_bid), label=astor.to_source(self.edges[(block.bid, next_bid)]) if self.edges[(block.bid, next_bid)] else '')

    def _show(self, fmt: str = 'pdf', calls: bool = True) -> gv.dot.Digraph:
        self.graph = gv.Digraph(name='cluster_'+self.name, format=fmt, graph_attr={'label': self.name})
        self._traverse(self.start, calls=calls)
        for k, v in self.func_calls.items():
            self.graph.subgraph(v._show(fmt, calls))
        return self.graph

    def show(self, filepath: str = './output', fmt: str = 'pdf', calls: bool = True, show: bool = True) -> None:
        self._show(fmt, calls)
        self.graph.render(filepath, view=show)


class CFGVisitor(ast.NodeVisitor):
    invertComparators: Dict[Type[ast.AST], Type[ast.AST]] = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE,
                                                               ast.LtE: ast.Gt,
                                                               ast.Gt: ast.LtE, ast.GtE: ast.Lt, ast.Is: ast.IsNot,
                                                               ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}

    def __init__(self):
        super().__init__()
        self.loop_stack: List[BasicBlock] = []

    def build(self, name: str, tree: Type[ast.AST]) -> CFG:
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

    def add_stmt(self, block: BasicBlock, stmt: Type[ast.AST]) -> None:
        block.stmts.append(stmt)

    def add_edge(self, frm_id: int, to_id: int, condition=None) -> BasicBlock:
        self.cfg.blocks[frm_id].next.append(to_id)
        self.cfg.blocks[to_id].prev.append(frm_id)
        self.cfg.edges[(frm_id, to_id)] = condition
        return self.cfg.blocks[to_id]

    def add_loop_block(self) -> BasicBlock:
        if self.curr_block.is_empty() and not self.curr_block.has_next():
            return self.curr_block
        else:
            loop_block = self.new_block()
            self.add_edge(self.curr_block.bid, loop_block.bid)
            return loop_block

    def add_subgraph(self, tree: Type[ast.AST]) -> None:
        self.cfg.func_calls[tree.name] = CFGVisitor().build(tree.name, ast.Module(body=tree.body))

    def add_condition(self, cond1: Optional[Type[ast.AST]], cond2: Optional[Type[ast.AST]]) -> Optional[Type[ast.AST]]:
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
                        self.add_edge(prev_bid, next_bid, self.add_condition(self.cfg.edges.get((prev_bid, block.bid)), self.cfg.edges.get((block.bid, next_bid))))
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
    def invert(self, node: Type[ast.AST]) -> Type[ast.AST]:
        # bug
        if type(node) == ast.Compare:
            return ast.Compare(left=node.left, ops=[self.invertComparators[type(node.ops[0])]()], comparators=node.comparators)
        # ?
        elif isinstance(node, ast.BinOp) and type(node.op) in inverse:
            return ast.BinOp(node.left, self.invertComparators[type(node.op)](), node.right)

        elif type(node) == ast.NameConstant and type(node.value) == bool:
            return ast.NameConstant(value=not node.value)
        elif type(node) == ast.BoolOp:
            return ast.BoolOp(values = [self.invert(x) for x in node.values], op = {ast.And: ast.Or(), ast.Or: ast.And()}.get(type(node.op)))
        elif type(node) == ast.UnaryOp:
            return self.UnaryopInvert(node)
        else:
            return ast.UnaryOp(op=ast.Not(), operand=node)

    def UnaryopInvert(self, node: Type[ast.AST]) -> Type[ast.AST]:
        if type(node.op) == ast.UAdd:
            return ast.UnaryOp(op=ast.USub(),operand = node.operand)
        elif type(node.op) == ast.USub:
            return ast.UnaryOp(op=ast.UAdd(),operand = node.operand)
        elif type(node.op) == ast.Invert:
            return ast.UnaryOp(op=ast.Not(), operand=node)
        else:
            return node.operand

    # def boolinvert(self, node:Type[ast.AST]) -> Type[ast.AST]:
    #     value = []
    #     for item in node.values:
    #         value.append(self.invert(item))
    #     if type(node.op) == ast.Or:
    #         return ast.BoolOp(values = value, op = ast.And())
    #     elif type(node.op) == ast.And:
    #         return ast.BoolOp(values = value, op = ast.Or())

    def generic_visit(self, node):
        if type(node) in [ast.Import, ast.ImportFrom]:
            self.add_stmt(self.curr_block, node)
            return
        if type(node) in [ast.FunctionDef, ast.AsyncFunctionDef]:
            self.add_stmt(self.curr_block, node)
            self.add_subgraph(node)
            return
        if type(node) in [ast.AnnAssign, ast.AugAssign, ast.Expr]:
            self.add_stmt(self.curr_block, node)
        super().generic_visit(node)

    def get_function_name(self, node: Type[ast.AST]) -> str:
        if type(node) == ast.Name:
            return node.id
        elif type(node) == ast.Attribute:
            return self.get_function_name(node.value) + '.' + node.attr
        elif type(node) == ast.Str:
            return node.s
        elif type(node) == ast.Subscript:
            return node.value.id

    def populate_body(self, body_list: List[Type[ast.AST]], to_bid: int) -> None:
        for child in body_list:
            self.visit(child)
        if not self.curr_block.next:
            self.add_edge(self.curr_block.bid, to_bid)

    def visit_Call(self, node):
        self.curr_block.calls.append(self.get_function_name(node.func))

    # assert type check
    def visit_Assert(self, node):
        self.add_stmt(self.curr_block, node)
        # If the assertion fails, the current flow ends, so the fail block is a
        # final block of the CFG.
        # self.cfg.finalblocks.append(self.add_edge(self.curr_block.bid, self.new_block().bid, self.invert(node.test)))
        # If the assertion is True, continue the flow of the program.
        # success block
        self.curr_block = self.add_edge(self.curr_block.bid, self.new_block().bid, node.test)
        self.generic_visit(node)

    # if else statement
    def visit_If(self, node):
        # Add the If statement at the end of the current block.
        self.add_stmt(self.curr_block, node)

        # Create a block for the code after the if-else.
        afterif_block = self.new_block()
        # Create a new block for the body of the if.
        if_block = self.add_edge(self.curr_block.bid, self.new_block().bid, node.test)

        # New block for the body of the else if there is an else clause.
        if node.orelse:
            self.curr_block = self.add_edge(self.curr_block.bid, self.new_block().bid, self.invert(node.test))

            # Visit the children in the body of the else to populate the block.
            self.populate_body(node.orelse, afterif_block.bid)
        else:
            self.add_edge(self.curr_block.bid, afterif_block.bid, self.invert(node.test))

        # Visit children to populate the if block.
        self.curr_block = if_block

        self.populate_body(node.body, afterif_block.bid)

        # Continue building the CFG in the after-if block.
        self.curr_block = afterif_block

    # Not tested: except with no specific error type
    def visit_Try(self, node):
        loop_guard = self.add_loop_block()
        self.curr_block = loop_guard
        self.add_stmt(loop_guard, ast.Try(body=[], handlers=[], orelse=[], finalbody=[]))

        after_try_block = self.new_block()
        self.add_stmt(after_try_block, ast.Name(id='handle errors', ctx=ast.Load()))
        self.populate_body(node.body, after_try_block.bid)

        self.curr_block = after_try_block

        if node.handlers:
            for handler in node.handlers:
                before_handler_block = self.new_block()
                self.curr_block = before_handler_block
                self.add_edge(after_try_block.bid, before_handler_block.bid, handler.type)

                after_handler_block = self.new_block()
                self.add_stmt(after_handler_block, ast.Name(id='end except', ctx=ast.Load()))
                self.populate_body(handler.body, after_handler_block.bid)
                self.add_edge(after_handler_block.bid, after_try_block.bid)


        if node.orelse:
            before_else_block = self.new_block()
            self.curr_block = before_else_block
            self.add_edge(after_try_block.bid, before_else_block.bid, ast.Name(id='No Error', ctx=ast.Load()))

            after_else_block = self.new_block()
            self.add_stmt(after_else_block, ast.Name(id='end no error', ctx=ast.Load()))
            self.populate_body(node.orelse, after_else_block.bid)
            self.add_edge(after_else_block.bid, after_try_block.bid)

        finally_block = self.new_block()
        self.curr_block = finally_block

        if node.finalbody:
            self.add_edge(after_try_block.bid, finally_block.bid, ast.Name(id='Finally', ctx=ast.Load()))
            after_finally_block = self.new_block()
            self.populate_body(node.finalbody, after_finally_block.bid)
            self.curr_block = after_finally_block
        else:
            self.add_edge(after_try_block.bid, finally_block.bid)

    def visit_Raise(self, node):
        self.add_stmt(self.curr_block, node)
        self.curr_block = self.new_block()

    # while loop
    def visit_While(self, node):
        loop_guard = self.add_loop_block()
        self.curr_block = loop_guard
        self.add_stmt(loop_guard, node)

        # New block for the case where the test in the while is False.
        afterwhile_block = self.new_block()
        self.loop_stack.append(afterwhile_block)
        inverted_test = self.invert(node.test)
        # Skip shortcut loop edge if while True:
        if not (isinstance(inverted_test, ast.NameConstant) and inverted_test.value == False):
            self.add_edge(self.curr_block.bid, afterwhile_block.bid, inverted_test)

        # New block for the case where the test in the while is True.
        # Populate the while block.
        self.curr_block = self.add_edge(self.curr_block.bid, self.new_block().bid, node.test)

        self.populate_body(node.body, loop_guard.bid)

        # Continue building the CFG in the after-while block.
        self.curr_block = afterwhile_block
        self.loop_stack.pop()

    def visit_For(self, node):
        loop_guard = self.add_loop_block()
        self.curr_block = loop_guard
        self.add_stmt(self.curr_block, node)

        # New block for the body of the for-loop.
        for_block = self.add_edge(self.curr_block.bid, self.new_block().bid, node.iter)

        # Block of code after the for loop.
        afterfor_block = self.add_edge(self.curr_block.bid, self.new_block().bid)
        self.loop_stack.append(afterfor_block)
        self.curr_block = for_block

        self.populate_body(node.body, loop_guard.bid)

        # Continue building the CFG in the after-for block.
        self.curr_block = afterfor_block

    def visit_Break(self, node):
        assert len(self.loop_stack), "Found break not inside loop"
        self.add_edge(self.curr_block.bid, self.loop_stack[-1].bid)

    def visit_Assign(self, node):
        # TODO dict and set comprehension
        if type(node.value) in [ast.ListComp] and len(node.targets) == 1 and type(node.targets[0]) == ast.Name:
            if type(node.value) == ast.ListComp:
                self.add_stmt(self.curr_block, ast.Assign(targets=[ast.Name(id=node.targets[0].id, ctx=ast.Store())], value=ast.List(elts=[], ctx=ast.Load())))
                self.listCompReg = node
            # elif type(node.value) == ast.SetComp:
            #     self.add_stmt(self.curr_block, ast.Assign(targets=[ast.Name(id=node.targets[0].id, ctx=ast.Store())], value=ast.Set(elts=[], ctx=ast.Load())))
            # else:
            #     self.add_stmt(self.curr_block, ast.Assign(targets=[ast.Name(id=node.targets[0].id, ctx=ast.Store())], value=ast.Dict(keys=[], values=[])))
        else:
            self.add_stmt(self.curr_block, node)
        self.generic_visit(node)

    def list_comp_helper(self, generators: List[Type[ast.AST]]) -> List[Type[ast.AST]]:
        if not generators:
            return [ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Name(id=self.listCompReg.targets[0].id, ctx=ast.Load()), attr='append', ctx=ast.Load()), args=[self.listCompReg.value.elt], keywords=[]))]
        else:
            # if generators[-1].ifs:
            return [ast.For(target=generators[-1].target, iter=generators[-1].iter, body=[ast.If(test=generators[-1].ifs[0], body=self.list_comp_helper(generators[:-1]), orelse=[])] if generators[-1].ifs else self.list_comp_helper(generators[:-1]), orelse=[])]
            # else:
            #     return [ast.For(target=generators[-1].target, iter=generators[-1].iter, body=self.list_comp_helper(generators[:-1]), orelse=[])]

    def visit_ListComp(self, node):
        try:
            self.generic_visit(ast.Module(self.list_comp_helper(self.listCompReg.value.generators)))
        except:
            pass

    def visit_Pass(self, node):
        self.add_stmt(self.curr_block, node)

    def visit_Continue(self, node):
        pass

    def visit_Await(self, node):
        afterawait_block = self.new_block()
        self.add_edge(self.curr_block.bid, afterawait_block.bid)
        self.generic_visit(node)
        self.curr_block = afterawait_block

    def visit_Yield(self, node):
        self.curr_block = self.add_edge(self.curr_block.bid, self.new_block().bid)

    # ToDO: final blocks to be add
    def visit_Return(self, node):
        self.add_stmt(self.curr_block, node)
        # self.cfg.finalblocks.append(self.curr_block)
        # Continue in a new block but without any jump to it -> all code after
        # the return statement will not be included in the CFG.
        self.curr_block = self.new_block()

#     ToDo: extra visit function: lambada, try & catch, list comprihension, set comprehension, dictionary comprehesion

# ToDo: unitest
