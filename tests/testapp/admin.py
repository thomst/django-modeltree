# -*- coding: utf-8 -*-

from django.contrib import admin
from taggit_ui.actions import manage_tags
from taggit_ui.filters import TagFilter
from .models import ModelA
from .models import ModelB
from .models import ModelC
from .models import ModelD


@admin.register(ModelA)
class ModelAAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'model_b',
        'tag_view',
    )
    list_filter = [TagFilter]
    actions = [manage_tags]

    def tag_view(self, obj):
        return ", ".join(o.name for o in obj.tags.all()) or '-'
    tag_view.short_description = 'tags'


@admin.register(ModelB)
class ModelBAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tag_view',
    )
    list_filter = [TagFilter]
    actions = [manage_tags]
    manage_tags_options = [
        'modela'
        'model_b',
        'model_c',
        'model_c__model_d',
    ]

    def tag_view(self, obj):
        return ", ".join(o.name for o in obj.tags.all()) or '-'
    tag_view.short_description = 'tags'


@admin.register(ModelC)
class ModelCAdmin(admin.ModelAdmin):
    list_display = (
        'id',
    )
    list_filter = [TagFilter]
    actions = [manage_tags]
    manage_tags_options = [
        'model_b',
        'model_c',
        'model_b__model_c',
        'model_a',
    ]

    def tag_view(self, obj):
        return ", ".join(o.name for o in obj.tags.all()) or '-'
    tag_view.short_description = 'tags'


@admin.register(ModelD)
class ModelDAdmin(admin.ModelAdmin):
    list_display = (
        'id',
    )
    list_filter = [TagFilter]
    actions = [manage_tags]
    manage_tags_options = [
        'model_c',
    ]

    def tag_view(self, obj):
        return ", ".join(o.name for o in obj.tags.all()) or '-'
    tag_view.short_description = 'tags'
