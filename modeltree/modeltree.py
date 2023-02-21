
from anytree import AnyNode
from anytree import RenderTree
from anytree import LevelOrderIter
from anytree import LevelOrderGroupIter
from anytree import find
from anytree import findall
from django.db import models


ORIGINAL_RELATION_TYPES = (
    models.OneToOneField,
    models.ForeignKey,
    models.ManyToManyField,
)
REMOTE_RELATION_TYPES = (
    models.OneToOneRel,
    models.ManyToOneRel,
    models.ManyToManyRel,
)
ONETO_RELATION_TYPES = (
    models.OneToOneField,
    models.ForeignKey,
    models.OneToOneRel,
)
MANYTO_RELATION_TYPES = (
    models.ManyToManyField,
    models.ManyToOneRel,
    models.ManyToManyRel
)
RELATION_STYLE = [
    'one_to_one',
    'one_to_many',
    'many_to_one',
    'many_to_many',
]
RELATION_TYPES = ORIGINAL_RELATION_TYPES + REMOTE_RELATION_TYPES


class ModelTree(AnyNode):
    """
    A node based tree describing a model and its recursive relations.
    """
    RELATION_TYPES = RELATION_TYPES
    OPTIONS = list()
    MAX_DEPTH = 3

    def __init__(self, model, items=None, field=None, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.model_name = model._meta.object_name
        self.field = field
        self._items = items
        self._options = self._get_options()
        self._build_tree()

    @property
    def label(self):
        if self.field:
            return '{} -> {}'.format(self.field.name, self.model_name)
        else:
            return str(self.model_name)

    @property
    def verbose_label(self):
        if self.field:
            relation_type = [t for t in RELATION_STYLE if getattr(self.field, t)][0]
            return '[{}] {}.{} => {}'.format(relation_type, self.parent.model_name, self.field.name, self.model_name)
        else:
            return str(self.model_name)

    @property
    def label_path(self):
        return '.'.join(n.label for n in self.path)

    @property
    def model_path(self):
        return ' -> '.join(n.model_name for n in self.path)

    @property
    def field_path(self):
        return '__'.join(n.field.name for n in self.path[1:])

    @property
    def items(self):
        if self._items is None and not self.root._items is None:
            query = self.field.remote_field.name + '__pk__in'
            item_ids = [i.pk for i in self.parent.items.all()]
            self._items = self.model.objects.filter(**{query: item_ids}).distinct()
        return self._items

    def render(self, key='verbose_label'):
        return (RenderTree(self).by_attr(key))

    def show(self, key='verbose_label'):
        print(self.render(key))

    def find(self, value, key='field_path'):
        return find(self, lambda n: getattr(n, key) == value)

    def findall(self, value, key='field_path'):
        return findall(self, lambda n: value in getattr(n, key))

    def iter(self, maxlevel=None, group=False, has_items=False):
        if has_items:
            filter = lambda n: bool(n.items)
        else:
            filter = None
        if group:
            return LevelOrderGroupIter(self, maxlevel=maxlevel, filter_=filter)
        else:
            return LevelOrderIter(self, maxlevel=maxlevel, filter_=filter)

    def _get_options(self):
        options = set()
        for option in self.OPTIONS:
            splitted = option.split('__')
            for i in range(len(splitted)):
                options.add('__'.join(splitted[:i+1]))
        return list(options)

    def _get_relation_fields(self):
        fields = self.model._meta.get_fields()
        check_type = lambda f: any(issubclass(type(f), r) for r in self.RELATION_TYPES)
        fields = [f for f in fields if check_type(f)]
        return fields

    def _field_is_valid(self, field):
        if field.remote_field is self.field:
            return False

        is_remote = lambda f: any(isinstance(f, t) for t in REMOTE_RELATION_TYPES)
        if field.related_model is self.model and is_remote(field):
            return False

        field_path = (self.field_path + '__' + field.name).strip('_')
        if self._options and not field_path in self._options:
            return False

        return True

    def _build_tree(self):
        if self.depth < self.MAX_DEPTH:
            for field in self._get_relation_fields():
                if self._field_is_valid(field):
                    self.__class__(model=field.related_model, field=field, parent=self)
