# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from testapp.models import ModelA, ModelB, ModelC, ModelD, ModelE


def create_test_data():
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

        # model_a.model_b = model_b
        # model_a.save()
        # model_a.tags.add('one')

        # if i % 2:
        #     model_a.tags.add('two')
        # elif i % 3:
        #     model_a.tags.add('three')


class Command(BaseCommand):
    help = 'Create test data.'

    def handle(self, *args, **options):
        create_test_data()
