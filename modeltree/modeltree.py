
from anytree import AnyNode
from anytree import RenderTree
from anytree import LevelOrderIter
from anytree import LevelOrderGroupIter
from anytree import PreOrderIter
from anytree import find
from anytree import findall


class ModelTree(AnyNode):
    """
    A node based tree describing a model and its recursive relations. Guess you
    have these models::

        class ModelOne(models.Model):
            model_two = models.ManyToManyField(
                'ModelTwo',
                related_name='model_one',
                blank=True)

        class ModelTwo(models.Model):
            model_three = models.ForeignKey(
                'ModelThree',
                related_name='model_two',
                blank=True, null=True,
                on_delete=models.SET_NULL)

        class ModelThree(models.Model):
            pass

        class ModelFour(models.Model):
            model_three = models.OneToOneField(
                'ModelThree',
                related_name='model_four',
                blank=True, null=True,
                on_delete=models.SET_NULL)

        class ModelFive(models.Model):
            model_two = models.ManyToManyField(
                'ModelThree',
                related_name='model_five',
                blank=True)

    then a tree representing these models will look like::

        >>> tree = ModelTree(ModelOne)
        >>> tree.show()
        ModelOne
        └── [many_to_many] ModelOne.model_two => ModelTwo
            └── [many_to_one] ModelTwo.model_three => ModelThree
                ├── [one_to_one] ModelThree.model_four => ModelFour
                └── [many_to_many] ModelThree.model_five => ModelFive

    or rendered with the :attr:`.field_path` reference::

        >>> tree = ModelTree(ModelOne)
        >>> tree.show('field_path')
        root
        └── model_two
            └── model_two__model_three
                ├── model_two__model_three__model_four
                └── model_two__model_three__model_five

    This specific model tree will be used as base for all code examples within
    this document.
    """

    MAX_DEPTH = 3
    """
    Max depth of the tree structure
    """

    RELATION_TYPES = None
    """
    A list of relations types as strings to follow when building the tree.
    By default all relations types will be followed. Types might be::

        RELATION_TYPES = [
            'one_to_one',
            'one_to_many',
            'many_to_one',
            'many_to_many',
        ]
    """

    FIELD_TYPES = None
    """
    A list of field types to follow when building the tree.
    By default all field types will be followed. Types might be::

        FIELD_TYPES = [
            models.OneToOneField,
            models.OneToOneRel,
            models.ForeignKey,
            models.ManyToOneRel,
            models.ManyToManyField,
            models.ManyToManyRel,
        ]
    """

    FIELD_PATHS = None
    """
    A list of :attr:`.field_path`s to follow when building the tree.
    Intermediated field-paths will be complemented. Guess you have this
    field-path specified::

        FIELD_PATHS = [
            'model_two__model_three__model_four',
        ]

    Then in effect the tree will be build by following these paths altogether:

    * model_two
    * model_two__model_three
    * model_two__model_three__model_four

    By default all field-paths will be followed.
    """

    def __init__(self, model, items=None, field=None, **kwargs):
        """
        To Build a tree you simply pass in the model the tree should be rooted
        to::

            tree = ModelTree(ModelOne)

        Optionally you can pass in a queryset of your model::

            items = ModelOne.objects.all()
            tree = ModelTree(ModelOne, items)

        Every node then will be equipped by the :attr:`.items` of the node's
        :attr:`.model` that are related to the items of the tree's root model.

        Parameters
        ----------
        model : obj of :class:`django.db.models.Model`
        items : obj of :class:`django.db.models.query.QuerySet` (optional)
        """
        super().__init__(**kwargs)
        self.model = model
        self.field = field
        self._items = items
        self._build_tree()

    @property
    def name(self):
        """
        A unique name as a identifier of the node. Since the :attr:`.field_path`
        is the most compact and unique value describing a node it serves best
        as the node's name attribute::

            >>> node = tree.get('model_two__model_three')
            >>> node.name == node.field_path
            True

        The name of the root node which has no field by its own is simply the
        string 'root'::

            >>> tree.root.name
            'root'
        """
        return self.field_path

    @property
    def model_name(self):
        """
        Class name of the node's :attr:`.model`.
        """
        return self.model._meta.object_name

    @property
    def field_name(self):
        """
        Name attribute of the node's :attr:`.field`.
        This is None for the root node.
        """
        return self.field.name if self.field else None

    @property
    def field_type(self):
        """
        Type of the :attr:`.field`.
        This is None for the root node.
        """
        return type(self.field) if self.field else None

    @property
    def relation_type(self):
        """
        String describing the relation type of :attr:`.field`.
        See :attr:`.RELATION_TYPES` for possible values.
        This is None for the root node.
        """
        if self.field:
            relation_types = ['one_to_one', 'one_to_many', 'many_to_one', 'many_to_many']
            return [t for t in relation_types if getattr(self.field, t)][0]
        else:
            return None

    @property
    def label(self):
        """
        String describing the field-model relation::

            >>> node_two = tree.get('model_two')
            >>> node_two.label
            'model_two -> ModelTwo'

        Since the root node has no field assigned it only shows the class name
        of its model::

            >>> tree.root.label
            'ModelOne'
        """
        if self.field:
            return '{} -> {}'.format(self.field.name, self.model_name)
        else:
            return str(self.model_name)

    @property
    def verbose_label(self):
        """
        String describing the field-model relation including the relation-type
        and the parent-model::

            >>> node_two = tree.get('model_two')
            >>> node_two.verbose_label
            '[many_to_many] ModelOne.model_two => ModelTwo'

        Since the root node has no field assigned it only shows the class name
        of its model::

            >>> tree.root.verbose_label
            'ModelOne'
        """
        if self.field:
            relation_types = ['one_to_one', 'one_to_many', 'many_to_one', 'many_to_many']
            relation_type = [t for t in relation_types if getattr(self.field, t)][0]
            return '[{}] {}.{} => {}'.format(relation_type, self.parent.model_name, self.field.name, self.model_name)
        else:
            return str(self.model_name)

    @property
    def label_path(self):
        """
        String describing the node's :attr:`.path` with :attr:`.label`s::

            >>> node_three = list(tree.iterate())[2]
            >>> node_three.label_path
            'ModelOne.model_two -> ModelTwo.model_three -> ModelThree'
        """
        return '.'.join(n.label for n in self.path)

    @property
    def model_path(self):
        """
        String describing the node's :attr:`.path` with :attr:`.model_name`s::

            >>> node_three = list(tree.iterate())[2]
            >>> node_three.model_path
            'ModelOne -> ModelTwo -> ModelThree'
        """
        return ' -> '.join(n.model_name for n in self.path)

    @property
    def field_path(self):
        """
        String describing the node's :attr:`.path` with :attr:`.field_name`s::

            >>> node_four = list(tree.iterate())[3]
            >>> node_four.field_path
            'model_two__model_three__model_four'

        Since the root-modelnode has no field by its own it is represented by
        the string 'root'::

            >>> tree.root.field_path
            'root'
        """
        if self.is_root:
            return 'root'
        else:
            return '__'.join(n.field.name for n in self.path[1:])

    @property
    def items(self):
        """
        If the ModelTree was initiated with a :class:`django.db.query.QuerySet`
        it will be the :attr:`.items` attribute of the root node. All child
        nodes hold a queryset of elements that are derived of the initial one::

            >>> items_one = ModelOne.objects.all().values_list('pk', flat=True)
            >>> items_two = ModelTwo.objects.filter(
            ...     model_one__pk__in=items_one).values_list('pk', flat=True)
            >>> items_three = ModelThree.objects.filter(
            ...     model_two__pk__in=items_two)
            >>> tree = ModelTree(ModelOne, items_one)
            >>> node_three = tree.get('model_two__model_three')
            >>> list(node_three.items) == list(items_three)
            True

        Items of a node are lazy. Querysets are evaluated not until an items
        attribute is accessed. And only for those nodes that link the current
        one with the root node. For each of those nodes the database will be hit
        once.

        If no queryset was passed for ModelTree initiation, then items of all
        nodes will be `None`.
        """
        if self._items is None and not self.root._items is None:
            query = self.field.remote_field.name + '__pk__in'
            item_ids = [i.pk for i in self.parent.items.all()]
            self._items = self.model.objects.filter(**{query: item_ids}).distinct()
        return self._items

    def render(self):
        """
        Return a :class:`anytree.RenderTree` instance for `self`.
        """
        return RenderTree(self)

    def show(self, key='verbose_label'):
        """
        Print the tree using a specific attribute. 

        Parameters
        ----------
        key: Attribute name the tree should be rendered with. (optional)
        """
        print(self.render().by_attr(key))

    def get(self, name=None, **params):
        """
        Get a node by its name or specific attributes.
        """
        if not name is None:
            params['name'] = name
        filter = lambda n: all(getattr(n, k) == v for k, v in params.items())
        return find(self, filter)

    def find(self, **params):
        """
        Find nodes by specific attributes
        """
        filter = lambda n: all(getattr(n, k) == v for k, v in params.items())
        return findall(self, filter)

    def grep(self, pattern, key='name'):
        """
        Grep nodes by a pattern that matches a specific attribute. The
        attribute's value must be of type string.
        """
        return findall(self, lambda n: pattern in getattr(n, key))

    def iterate(self, by_level=False, by_grouped_level=False, maxlevel=None, has_items=False, filter=None):
        """
        Return a tree iterator.
        """
        filters = list(filter) if filter else list()
        if has_items:
            filters.append(lambda n: bool(n.items))

        if filters:
            filter = lambda n: all(f(n) for f in filters)

        if by_level:
            iter_class = LevelOrderIter
        elif by_grouped_level:
            iter_class = LevelOrderGroupIter
        else:
            iter_class = PreOrderIter

        return iter_class(self, maxlevel=maxlevel, filter_=filter)

    def _follow_this_path(self, field):
        allowed_paths = set()
        for path in self.FIELD_PATHS:
            splitted = path.split('__')
            for i in range(len(splitted)):
                allowed_paths.add('__'.join(splitted[:i+1]))
        if self.is_root:
            this_path = field.name
        else:
            this_path = '__'.join([self.field_path, field.name]).strip('_')
        return this_path in allowed_paths

    def _follow_this_field(self, field):
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
