from io import StringIO
from doctest import run_docstring_examples, testmod
from contextlib import redirect_stdout
from django.test import TestCase
from django.db import models
from anytree import findall
from anytree import RenderTree
from anytree.search import CountError
from modeltree import __version__
from modeltree import ModelTree
from testapp.models import ModelA, ModelB, ModelC, ModelD, ModelE
from testapp.models import ModelOne, ModelTwo, ModelThree, ModelFour
from testapp.management.commands.createtestdata import create_test_data


class TreeWithFieldTypes(ModelTree):
    FIELD_TYPES = [
        models.ManyToManyField,
        models.ManyToManyRel,
        models.OneToOneField,
    ]


class TreeWithRelationTypes(ModelTree):
    RELATION_TYPES = [
        'one_to_many',
        'many_to_one',
    ]


class TreeWithFieldPaths(ModelTree):
    FIELD_PATHS = [
        'model_c__modelb__model_b',
        'model_d__modelc__modela',
    ]


class TreeWithMaxDepth(ModelTree):
    MAX_DEPTH = 1


class ModelTreeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data()

    def test_01_node(self):
        root = ModelTree(ModelA)
        node = root.get('model_c__modelb__model_b')
        self.assertEqual(node.label, 'model_b -> ModelB')
        self.assertEqual(node.verbose_label, '[one_to_one] ModelB.model_b => ModelB')
        self.assertEqual(node.field_path, 'model_c__modelb__model_b')
        self.assertEqual(node.model_path, 'ModelA -> ModelC -> ModelB -> ModelB')
        self.assertEqual(node.label_path, 'ModelA.model_c -> ModelC.modelb -> ModelB.model_b -> ModelB')
        self.assertEqual(len(node.path), 4)
        self.assertEqual(node.items, None)

    def test_02_tree(self):
        root = ModelTree(ModelA)
        self.assertEqual(len(list(root.iterate(by_level=True))), 39)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 7)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 11)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 7)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 5)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 9)

    def test_03_tree_with_field_paths(self):
        root = TreeWithFieldPaths(ModelA)
        self.assertEqual(len(list(root.iterate(by_level=True))), 7)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 0)


    def test_04_tree_with_field_types(self):
        root = TreeWithFieldTypes(ModelA)
        self.assertEqual(len(list(root.iterate(by_level=True))), 9)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 3)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 2)


    def test_05_tree_with_relation_types(self):
        root = TreeWithRelationTypes(ModelA)
        self.assertEqual(len(list(root.iterate(by_level=True))), 4)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 0)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 1)


    def test_06_tree_with_max_depth(self):
        root = TreeWithMaxDepth(ModelA)
        self.assertEqual(len(list(root.iterate(by_level=True))), 4)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 0)

    def test_07_count_items(self):
        items = ModelA.objects.filter(pk__in=range(22))
        root = TreeWithFieldPaths(ModelA, items=items)
        self.assertEqual(len(list(root.iterate(by_level=True))[0].items), 22)
        self.assertEqual(len(list(root.iterate(by_level=True))[1].items), 14)
        self.assertEqual(len(list(root.iterate(by_level=True))[2].items), 18)
        self.assertEqual(len(list(root.iterate(by_level=True))[3].items), 4)
        self.assertEqual(len(list(root.iterate(by_level=True))[4].items), 6)
        self.assertEqual(len(list(root.iterate(by_level=True))[5].items), 0)
        self.assertEqual(len(list(root.iterate(by_level=True))[6].items), 4)

        items = ModelA.objects.filter(pk__in=range(12, 16))
        root = TreeWithFieldPaths(ModelA, items=items)
        self.assertEqual(len(list(root.iterate(by_level=True))[0].items), 4)
        self.assertEqual(len(list(root.iterate(by_level=True))[1].items), 2)
        self.assertEqual(len(list(root.iterate(by_level=True))[2].items), 6)
        self.assertEqual(len(list(root.iterate(by_level=True))[3].items), 0)
        self.assertEqual(len(list(root.iterate(by_level=True))[4].items), 0)
        self.assertEqual(len(list(root.iterate(by_level=True))[5].items), 0)
        self.assertEqual(len(list(root.iterate(by_level=True))[6].items), 0)

    def test_08_compare_items(self):
        # Manually create set of objects of node 'model_d__modelc__modela'
        # and compare the node items with the manually retreived objects.
        # root.show()
        items = ModelA.objects.filter(pk__in=range(22))
        root = TreeWithFieldPaths(ModelA, items=items)
        node = root.get('model_d__modelc__modela')
        objs_d = set()
        for obj_a in items:
            objs_d.update(set(obj_a.model_d.all()))
        objs_c = set()
        for obj_d in objs_d:
            objs_c.update(set(obj_d.modelc_set.all()))
        objs_a = set()
        for obj_c in objs_c:
            objs_a.update(set(obj_c.modela_set.all()))
        self.assertListEqual(list(node.items), list(objs_a))

    def test_09_helper_methods(self):
        # iterate
        root = ModelTree(ModelA)
        nodes = list(root.iterate())
        self.assertEqual(len(nodes), 39)
        nodes = list(root.iterate(by_level=True))
        self.assertEqual(len(nodes), 39)
        nodes = list(root.iterate(by_grouped_level=True))
        self.assertEqual(len(nodes), 4)
        nodes = list(root.iterate(has_items=True))
        self.assertEqual(len(nodes), 0)
        items = ModelA.objects.filter(pk__in=range(12, 16))
        root = TreeWithFieldPaths(ModelA, items=items)
        nodes = list(root.iterate(has_items=True))
        self.assertEqual(len(nodes), 3)

        # get
        root = ModelTree(ModelA)
        nodes = list(root.iterate(by_level=True))
        field_path = nodes[6].field_path
        self.assertEqual(root.get(field_path).field_path, field_path)
        self.assertIsNone(root.get('dummy__path'))
        self.assertTrue(root.get('root').is_root)
        self.assertRaises(CountError, root.get, model=ModelC)

        # find
        self.assertEqual(len(root.find(field_type=models.ManyToManyField)), 5)
        self.assertEqual(len(root.find(model=ModelC)), 7)

        # grep
        self.assertEqual(len(root.grep('model_c__modelb')), 5)
        self.assertEqual(len(root.grep('ModelB', key='label')), 11)
        for node in root.grep('ModelB', key='label'):
            self.assertTrue('ModelB' in node.label)

        # render and show
        self.assertIsInstance(root.render(), RenderTree)
        self.assertIn(nodes[4].field_path, root.render().by_attr('field_path'))
        self.assertIn(nodes[4].model_path, root.render().by_attr('model_path'))
        self.assertIn(nodes[4].field_name, root.render().by_attr('field_name'))
        self.assertIn(nodes[4].relation_type, root.render().by_attr('relation_type'))
        self.assertIn(nodes[4].label, root.render().by_attr('label'))
        with redirect_stdout(StringIO()) as stdout:
            root.show()
        self.assertIn(nodes[4].verbose_label, stdout.getvalue())

    def test_10_docstrings(self):
        globs = dict(
            models=models,
            ModelOne=ModelOne,
            ModelTwo=ModelTwo,
            ModelThree=ModelThree,
            ModelFour=ModelFour,
            ModelTree=ModelTree,
            tree=ModelTree(ModelOne),
            )
        run_docstring_examples(ModelTree, globs=globs)
        run_docstring_examples(ModelTree.__init__, globs=globs)
        run_docstring_examples(ModelTree.label, globs=globs)
        run_docstring_examples(ModelTree.verbose_label, globs=globs)
        run_docstring_examples(ModelTree.label_path, globs=globs)
        run_docstring_examples(ModelTree.model_path, globs=globs)
        run_docstring_examples(ModelTree.field_path, globs=globs)
        run_docstring_examples(ModelTree.items, globs=globs)
        run_docstring_examples(ModelTree.render, globs=globs)
        run_docstring_examples(ModelTree.find, globs=globs)
        run_docstring_examples(ModelTree.grep, globs=globs)
        run_docstring_examples(ModelTree.iterate, globs=globs)
