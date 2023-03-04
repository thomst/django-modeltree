import doctest
from io import StringIO
from contextlib import redirect_stdout
from django.test import TestCase
from django.db import models
from anytree import findall
from anytree import RenderTree
from anytree.search import CountError
from modeltree import __version__
from modeltree import ModelTree
from testapp.models import ModelA, ModelB, ModelC, ModelD, ModelE
from testapp.models import ModelOne, ModelTwo, ModelThree, ModelFour, ModelFive
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
        self.assertEqual(node.field_path, 'model_c__modelb__model_b')
        self.assertEqual(node.model, ModelB)
        self.assertEqual(node.field.name, 'model_b')
        self.assertEqual(node.items, None)
        self.assertEqual(len(node.path), 4)

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
        self.assertRaises(CountError, root.get, filter=lambda n: n.model == ModelC)

        # find
        self.assertEqual(len(root.find(lambda n: type(n.field) == models.ManyToManyField)), 5)
        self.assertEqual(len(root.find(lambda n: n.model == ModelC)), 7)

        # render and show
        self.assertIsInstance(root.render(), RenderTree)
        self.assertIn(nodes[4].field_path, root.render().by_attr('field_path'))
        self.assertIn(nodes[4].relation_type, root.render().by_attr('relation_type'))
        self.assertIn(str(nodes[4].model), root.render().by_attr('model'))
        self.assertIn(str(nodes[4].field), root.render().by_attr('field'))
        with redirect_stdout(StringIO()) as stdout:
            root.show()
        self.assertIn(str(nodes[4]), stdout.getvalue())
        with redirect_stdout(StringIO()) as stdout:
            root.show('[{node.relation_type}]{node.field.name} -> {node.model._meta.object_name}')
        self.assertIn('[many_to_many]modele -> ModelE', stdout.getvalue())
        with redirect_stdout(StringIO()) as stdout:
            root.show(root_format='{node.model._meta.model_name}')
        self.assertRegex(stdout.getvalue(), r'^modela')

    def test_10_docstrings(self):
        globs = dict(
            models=models,
            ModelOne=ModelOne,
            ModelTwo=ModelTwo,
            ModelThree=ModelThree,
            ModelFour=ModelFour,
            ModelFive=ModelFive,
            ModelTree=ModelTree,
            tree=ModelTree(ModelOne),
            )
        modeltree_file = '../../../modeltree/modeltree.py'
        doctest.testfile(modeltree_file, globs=globs, raise_on_error=True)
