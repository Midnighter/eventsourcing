import uuid

from eventsourcing.domain.model.new_entity import EventSourcedEntity, attribute, EntityRepository, entity_mutator, \
    singledispatch, Created, AttributeChanged, Discarded
from eventsourcing.domain.model.events import publish, DomainEvent


class Example(EventSourcedEntity):
    """
    An example event sourced domain model entity.
    """

    # Todo: Move this to the Cassandra repo, and make sure it will work by default.
    # Needed to get an event history longer than 10000 in Cassandra.
    # __page_size__ = 1000

    # Make sure events that are applied to the entity have originated
    # from the entity at the version the instance it is current at.
    #  - this assumes _validate_originator() is called in mutators.
    __always_validate_originator_version__ = True

    class Created(Created):
        pass

    class AttributeChanged(AttributeChanged):
        pass

    class Discarded(Discarded):
        pass

    class Heartbeat(DomainEvent):
        pass

    def __init__(self, a, b, **kwargs):
        super(Example, self).__init__(**kwargs)
        self._a = a
        self._b = b
        self._count_heartbeats = 0

    @attribute
    def a(self):
        """The 'a' attribute."""

    @attribute
    def b(self):
        """The 'b' attribute."""

    def beat_heart(self):
        self._assert_not_discarded()
        event = self.Heartbeat(entity_id=self._id, entity_version=self._version)
        self._apply(event)
        publish(event)

    def count_heartbeats(self):
        return self._count_heartbeats

    @staticmethod
    def _mutator(event, initial):
        return example_mutator(event, initial)


@singledispatch
def example_mutator(event, initial):
    return entity_mutator(event, initial)


@example_mutator.register(Example.Heartbeat)
def heartbeat_mutator(event, self):
    self._validate_originator(event)
    assert isinstance(self, Example), self
    self._count_heartbeats += 1
    self._increment_version()
    return self


class ExampleRepository(EntityRepository):
    pass


def register_new_example(a, b):
    """
    Factory method for example entities.

    :rtype: Example
    """
    entity_id = uuid.uuid4().hex
    event = Example.Created(entity_id=entity_id, a=a, b=b)
    entity = Example.mutate(event=event)
    publish(event=event)
    return entity
