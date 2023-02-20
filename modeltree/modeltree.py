
from anytree import AnyNode
from django.db import models


ORIGINAL_RELATION_TYPES = (
    models.OneToOneField,
    models.ForeignKey,
    models.ManyToManyField,
)
REMOTE_RELATION_TYPES = (
    models.OneToOneRel,
    models.ManyToOneRel,
    models.ManyToManyRel
)
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
        self.field = field
        self._items = items
        self._options = self._get_options()
        self._build_tree()

    @property
    def label(self):
        if self.field:
            return '{} -> {}'.format(self.field.name, self.model._meta.verbose_name)
        else:
            return str(self.model._meta.verbose_name)
 
    @property
    def label_path(self):
        return '.'.join(n.label for n in self.path)

    @property
    def field_path(self):
        return '__'.join(n.field.name for n in self.path[1:])

    @property
    def items(self):
        if self.is_root and self._items:
            self._items = list(self._items.all())
        elif not self.is_root and self.parent.items and self._items is None:
            self._items = list()
            for item in self.parent.items:
                # Check if item has field attribute which is not empty.
                if hasattr(item, self.field.name) and getattr(item, self.field.name):
                    # Get items from ManyTo-fields.
                    try:
                        self._items += list(getattr(item, self.field.name).all())
                    # Get item from OneTo-fields.
                    except AttributeError:
                        self._items.append(getattr(item, self.field.name))
        return self._items

    def follow_this_field(self, field):
        """
        Overwrite this method to filter the field to follow when building the tree.
        """
        return True

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

        if not self.follow_this_field(field):
            return False

        return True

    def _build_tree(self):
        if self.depth < self.MAX_DEPTH:
            for field in self._get_relation_fields():
                if self._field_is_valid(field):
                    self.__class__(model=field.related_model, field=field, parent=self)
