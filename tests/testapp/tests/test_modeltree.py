

from io import StringIO
from contextlib import redirect_stdout
from django.test import TestCase
from anytree import findall
from anytree import find
from modeltree import __version__
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

    def test_01_node(self):
        root = ModelTree(ModelA)
        node = find(root, lambda n: n.field_path == 'model_c__modelb__model_b')
        self.assertEqual(node.label, 'model_b -> ModelB')
        self.assertEqual(node.label_path, 'ModelA.model_c -> ModelC.modelb -> ModelB.model_b -> ModelB')
        self.assertEqual(len(node.path), 4)
        self.assertEqual(node.items, None)

    def test_02_tree(self):
        root = ModelTree(ModelA)
        # print(RenderTree(root).by_attr('field_path'))
        self.assertEqual(len(list(root.iter())), 33)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 6)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 8)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 6)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 5)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 8)

    def test_03_tree_with_options(self):
        root = ModelTreeWithOptions(ModelA)
        # print(RenderTree(root).by_attr('field_path'))
        self.assertEqual(len(list(root.iter())), 7)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 2)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 0)


    def test_04_tree_with_max_depth(self):
        root = ModelTreeWithMaxDepth(ModelA)
        self.assertEqual(len(list(root.iter())), 4)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelA)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelB)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelC)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelD)), 1)
        self.assertEqual(len(findall(root, filter_=lambda n: n.model == ModelE)), 0)

    def test_05_count_items(self):
        items = ModelA.objects.filter(pk__in=range(22))
        root = ModelTreeWithOptions(ModelA, items=items)
        self.assertEqual(len(list(root.iter())[0].items), 22)
        self.assertEqual(len(list(root.iter())[1].items), 14)
        self.assertEqual(len(list(root.iter())[2].items), 18)
        self.assertEqual(len(list(root.iter())[3].items), 4)
        self.assertEqual(len(list(root.iter())[4].items), 6)
        self.assertEqual(len(list(root.iter())[5].items), 0)
        self.assertEqual(len(list(root.iter())[6].items), 4)

        items = ModelA.objects.filter(pk__in=range(12, 16))
        root = ModelTreeWithOptions(ModelA, items=items)
        self.assertEqual(len(list(root.iter())[0].items), 4)
        self.assertEqual(len(list(root.iter())[1].items), 2)
        self.assertEqual(len(list(root.iter())[2].items), 6)
        self.assertEqual(len(list(root.iter())[3].items), 0)
        self.assertEqual(len(list(root.iter())[4].items), 0)
        self.assertEqual(len(list(root.iter())[5].items), 0)
        self.assertEqual(len(list(root.iter())[6].items), 0)

    def test_06_compare_items(self):
        # Manually create set of objects of node 'model_d__modelc__modela'
        # and compare the node items with the manually retreived objects.
        # root.show()
        items = ModelA.objects.filter(pk__in=range(22))
        root = ModelTreeWithOptions(ModelA, items=items)
        node = root.find('model_d__modelc__modela')
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

    def test_07_helper_methods(self):
        # iter
        root = ModelTree(ModelA)
        nodes = list(root.iter())
        self.assertEqual(len(nodes), 33)

        # iter with group
        nodes = list(root.iter(group=True))
        self.assertEqual(len(nodes), 4)
        nodes = list(root.iter(has_items=True))
        self.assertEqual(len(nodes), 0)

        # iter with has_items
        items = ModelA.objects.filter(pk__in=range(12, 16))
        root = ModelTreeWithOptions(ModelA, items=items)
        nodes = list(root.iter(has_items=True))
        self.assertEqual(len(nodes), 3)

        # find and findall
        root = ModelTree(ModelA)
        nodes = list(root.iter())
        field_path = nodes[6].field_path
        self.assertEqual(root.find(field_path).field_path, field_path)
        self.assertIsNone(root.find('dummy__path'))
        self.assertTrue(root.find('').is_root)
        self.assertEqual(len(root.findall('model_c__modelb')), 4)

        # render and show
        self.assertIn(nodes[4].verbose_label, root.render())
        self.assertIn(nodes[4].field_path, root.render('field_path'))
        self.assertIn(nodes[4].model_path, root.render('model_path'))
        self.assertIn(nodes[4].label, root.render('label'))
        with redirect_stdout(StringIO()) as stdout:
            root.show()
        self.assertIn(nodes[4].verbose_label, stdout.getvalue())
