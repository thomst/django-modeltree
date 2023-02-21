
from anytree import AnyNode
from anytree import RenderTree
from anytree import LevelOrderIter
from anytree import LevelOrderGroupIter
from anytree import find
from anytree import findall


class ModelTree(AnyNode):
    """
    A node based tree describing a model and its recursive relations.
    """
    MAX_DEPTH = 3
    RELATION_TYPES = None
    FIELD_TYPES = None
    FIELD_PATHS = None

    def __init__(self, model, items=None, field=None, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.model_name = model._meta.object_name
        self.field = field
        self._items = items
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
            relation_types = ['one_to_one', 'one_to_many', 'many_to_one', 'many_to_many']
            relation_type = [t for t in relation_types if getattr(self.field, t)][0]
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

    def iterate(self, maxlevel=None, group=False, has_items=False):
        if has_items:
            filter = lambda n: bool(n.items)
        else:
            filter = None
        if group:
            return LevelOrderGroupIter(self, maxlevel=maxlevel, filter_=filter)
        else:
            return LevelOrderIter(self, maxlevel=maxlevel, filter_=filter)

    def _follow_this_path(self, field):
        allowed_paths = set()
        for path in self.FIELD_PATHS:
            splitted = path.split('__')
            for i in range(len(splitted)):
                allowed_paths.add('__'.join(splitted[:i+1]))
        this_path = '__'.join([self.field_path, field.name]).strip('_')
        return this_path in allowed_paths

    def _follow_this_field(self, field):
        # field_path is '' for root node. Therefor we use a strip.
        field_path = '__'.join([self.field_path, field.name]).strip('_')

        if not field.is_relation:
            return False
        elif field.remote_field is self.field:
            return False
        elif self.RELATION_TYPES and not any(getattr(field, t) for t in self.RELATION_TYPES):
            return False
        elif self.FIELD_TYPES and not any(isinstance(field, t) for t in self.FIELD_TYPES):
            return False
        elif self.FIELD_PATHS and not self._follow_this_path(field):
            return False
        else:
            return True

    def _build_tree(self):
        if self.depth < self.MAX_DEPTH:
            for field in self.model._meta.get_fields():
                if self._follow_this_field(field):
                    self.__class__(model=field.related_model, field=field, parent=self)
