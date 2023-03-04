"""
.. note::

    While modeltree is functional and well tested, it's in an early state of
    its development. Backward incompatible api changes are possible. Feedback
    and suggestions about the api are very welcome. Just open an issue on
    github.


What is a ModelTree?
--------------------

A ModelTree describes a :class:`~django.db.models.Model` and all its
recursive relations to other models. It is :class:`~anytree.node.node.Node`
based, iterable, walkable, searchable and can be populated by
:attr:`~.ModelTree.items`.

Guess you have these models::

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

Then a tree representing these models will look like::

    >>> tree = ModelTree(ModelOne)
    >>> tree.show()
    ModelOne
    └── model_two -> ModelTwo
        └── model_three -> ModelThree
            ├── model_four -> ModelFour
            └── model_five -> ModelFive

Or rendered by using the :attr:`~.ModelTree.field_path` attribute::

    >>> tree = ModelTree(ModelOne)
    >>> tree.show('{node.field_path}')
    ModelOne
    └── model_two
        └── model_two__model_three
            ├── model_two__model_three__model_four
            └── model_two__model_three__model_five


How to build a ModelTree?
-------------------------

This is very easy. Simply pass in the model the tree should be rooted to::

    tree = ModelTree(ModelOne)

Optionally you can pass in a queryset of your model. Every node then will be
populated by items of the node's :attr:`~.ModelTree.model` that are related
to these initial items by the direct or indirect relation of their models::

    >>> items = ModelOne.objects.all()
    >>> tree = ModelTree(ModelOne, items)

Guess you want all ModelFive items that are related to the ModelOne items
with which you initiated your tree::

    >>> items = ModelOne.objects.all()
    >>> tree = ModelTree(ModelOne, items)
    >>> model_five_node = tree.get(filter=lambda n: n.model == ModelFive)
    >>> len(model_five_node.items)
    0

See the :attr:`~.ModelTree.items` section for more information about how items
are processed.


What if I don't want to follow all model relations?
---------------------------------------------------

You can easily adjust the way your tree is build up. Therefore overwrite one
or more of the following class attributes in your ModelTree subclass:

* :attr:`~.ModelTree.MAX_DEPTH`
* :attr:`~.ModelTree.FOLLOW_ACROSS_APPS`
* :attr:`~.ModelTree.RELATION_TYPES`
* :attr:`~.ModelTree.FIELD_TYPES`
* :attr:`~.ModelTree.FIELD_PATHS`

Guess you whish to only follow specific relation-types::

    >>> class MyModelTree(ModelTree):
    ...     RELATION_TYPES = [
    ...         'many_to_many',
    ...         'many_to_one',
    ...     ]
    ...
    >>> tree = MyModelTree(ModelOne)
    >>> tree.show()
    ModelOne
    └── model_two -> ModelTwo
        └── model_three -> ModelThree
            └── model_five -> ModelFive

For further adjustments you could also overwrite the private
:meth:`~.ModelTree._follow` method. See the description below.
"""

from django.db import models
from anytree import AnyNode
from anytree import RenderTree
from anytree import LevelOrderIter
from anytree import LevelOrderGroupIter
from anytree import PreOrderIter
from anytree import find
from anytree import findall


RELATION_TYPES = [
    'one_to_one',
    'one_to_many',
    'many_to_one',
    'many_to_many',
]
FIELD_TYPES = [
    models.OneToOneField,
    models.OneToOneRel,
    models.ForeignKey,
    models.ManyToOneRel,
    models.ManyToManyField,
    models.ManyToManyRel,
]


class ModelTree(AnyNode):
    """
    A ModelTree is technical a Subclass of :class:`~anytree.node.node.AnyNode`,
    that builds its own children nodes based on the recursives model relations.
    Means you just have to pass in a model and get a complete tree of this model
    and all its relations::

        >>> tree = ModelTree(ModelOne)
        >>> tree.show()
        ModelOne
        └── model_two -> ModelTwo
            └── model_three -> ModelThree
                ├── model_four -> ModelFour
                └── model_five -> ModelFive

    In advance you can pass in some items of your model as a queryset. The
    :attr:`.items` property of each node of your tree then reflects the itmes
    that are derived from the initial items by the direct or indirect relations
    of their models.

        >>> items = ModelOne.objects.all()
        >>> tree = ModelTree(ModelOne, items)

    Guess you want all ModelFour items that are related to the ModelOne items
    with which you initiated your tree::

        >>> items = ModelOne.objects.all()
        >>> tree = ModelTree(ModelOne, items)
        >>> model_four_node = tree.get(filter=lambda n: n.model == ModelFour)
        >>> len(model_four_node.items)
        0

    :param model: model to start with
    :type model: :class:`~django.db.models.Model`
    :param items: model items (optional)
    :type items: :class:`~django.db.models.query.QuerySet`
    """

    MAX_DEPTH = 3
    """
    Max depth of the tree structure.
    """

    FOLLOW_ACROSS_APPS = False
    """
    Follow relations across different apps.
    """

    RELATION_TYPES = RELATION_TYPES
    """
    A list of relation-types as strings to follow when building the tree.
    By default all relation-types will be followed::

        RELATION_TYPES = [
            'one_to_one',
            'one_to_many',
            'many_to_one',
            'many_to_many',
        ]
    """

    FIELD_TYPES = FIELD_TYPES
    """
    A list of field-types to follow when building the tree.
    By default all field-types and their reverse field-types are followed::

        FIELD_TYPES = [
            models.OneToOneField,
            models.OneToOneRel,
            models.ForeignKey,
            models.ManyToOneRel,
            models.ManyToManyField,
            models.ManyToManyRel,
        ]

    .. note::
    
        Generic relations using the contenttypes framework are not supported.
    """

    FIELD_PATHS = None
    """
    A list of :attr:`.field_path`\s to follow when building the tree.
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
        super().__init__(**kwargs)
        self._model = model
        self._field = field
        self._items = items
        self._build_tree()

    def __str__(self):
        if self._field:
            return '{} -> {}'.format(self._field.name, self._model._meta.object_name)
        else:
            return '{}'.format(self._model._meta.object_name)

    def __repr__(self):
        classname = type(self).__name__
        return '{}(model={}, field={})'.format(classname, repr(self._model), repr(self._field))

    @property
    def model(self):
        """
        :class:`django.db.models.Model` of the node.
        """
        return self._model

    @property
    def field(self):
        """
        The relation field of the parent node's model leading to this node.
        This is None for the root node.
        """
        return self._field

    @property
    def relation_type(self):
        """
        String describing the relation type of :attr:`.field`.
        See :attr:`.RELATION_TYPES` for possible values.
        This is an empty string for the root node.
        """
        if self.field:
            return [t for t in RELATION_TYPES if getattr(self.field, t)][0]
        else:
            return str()

    @property
    def field_path(self):
        """
        String describing the node's :attr:`~anytree.node.nodemixin.NodeMixin.path`
        using the :attr:`.field_name` of nodes::

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
        If the ModelTree was initiated with a :class:`~django.db.models.query.QuerySet`
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
        one with the root node. For each intermediated node the database will
        be hit once.

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
        Return a :class:`~anytree.render.RenderTree` instance for `self`.

        :return: instance of :class:`~anytree.render.RenderTree`
        """
        return RenderTree(self)

    def show(self, format='{node}', root_format='{node}'):
        """
        Print a tree. Each node will be rendered by using a format string which
        reference the node object by the key *node*::

            >>> tree = ModelTree(ModelOne)
            >>> tree.show('{node.field.model._meta.object_name}.{node.field.name} -> {node.model._meta.object_name}')
            ModelOne
            └── ModelOne.model_two -> ModelTwo
                └── ModelTwo.model_three -> ModelThree
                    ├── ModelThree.model_four -> ModelFour
                    └── ModelThree.model_five -> ModelFive

        :param str format: format string to render a node object (optional)
        :param str root_format: format string to render the root node object (optional)
        """
        for prefix, _, node in self.render():
            if root_format and node.is_root:
                label = root_format.format(node=node)
            else:
                label = format.format(node=node)
            print(f'{prefix}{label}')

    def get(self, field_path=None, filter=None):
        """
        Either lookup a node by its :attr:`.field_path` or use a filter::

            >>> tree = ModelTree(ModelOne)
            >>> tree.get('model_two') == tree.get(filter=lambda n: n.model == ModelTwo)
            True

        :param str field_path: a node's :attr:`.field_path` (optional)
        :params: any key value pair referencing to a node's attribute
        :return: node object or None if no node matches the search parameters
        :rtype: :class:`~modeltree.ModelTree` or None
        :raises: :class:`~anytree.search.CountError`: if more than one node was found
        """
        if field_path:
            filter = lambda n: n.field_path == field_path
        return find(self, filter)

    def find(self, filter):
        """
        Find nodes using a filter::

            >>> tree = ModelTree(ModelOne)
            >>> len(tree.find(lambda n: n.relation_type == 'many_to_many'))
            2
            >>> len(tree.find(lambda n: type(n.field) == models.OneToOneRel))
            1

        :params: any key value pair referencing to attributes of nodes
        :return: tuple of nodes
        """
        return findall(self, filter)

    def iterate(self, by_level=False, by_grouped_level=False, maxlevel=None, has_items=False, filter=None):
        """
        Return a tree iterator using the iteration classes of anytree:

        * :class:`~anytree.iterators.preorderiter.PreOrderIter`
        * :class:`~anytree.iterators.levelorderiter.LevelOrderIter`
        * :class:`~anytree.iterators.levelordergroupiter.LevelOrderGroupIter`

        By default an instance of the ProOrderIter class will be returned.

        :param bool by_level: use the LevelOrderIter class
        :param bool by_grouped_level: use the LevelOrderGroupIter class
        :param int maxlevel: maximum iteration level
        :param bool has_items: iterate only over nodes with more than 0 items
        :param callable filter: a callable recieving the node and returning a boolean.
        :return: iterator
        """
        filters = [filter] if filter else list()
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

    def _follow(self, field):
        """
        To fine-tune the way a tree is build overwrite this method. You can do
        what ever you want evaluating a field. Guess you only want to build your
        tree for specific django-apps::

            >>> class MyModelTree(ModelTree):
            ...    FOLLOW_ACROSS_APPS = True
            ...    def _follow(self, field):
            ...       if field.related_model._meta.app_label in ['testapp']:
            ...          return True
            ...       else:
            ...          return False
            ... 
            >>> tree = MyModelTree(ModelOne)
            >>> all(n.model._meta.app_label == 'testapp' for n in tree.iterate())
            True

        :param field: the field of :attr:`.model` to follow building the tree
        :type field: a model's relation field
        :return boolean: True to follow, False to not follow
        """
        return True

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
        # Only follow relational fields.
        if not field.is_relation:
            return False

        # Do not follow a field back to its remote field.
        elif field.remote_field is self.field:
            return False

        # Do not follow generic relations.
        elif (not field.related_model or
              field.related_model._meta.app_label == 'contenttypes'):
            return False

        # Do not follow across apps if not setup so.
        elif (not self.FOLLOW_ACROSS_APPS and
              not field.related_model._meta.app_label == self.model._meta.app_label):
            return False

        # Only follow specific relation-types.
        elif not any(getattr(field, t) for t in self.RELATION_TYPES):
            return False

        # Only follow specific field-types.
        elif not type(field) in self.FIELD_TYPES:
            return False

        # Only follow specific field-paths.
        elif self.FIELD_PATHS and not self._follow_this_path(field):
            return False

        # Allow customizing the tree building by follow method.
        elif not self._follow(field):
            return False

        else:
            return True

    def _build_tree(self):
        if self.depth < self.MAX_DEPTH:
            for field in self.model._meta.get_fields():
                if self._follow_this_field(field):
                    self.__class__(model=field.related_model, field=field, parent=self)
