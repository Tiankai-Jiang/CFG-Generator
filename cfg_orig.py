import ast, astor, sys
import graphviz as gv

def invert(node):
    """
    Invert the operation in an ast node object (get its negation).

    Args:
        node: An ast node object.

    Returns:
        An ast node object containing the inverse (negation) of the input node.
    """
    inverse = {ast.Eq: ast.NotEq,
               ast.NotEq: ast.Eq,
               ast.Lt: ast.GtE,
               ast.LtE: ast.Gt,
               ast.Gt: ast.LtE,
               ast.GtE: ast.Lt,
               ast.Is: ast.IsNot,
               ast.IsNot: ast.Is,
               ast.In: ast.NotIn,
               ast.NotIn: ast.In}


    # how to invert expression like 1 < b < 2?, it seems like the follow code only invert the first operand
    if type(node) == ast.Compare:
        op = type(node.ops[0])
        inverse_node = ast.Compare(left=node.left, ops=[inverse[op]()], comparators=node.comparators)

    # is the following three lines necessary?
    elif isinstance(node, ast.BinOp) and type(node.op) in inverse:
        op = type(node.op)
        inverse_node = ast.BinOp(node.left, inverse[op](), node.right)
        
    elif type(node) == ast.NameConstant and node.value in [True, False]:
        inverse_node = ast.NameConstant(value=not node.value)
    else:
        inverse_node = ast.UnaryOp(op=ast.Not(), operand=node)

    return inverse_node


def merge_exitcases(exit1, exit2):
    """
    Merge the exitcases of two Links.

    Args:
        exit1: The exitcase of a Link object.
        exit2: Another exitcase to merge with exit1.

    Returns:
        The merged exitcases.
    """
    if exit1:
        if exit2:
            return ast.BoolOp(ast.And(), values=[exit1, exit2])
        return exit1
    return exit2


class CFGBuilder(ast.NodeVisitor):
    """
    Control flow graph builder.

    A control flow graph builder is an ast.NodeVisitor that can walk through
    a program's AST and iteratively build the corresponding CFG.
    """

    def __init__(self):
        super().__init__()
        self.after_loop_block_stack = []

    # ---------- CFG building methods ---------- #
    def build(self, name, tree, asynchr=False, entry_id=0):
        """
        Build a CFG from an AST.

        Args:
            name: The name of the CFG being built.
            tree: The root of the AST from which the CFG must be built.
            async: Boolean indicating whether the CFG being built represents an
                   asynchronous function or not. When the CFG of a Python
                   program is being built, it is considered like a synchronous
                   'main' function.
            entry_id: Value for the id of the entry block of the CFG.

        Returns:
            The CFG produced from the AST.
        """
        self.cfg = CFG(name, asynchr=asynchr)
        # Tracking of the current block while building the CFG.
        self.current_id = entry_id
        self.current_block = self.new_block()
        self.cfg.entryblock = self.current_block
        # Actual building of the CFG is done here.
        self.visit(tree)
        self.clean_cfg(self.cfg.entryblock)
        return self.cfg

    def build_from_src(self, name, src):
        """
        Build a CFG from some Python source code.

        Args:
            name: The name of the CFG being built.
            src: A string containing the source code to build the CFG from.

        Returns:
            The CFG produced from the source code.
        """
        tree = ast.parse(src, mode='exec')
        return self.build(name, tree)

    def build_from_file(self, name, filepath):
        """
        Build a CFG from some Python source file.

        Args:
            name: The name of the CFG being built.
            filepath: The path to the file containing the Python source code
                      to build the CFG from.

        Returns:
            The CFG produced from the source file.
        """
        with open(filepath, 'r') as src_file:
            src = src_file.read()
            return self.build_from_src(name, src)

    # ---------- Graph management methods ---------- #
    def new_block(self):
        """
        Create a new block with a new id.

        Returns:
            A Block object with a new unique id.
        """
        self.current_id += 1
        return Block(self.current_id)

    def add_statement(self, block, statement):
        """
        Add a statement to a block.

        Args:
            block: A Block object to which a statement must be added.
            statement: An AST node representing the statement that must be
                       added to the current block.
        """
        block.statements.append(statement)

    def add_exit(self, block, nextblock, exitcase=None):
        """
        Add a new exit to a block.

        Args:
            block: A block to which an exit must be added.
            nextblock: The block to which control jumps from the new exit.
            exitcase: An AST node representing the 'case' (or condition)
                      leading to the exit from the block in the program.
        """
        newlink = Link(block, nextblock, exitcase)
        block.exits.append(newlink)
        nextblock.predecessors.append(newlink)

    def new_loopguard(self):
        """
        Create a new block for a loop's guard if the current block is not
        empty. Links the current block to the new loop guard.

        Returns:
            The block to be used as new loop guard.
        """
        if self.current_block.is_empty() and len(self.current_block.exits) == 0:
            # If the current block is empty and has no exits, it is used as
            # entry block (condition test) for the loop.
            loopguard = self.current_block
        else:
            # Jump to a new block for the loop's guard if the current block
            # isn't empty or has exits.
            loopguard = self.new_block()
            self.add_exit(self.current_block, loopguard)

        return loopguard

    def new_functionCFG(self, node, asynchr=False):
        """
        Create a new sub-CFG for a function definition and add it to the
        function CFGs of the CFG being built.

        Args:
            node: The AST node containing the function definition.
            async: Boolean indicating whether the function for which the CFG is
                   being built is asynchronous or not.
        """
        self.current_id += 1
        # A new sub-CFG is created for the body of the function definition and
        # added to the function CFGs of the current CFG.
        func_body = ast.Module(body=node.body)
        func_builder = CFGBuilder()
        self.cfg.functioncfgs[node.name] = func_builder.build(node.name, func_body, asynchr, self.current_id)
        self.current_id = func_builder.current_id + 1

    def clean_cfg(self, block, visited=[]):
        """
        Remove the useless (empty) blocks from a CFG.

        Args:
            block: The block from which to start traversing the CFG to clean
                   it.
            visited: A list of blocks that already have been visited by
                     clean_cfg (recursive function).
        """
        # Don't visit blocks twice.
        if block in visited:
            return
        visited.append(block)

        # Empty blocks are removed from the CFG.
        if block.is_empty():
            for pred in block.predecessors:
                for exit in block.exits:
                    self.add_exit(pred.source, exit.target, merge_exitcases(pred.exitcase, exit.exitcase))
                    # Check if the exit hasn't yet been removed from
                    # the predecessors of the target block.
                    if exit in exit.target.predecessors:
                        exit.target.predecessors.remove(exit)
                # Check if the predecessor hasn't yet been removed from
                # the exits of the source block.
                if pred in pred.source.exits:
                    pred.source.exits.remove(pred)

            block.predecessors = []
            for exit in block.exits:
                self.clean_cfg(exit.target, visited)
            block.exits = []
        else:
            for exit in block.exits:
                self.clean_cfg(exit.target, visited)

    # ---------- AST Node visitor methods ---------- #
    def visit_Expr(self, node):
        self.add_statement(self.current_block, node)
        self.generic_visit(node)

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
        self.current_block.func_calls.append(func_name)

    def visit_Assign(self, node):
        self.add_statement(self.current_block, node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        self.add_statement(self.current_block, node)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self.add_statement(self.current_block, node)
        self.generic_visit(node)

    def visit_Raise(self, node):
        # TODO
        pass

    def visit_Assert(self, node):
        self.add_statement(self.current_block, node)
        # New block for the case in which the assertion 'fails'.
        failblock = self.new_block()
        self.add_exit(self.current_block, failblock, invert(node.test))
        # If the assertion fails, the current flow ends, so the fail block is a
        # final block of the CFG.
        self.cfg.finalblocks.append(failblock)
        # If the assertion is True, continue the flow of the program.
        successblock = self.new_block()
        self.add_exit(self.current_block, successblock, node.test)
        self.current_block = successblock
        self.generic_visit(node)

    def visit_If(self, node):
        # Add the If statement at the end of the current block.
        self.add_statement(self.current_block, node)

        # Create a new block for the body of the if.
        if_block = self.new_block()
        self.add_exit(self.current_block, if_block, node.test)

        # Create a block for the code after the if-else.
        afterif_block = self.new_block()

        # New block for the body of the else if there is an else clause.
        if len(node.orelse) != 0:
            else_block = self.new_block()
            self.add_exit(self.current_block, else_block, invert(node.test))
            self.current_block = else_block
            # Visit the children in the body of the else to populate the block.
            for child in node.orelse:
                self.visit(child)
            # If encountered a break, exit will have already been added
            if not self.current_block.exits:
                self.add_exit(self.current_block, afterif_block)
        else:
            self.add_exit(self.current_block, afterif_block, invert(node.test))

        # Visit children to populate the if block.
        self.current_block = if_block
        for child in node.body:
            self.visit(child)
        if not self.current_block.exits:
            self.add_exit(self.current_block, afterif_block)

        # Continue building the CFG in the after-if block.
        self.current_block = afterif_block

    def visit_While(self, node):
        loop_guard = self.new_loopguard()
        self.current_block = loop_guard
        self.add_statement(self.current_block, node)

        # New block for the case where the test in the while is True.
        while_block = self.new_block()
        self.add_exit(self.current_block, while_block, node.test)

        # New block for the case where the test in the while is False.
        afterwhile_block = self.new_block()
        self.after_loop_block_stack.append(afterwhile_block)
        inverted_test = invert(node.test)
        # Skip shortcut loop edge if while True:
        if not (isinstance(inverted_test, ast.NameConstant) and \
                inverted_test.value == False):
            self.add_exit(self.current_block, afterwhile_block, inverted_test)

        # Populate the while block.
        self.current_block = while_block
        for child in node.body:
            self.visit(child)
        if not self.current_block.exits:
            # Did not encounter a break statement, loop back
            self.add_exit(self.current_block, loop_guard)

        # Continue building the CFG in the after-while block.
        self.current_block = afterwhile_block
        self.after_loop_block_stack.pop()

    def visit_For(self, node):
        loop_guard = self.new_loopguard()
        self.current_block = loop_guard
        self.add_statement(self.current_block, node)

        # New block for the body of the for-loop.
        for_block = self.new_block()
        self.add_exit(self.current_block, for_block, node.iter)

        # Block of code after the for loop.
        afterfor_block = self.new_block()
        self.add_exit(self.current_block, afterfor_block)
        self.after_loop_block_stack.append(afterfor_block)
        self.current_block = for_block

        # Populate the body of the for loop.
        for child in node.body:
            self.visit(child)
        if not self.current_block.exits:
            # Did not encounter a break
            self.add_exit(self.current_block, loop_guard)

        # Continue building the CFG in the after-for block.
        self.current_block = afterfor_block

    def visit_Break(self, node):
        assert len(self.after_loop_block_stack), "Found break not inside loop"
        self.add_exit(self.current_block, self.after_loop_block_stack[-1])

    def visit_Continue(self, node):
        # TODO
        pass

    def visit_Import(self, node):
        self.add_statement(self.current_block, node)

    def visit_ImportFrom(self, node):
        self.add_statement(self.current_block, node)

    def visit_FunctionDef(self, node):
        self.add_statement(self.current_block, node)
        self.new_functionCFG(node, asynchr=False)

    def visit_AsyncFunctionDef(self, node):
        self.add_statement(self.current_block, node)
        self.new_functionCFG(node, asynchr=True)

    def visit_Await(self, node):
        afterawait_block = self.new_block()
        self.add_exit(self.current_block, afterawait_block)
        self.generic_visit(node)
        self.current_block = afterawait_block

    def visit_Return(self, node):
        self.add_statement(self.current_block, node)
        self.cfg.finalblocks.append(self.current_block)
        # Continue in a new block but without any jump to it -> all code after
        # the return statement will not be included in the CFG.
        self.current_block = self.new_block()

    def visit_Yield(self, node):
        self.cfg.asynchr = True
        afteryield_block = self.new_block()
        self.add_exit(self.current_block, afteryield_block)
        self.current_block = afteryield_block

class Block:
    """
    Basic block in a control flow graph.

    Contains a list of statements executed in a program without any control
    jumps. A block of statements is exited through one of its exits. Exits are
    a list of Links that represent control flow jumps.
    """

    __slots__ = ["id", "statements", "func_calls", "predecessors", "exits"]

    def __init__(self, id):
        # Id of the block.
        self.id = id
        # Statements in the block.
        self.statements = []
        # Calls to functions inside the block (represents context switches to
        # some functions' CFGs).
        self.func_calls = []
        # Links to predecessors in a control flow graph.
        self.predecessors = []
        # Links to the next blocks in a control flow graph.
        self.exits = []

    def __str__(self):
        if self.statements:
            return "block:{}@{}".format(self.id, self.at())
        return "empty block:{}".format(self.id)

    def __repr__(self):
        txt = "{} with {} exits".format(str(self), len(self.exits))
        if self.statements:
            txt += ", body=["
            txt += ", ".join([ast.dump(node) for node in self.statements])
            txt += "]"
        return txt

    def at(self):
        """
        Get the line number of the first statement of the block in the program.
        """
        if self.statements and self.statements[0].lineno >= 0:
            return self.statements[0].lineno
        return None

    def is_empty(self):
        """
        Check if the block is empty.

        Returns:
            A boolean indicating if the block is empty (True) or not (False).
        """
        return len(self.statements) == 0

    def get_source(self):
        """
        Get a string containing the Python source code corresponding to the
        statements in the block.

        Returns:
            A string containing the source code of the statements.
        """
        src = ""
        for statement in self.statements:
            if type(statement) in [ast.If, ast.For, ast.While]:
                src += (astor.to_source(statement)).split('\n')[0] + "\n"
            elif type(statement) == ast.FunctionDef or type(statement) == ast.AsyncFunctionDef:
                src += (astor.to_source(statement)).split('\n')[0] + "...\n"
            else:
                src += astor.to_source(statement)
        return src

    def get_calls(self):
        """
        Get a string containing the calls to other functions inside the block.

        Returns:
            A string containing the names of the functions called inside the
            block.
        """
        txt = ""
        for func_name in self.func_calls:
            txt += func_name + '\n'
        return txt

class Link:
    """
    Link between blocks in a control flow graph.

    Represents a control flow jump between two blocks. Contains an exitcase in
    the form of an expression, representing the case in which the associated
    control jump is made.
    """

    __slots__ = ["source", "target", "exitcase"]

    def __init__(self, source, target, exitcase=None):
        assert type(source) == Block, "Source of a link must be a block"
        assert type(target) == Block, "Target of a link must be a block"
        # Block from which the control flow jump was made.
        self.source = source
        # Target block of the control flow jump.
        self.target = target
        # 'Case' leading to a control flow jump through this link.
        self.exitcase = exitcase

    def __str__(self):
        return "link from {} to {}".format(str(self.source), str(self.target))

    def __repr__(self):
        if self.exitcase is not None:
            return "{}, with exitcase {}".format(str(self), ast.dump(self.exitcase))
        return str(self)

    def get_exitcase(self):
        """
        Get a string containing the Python source code corresponding to the
        exitcase of the Link.

        Returns:
            A string containing the source code.
        """
        if self.exitcase:
            return astor.to_source(self.exitcase)
        return ""


class CFG:
    """
    Control flow graph (CFG).

    A control flow graph is composed of basic blocks and links between them
    representing control flow jumps. It has a unique entry block and several
    possible 'final' blocks (blocks with no exits representing the end of the
    CFG).
    """

    def __init__(self, name, asynchr=False):
        assert type(name) == str, "Name of a CFG must be a string"
        assert type(asynchr) == bool, "Async must be a boolean value"
        # Name of the function or module being represented.
        self.name = name
        # Type of function represented by the CFG (sync or async). A Python
        # program is considered as a synchronous function (main).
        self.asynchr = asynchr
        # Entry block of the CFG.
        self.entryblock = None
        # Final blocks of the CFG.
        self.finalblocks = []
        # Sub-CFGs for functions defined inside the current CFG.
        self.functioncfgs = {}

    def __str__(self):
        return "CFG for {}".format(self.name)

    def _visit_blocks(self, graph, block, visited=[], calls=True):
        # Don't visit blocks twice.
        if block.id in visited:
            return

        nodelabel = block.get_source()

        graph.node(str(block.id), label=nodelabel)
        visited.append(block.id)

        # Show the block's function calls in a node.
        if calls and block.func_calls:
            calls_node = str(block.id)+"_calls"
            calls_label = block.get_calls().strip()
            graph.node(calls_node, label=calls_label,
                       _attributes={'shape': 'box'})
            graph.edge(str(block.id), calls_node, label="calls",
                       _attributes={'style': 'dashed'})

        # Recursively visit all the blocks of the CFG.
        for exit in block.exits:
            self._visit_blocks(graph, exit.target, visited, calls=calls)
            edgelabel = exit.get_exitcase().strip()
            graph.edge(str(block.id), str(exit.target.id), label=edgelabel)

    def _build_visual(self, format='pdf', calls=True):
        graph = gv.Digraph(name='cluster'+self.name, format=format,
                           graph_attr={'label': self.name})
        self._visit_blocks(graph, self.entryblock, visited=[], calls=calls)

        # Build the subgraphs for the function definitions in the CFG and add
        # them to the graph.
        for subcfg in self.functioncfgs:
            subgraph = self.functioncfgs[subcfg]._build_visual(format=format,
                                                               calls=calls)
            graph.subgraph(subgraph)

        return graph

    def build_visual(self, filepath, format, calls=True, show=True):
        """
        Build a visualisation of the CFG with graphviz and output it in a DOT
        file.

        Args:
            filename: The name of the output file in which the visualisation
                      must be saved.
            format: The format to use for the output file (PDF, ...).
            show: A boolean indicating whether to automatically open the output
                  file after building the visualisation.
        """
        graph = self._build_visual(format, calls)
        graph.render(filepath, view=show, cleanup=True)

    def __iter__(self):
        """
        Generator that yields all the blocks in the current graph, then
        recursively yields from any sub graphs
        """
        visited = set()
        to_visit = [self.entryblock]

        while to_visit:
            block = to_visit.pop(0)
            visited.add(block)
            for exit_ in block.exits:
                if exit_.target in visited or exit_.target in to_visit:
                    continue
                to_visit.append(exit_.target)
            yield block

        for subcfg in self.functioncfgs.values():
            yield from subcfg

if __name__ == '__main__':
    filename = sys.argv[1]
    try:
        cfg = CFGBuilder().build_from_file("test", filename)
        cfg.build_visual("output_orig", format='pdf', calls=True)
    except:
        print('Error in source code')
        exit(1)