# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from testapp.models import ModelA, ModelB, ModelC, ModelD, ModelE
from testapp.models import ModelOne, ModelTwo, ModelThree, ModelFour, ModelFive


def create_test_data():
    # create admin-user
    User.objects.all().delete()
    User.objects.create_superuser('admin', 'admin@testapp.de', 'adminpassword')

    # clear existing data
    ModelA.objects.all().delete()
    ModelB.objects.all().delete()
    ModelC.objects.all().delete()
    ModelD.objects.all().delete()
    ModelE.objects.all().delete()

    for i in range(36):
        model_a = ModelA(id=i)
        model_b = ModelB(id=i)
        model_c = ModelC(id=i)
        model_d = ModelD(id=i)
        model_e = ModelE(id=i)
        model_a.save()
        model_b.save()
        model_c.save()
        model_d.save()
        model_e.save()

        if i % 2:
            model_a.model_b = model_b

        if i % 3:
            model_a.model_c = model_c

        if not i % 4:
            model_b.model_c = model_c

        if not i % 5:
            model_e.model_d = model_d

        if not i + 1 % 3:
            model_e.model_c = model_c
        model_a.save()
        model_b.save()
        model_c.save()
        model_d.save()
        model_e.save()


    for i in range(18):
        model_a = ModelA.objects.get(pk=i)
        model_c = ModelC.objects.get(pk=i)
        model_e = ModelE.objects.get(pk=i)

        if not i % 6:
            objs = list(ModelD.objects.filter(pk__in=range(i, i+6)))
            model_a.model_d.add(*objs)

        if i in range(6):
            objs = list(ModelD.objects.filter(pk__in=[i, i+1]))
            model_c.model_d.add(*objs)

        if i in range(6, 12):
            objs = list(ModelB.objects.filter(pk__in=range(26, 30)))
            model_e.model_b.add(*objs)


    # Create test-data for ModelOne serie.
    ModelOne.objects.all().delete()
    ModelTwo.objects.all().delete()
    ModelThree.objects.all().delete()
    ModelFour.objects.all().delete()
    ModelFive.objects.all().delete()
    [ModelOne(id=i).save() for i in range(4)]
    [ModelTwo(id=i).save() for i in range(8)]
    [ModelThree(id=i).save() for i in range(8)]
    [ModelFour(id=i).save() for i in range(8)]
    [ModelFive(id=i).save() for i in range(8)]

    obj_one = ModelOne.objects.get(id=3)
    obj_one.model_two.set(ModelTwo.objects.filter(id__in=range(3)))
    obj_one = ModelOne.objects.get(id=2)
    obj_one.model_two.set(ModelTwo.objects.filter(id__in=range(3,5)))

    for obj in ModelOne.objects.all():
        obj.user = User.objects.all()[0]
        obj.save()

    obj_two = ModelTwo.objects.get(id=7)
    obj_two.model_one.set(ModelOne.objects.filter(id__in=range(4)))

    objs_two = ModelTwo.objects.filter(id__in=range(4,8))
    for index, obj in enumerate(objs_two):
        obj.model_three = ModelThree.objects.get(id=index%2)
        obj.save()

    for obj in ModelThree.objects.filter(id__in=range(2)):
        obj.model_five.set(ModelFive.objects.filter(id__in=range(3, 6)))

    for obj in ModelFour.objects.all():
        obj.model_three = ModelThree.objects.get(pk=obj.id)
        obj.save()

    # from modeltree import ModelTree
    # class MyModelTree(ModelTree):
    #     FOLLOW_ACROSS_APPS = True
    # items = ModelOne.objects.filter(id__in=range(4))
    # tree = MyModelTree(ModelOne, items)
    # tree.show('[{node.relation_type}] {node.field.name}', with_items=True)


class Command(BaseCommand):
    help = 'Create test data.'

    def handle(self, *args, **options):
        create_test_data()
