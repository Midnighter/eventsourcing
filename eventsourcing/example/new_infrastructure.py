from eventsourcing.example.new_domain_model import Example, ExampleRepository
from eventsourcing.infrastructure.new_event_sourced_repo import EventSourcedRepository


class ExampleRepo(EventSourcedRepository, ExampleRepository):
    """
    Event sourced repository for the Example domain model entity.
    """
    domain_class = Example

