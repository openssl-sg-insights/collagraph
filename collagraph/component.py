from abc import abstractmethod
from collections import defaultdict

from observ import reactive, readonly

from collagraph import render_slot


class Component:
    """Abstract base class for components"""

    __slots__ = ["state", "props"]
    __lookup_cache__ = defaultdict(dict)

    def __init__(self, props=None):
        self.props = readonly({} if props is None else props)
        self.state = reactive({})
        self._element = None
        self._slots = {}
        self._event_handlers = defaultdict(set)
        self._lookup_cache = Component.__lookup_cache__[type(self)]

    @property
    def element(self):
        """The root DOM element of this component."""
        return self._element

    @element.setter
    def element(self, value):
        """Setter that is used by the internals of Collagraph. Please don't use this."""
        self._element = value

    def render_slot(self, name, props=None):
        return render_slot(name, props, self._slots)

    # Provide shortcut to render_slot method
    s = render_slot

    def mounted(self):
        """Called after the component has been mounted.

        A component is considered mounted after:

        * All of its child components have been mounted.
        * Its own DOM tree has been created and inserted into the parent container.
        """
        pass

    def updated(self):
        """Called after the component has updated its DOM tree.

        A parent component's updated method is called after that of its child
        components.
        """
        pass

    def before_unmount(self):
        """Called right before a component instance is to be unmounted.

        Use this method to clean up manually created side effects such as timers, DOM
        event listeners or server connections.

        Note that there are no specific guarantees about the order of when this method
        is called. A parent component's method might be called before that of its child
        components.
        """
        pass

    @abstractmethod
    def render():  # pragma: no cover
        pass

    def emit(self, event, *args, **kwargs):
        """Call event handlers for the given event. Any args and kwargs will be passed
        on to the registered handlers."""
        for handler in self._event_handlers[event].copy():
            handler(*args, **kwargs)

    def add_event_handler(self, event, handler):
        """Adds an event handler for the given event."""
        self._event_handlers[event].add(handler)

    def remove_event_handler(self, event, handler):
        """Removes an event handler for the given event."""
        self._event_handlers[event].remove(handler)

    def _lookup(self, name):
        """
        Helper method that is used in the template.
        The method looks up variables that are mentioned in the template.
        This provides some syntactic sugar so that users can leave out `self`,
        `self.state` and `self.props`.
        """
        cache = self._lookup_cache
        if method := cache.get(name):
            return method(self, name)

        def props_lookup(self, name):
            return self.props[name]

        def state_lookup(self, name):
            return self.state[name]

        def self_lookup(self, name):
            return getattr(self, name)

        def global_lookup(self, name):
            return globals()[name]

        if name in self.props:
            cache[name] = props_lookup
        elif name in self.state:
            cache[name] = state_lookup
        elif hasattr(self, name):
            cache[name] = self_lookup
        elif name in globals():
            cache[name] = global_lookup
        else:
            raise NameError(f"name '{name}' is not defined")
        return self._lookup(name)