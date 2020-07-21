import cfg, os, ast, astpretty, unittest, tracemalloc

# class TestBlockId(unittest.TestCase):

#     def test_gen(self):
#         assert cfg.BlockId().gen() == 0
#         assert cfg.BlockId().gen() == 1
#         assert cfg.BlockId().gen() == 2
#         assert cfg.BlockId().gen() == 3


class TestBasicBlock(unittest.TestCase):

    def test_is_empty(self):
        # tracemalloc.start()

        # test 1: empty class
        example_path = os.path.abspath(os.getcwd()) + "/test_emptyclass.py"
        with open(example_path, 'r') as f:
            tree = ast.parse(f.read())

        test = cfg.CFGVisitor().build("Test", tree)
        assert type(test) == cfg.CFG
        assert test.name == "Test"

        self.assertTrue(test.start.is_empty())

        # test2: non empty class
        example_path = os.path.abspath(os.getcwd()) + "/test_non_emptyclass.py"
        with open(example_path, 'r') as f:
            tree = ast.parse(f.read())
        test = cfg.CFGVisitor().build("Test", tree)
        test.show()
        self.assertFalse(test.start.is_empty())

        # snapshot = tracemalloc.take_snapshot()
        # top_stats = snapshot.statistics('lineno')
        # print("[ Top 10 ]")
        # for stat in top_stats[:10]:
        #     print(stat)

    def test_has_next(self):

        block1 = cfg.BasicBlock(1)
        block1.prev = [0]
        block1.next = [2]

        block2 = cfg.BasicBlock(2)

        self.assertTrue(block1.has_next())
        self.assertFalse(block2.has_next())

    def test_remove_from_next(self):
        block1 = cfg.BasicBlock(2)
        block1.prev = [1]
        block1.next = [3]
        block1.remove_from_next(3)
        self.assertFalse(block1.has_next())

    # self.assertTrue(test.blocks[item].has_next())
    def test_has_previous(self):
        block1 = cfg.BasicBlock(2)
        block1.prev = [1]
        block1.next = [3]
        self.assertTrue(block1.has_previous())

    def test_remove_from_prev(self):
        block1 = cfg.BasicBlock(2)
        block1.prev = [1]
        block1.next = [3]
        block1.remove_from_prev(1)
        self.assertFalse(block1.has_previous())

    def test_stmts_to_code(self):

        example_path = os.path.abspath(os.getcwd()) + "/test_non_emptyclass.py"
        with open(example_path, 'r') as f:
            tree = ast.parse(f.read())
        test = cfg.CFGVisitor().build("Test", tree)

        for item in test.blocks:
            block1 = cfg.BasicBlock(item)
            for temp in test.blocks[item].stmts:
                # astpretty.pprint(temp)

                block1.stmts.append(temp)
            self.assertEqual(block1.stmts_to_code(), "def test_function(a):\n")

    def test_calls_to_code(self):
        block1 = cfg.BasicBlock(1)

        example_path = os.path.abspath(os.getcwd()) + "/test_functionCalls.py"
        with open(example_path, 'r') as f:
            tree = ast.parse(f.read())
        test = cfg.CFGVisitor().build("Test", tree)

        for item in test.blocks:
            for temp in test.blocks[item].stmts:
                # astpretty.pprint(temp)
                block1.calls.append(temp.body[0].body[0].value.func.id)
                block1.calls.append(temp.body[0].orelse[0].value.func.id)
        self.assertEqual(block1.calls_to_code(), "add\nsubstract")

# class TestCFGVisitor(unittest.TestCase):
#     def test_build(self):
#         self.fail()
#
#     def test_new_block(self):
#         self.fail()
#
#     def test_add_stmt(self):
#         self.fail()
#
#     def test_add_edge(self):
#         self.fail()
#
#     def test_add_loop_block(self):
#         self.fail()
#
#     def test_add_subgraph(self):
#         self.fail()
#
#     def test_add_condition(self):
#         self.fail()
#
#     def test_remove_empty_blocks(self):
#         self.fail()
#
#     def test_invert(self):
#         self.fail()
#
#     def test_unaryop_invert(self):
#         self.fail()
#
#     def test_combine_conditions(self):
#         self.fail()
#
#     def test_generic_visit(self):
#         self.fail()
#
#     def test_get_function_name(self):
#         self.fail()
#
#     def test_populate_body(self):
#         self.fail()
#
#     def test_visit_assert(self):
#         self.fail()
#
#     def test_visit_assign(self):
#         self.fail()
#
#     def test_visit_await(self):
#         self.fail()
#
#     def test_visit_break(self):
#         self.fail()
#
#     def test_visit_call(self):
#         self.fail()
#
#     def test_visit_continue(self):
#         self.fail()
#
#     def test_visit_dict_comp_rec(self):
#         self.fail()
#
#     def test_visit_dict_comp(self):
#         self.fail()
#
#     def test_visit_expr(self):
#         self.fail()
#
#     def test_visit_for(self):
#         self.fail()
#
#     def test_visit_generator_exp_rec(self):
#         self.fail()
#
#     def test_visit_generator_exp(self):
#         self.fail()
#
#     def test_visit_if(self):
#         self.fail()
#
#     def test_visit_lambda(self):
#         self.fail()
#
#     def test_visit_list_comp_rec(self):
#         self.fail()
#
#     def test_visit_list_comp(self):
#         self.fail()
#
#     def test_visit_pass(self):
#         self.fail()
#
#     def test_visit_raise(self):
#         self.fail()
#
#     def test_visit_return(self):
#         self.fail()
#
#     def test_visit_set_comp_rec(self):
#         self.fail()
#
#     def test_visit_set_comp(self):
#         self.fail()
#
#     def test_visit_try(self):
#         self.fail()
#
#     def test_visit_while(self):
#         self.fail()
#
#     def test_visit_yield(self):
#         self.fail()
#
#
if __name__ == '__main__':
    unittest.main()