

from django.test import TestCase
from anytree import RenderTree
from anytree import findall
from anytree import find
from anytree import LevelOrderIter
from modeltree import ModelTree
from testapp.models import ModelA, ModelB, ModelC, ModelD, ModelE
from testapp.management.commands.createtestdata import create_test_data


class ModelTreeWithOptions(ModelTree):
    OPTIONS = [
        'model_c__modelb__model_b',
        'model_d__modelc__modela',
    ]


class ModelTreeWithMaxDepth(ModelTree):
    MAX_DEPTH = 1


class ModelTreeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data()

    def setUp(self):
        self.tree = ModelTree(ModelA)
        self.tree_with_options = ModelTreeWithOptions(ModelA)
        self.tree_with_maxdepth = ModelTreeWithMaxDepth(ModelA)

    def test_01_node(self):
        root = ModelTree(ModelA)
        # print(RenderTree(root).by_attr('field_path'))
        node = find(root, lambda n: n.field_path == 'model_c__modelb__model_b')
        self.assertEqual(node.label, 'model_b -> model b')
        self.assertEqual(node.label_path, 'model a.model_c -> model c.modelb -> model b.model_b -> model b')
        self.assertEqual(len(node.path), 4)
        self.assertEqual(node.items, None)

    def test_02_tree(self):
        root = ModelTree(ModelA)
        # print(RenderTree(root).by_attr('field_path'))
        self.assertEqual(len([n for n in LevelOrderIter(root)]), 33)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 6)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 8)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 6)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 5)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 8)

    def test_03_tree_with_options(self):
        root = ModelTreeWithOptions(ModelA)
        # print(RenderTree(root).by_attr('field_path'))
        self.assertEqual(len([n for n in LevelOrderIter(root)]), 7)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 0)


    def test_04_tree_with_max_depth(self):
        root = ModelTreeWithMaxDepth(ModelA)
        self.assertEqual(len([n for n in LevelOrderIter(root)]), 4)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 0)
