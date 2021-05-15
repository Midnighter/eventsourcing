[![Build Status](https://github.com/johnbywater/eventsourcing/actions/workflows/runtests.yaml/badge.svg?branch=9.0)](https://github.com/johnbywater/eventsourcing/tree/9.0)
[![Coverage Status](https://coveralls.io/repos/github/johnbywater/eventsourcing/badge.svg?branch=9.0)](https://coveralls.io/github/johnbywater/eventsourcing?branch=9.0)
[![Documentation Status](https://readthedocs.org/projects/eventsourcing/badge/?version=v9.0.2)](https://eventsourcing.readthedocs.io/en/v9.0.2/)
[![Latest Release](https://badge.fury.io/py/eventsourcing.svg)](https://pypi.org/project/eventsourcing/)


# Event Sourcing in Python

A library for event sourcing in Python.

*"totally amazing and a pleasure to use"*

[Read the documentation here](https://eventsourcing.readthedocs.io/).

## Installation

Use pip to install the [stable distribution](https://pypi.org/project/eventsourcing/) from
the Python Package Index.

    $ pip install eventsourcing

It is recommended to install Python packages into a Python virtual environment.

    $ python -m venv venv
    $ ./venv/bin/pip install eventsourcing

## Synopsis

The example below defines an event-sourced aggregate `World`. An event
named `Created` will be triggered when the class is called. The aggregate
has a command method `make_it_so()`. An event named `SomethingHappened`
will be triggered when the method is called.

```python
from eventsourcing.domain import Aggregate, event

class World(Aggregate):
    @event('Created')
    def __init__(self):
        self.history = []

    @event('SomethingHappened')
    def make_it_so(self, what):
        self.history.append(what)
```

The `World` class uses the aggregate base class `Aggregate` from the library's
`domain` module. The `@event` decorator is used to define aggregate
event classes by inspecting the parameters of the decorated method signature.
The events are triggered when the decorated methods are called. The decorated
method body is used to evolve the state of the aggregate.

```python
world = World()
world.make_it_so('something')
assert world.history == ['something']
```

The example below defines an event-sourced application `Worlds`
that creates instances of the aggregate class `World`. It has
a method `create_world()` that creates and saves new aggregates.
It has a `make_it_so()` method that calls `make_it_so()` on already
existing aggregates. And it has a `get_history()` method that
returns the `history` of an aggregate.

```python

from eventsourcing.application import Application

class Worlds(Application):
    def create_world(self):
        world = World()
        self.save(world)
        return world.id

    def make_it_so(self, world_id, what):
        world = self.repository.get(world_id)
        world.make_it_so(what)
        self.save(world)

    def get_history(self, world_id):
        world = self.repository.get(world_id)
        return world.history
```

The application class `Worlds` uses the library's application base
class `Application`. The `Application` class brings together a domain
model of event-sourced aggregates and persistence infrastructure that
can store and retreive aggregate events.

```python
application = Worlds()
world_id = application.create_world()
application.make_it_so(world_id, 'something')
assert application.get_history(world_id) == ['something']
```

Pending aggregate events will collected when the application's `save()`
method is called. When the application repository's `get()` method is
called, the aggregate events will be retrieved and used to reconstruct
the state of the aggregate

Please refer to the sections below for more details and explanation.

## Features

**Domain models and applications** — base classes for domain model aggregates
and applications. Suggests how to structure an event-sourced application. All
classes are fully type-hinted to guide developers in using the library.

**Flexible event store** — flexible persistence of domain events. Combines
an event mapper and an event recorder in ways that can be easily extended.
Mapper uses a transcoder that can be easily extended to support custom
model object types. Recorders supporting different databases can be easily
substituted and configured with environment variables.

**Application-level encryption and compression** — encrypts and decrypts events inside the
application. This means data will be encrypted in transit across a network ("on the wire")
and at disk level including backups ("at rest"), which is a legal requirement in some
jurisdictions when dealing with personally identifiable information (PII) for example
the EU's GDPR. Compression reduces the size of stored domain events and snapshots, usually
by around 25% to 50% of the original size. Compression reduces the size of data
in the database and decreases transit time across a network.

**Snapshotting** — reduces access-time for aggregates with many domain events.

**Versioning** - allows domain model changes to be introduced after an application
has been deployed. Both domain events and aggregate classes can be versioned.
The recorded state of an older version can be upcast to be compatible with a new
version. Stored events and snapshots are upcast from older versions
to new versions before the event or aggregate object is reconstructed.

**Optimistic concurrency control** — ensures a distributed or horizontally scaled
application doesn't become inconsistent due to concurrent method execution. Leverages
optimistic concurrency controls in adapted database management systems.

**Notifications and projections** — reliable propagation of application
events with pull-based notifications allows the application state to be
projected accurately into replicas, indexes, view models, and other applications.
Supports materialized views and CQRS.

**Event-driven systems** — reliable event processing. Event-driven systems
can be defined independently of particular persistence infrastructure and mode of
running.

**Detailed documentation** — documentation provides general overview, introduction
of concepts, explanation of usage, and detailed descriptions of library classes.

**Worked examples** — includes examples showing how to develop aggregates, applications
and systems.


## Domain model

Continuing the examples defined above, when the class `World`
is called, a `Created` event object is constructed. This initial
event is used to construct an instance of `World`. Please note,
aggregate events are defined on the aggregate class, so that they
are "namespaced" within the aggregate class.

```python
# Create a new aggregate.
world = World()
assert isinstance(world, World)
```

The initial event object is immediately appended to the aggregate's internal
list of pending events. Pending event objects can be collected using the
aggregate's `collect_events()` method. Pleae note, the `collect_events()`
method is used by the `Application.save()` method to collect aggregate
events, so they can be stored in a database.

```python
# Collect events.
events = world.collect_events()
assert len(events) == 1
assert type(events[0]).__name__ == 'Created'
assert type(events[0]).__qualname__ == 'World.Created'
```

When the command method `make_it_so()` is called on an instance of
the `World` class, a `SomethingHappened` event is triggered with the
value of the `what` argument. The event object is used to append
the value `what` to the `history` of the `World` aggregate instance.
The event is "applied" to the aggregate using the body of the decorated
method.

```python
# Execute aggregate commands.
world.make_it_so('dinosaurs')
world.make_it_so('trucks')
world.make_it_so('internet')

# Check aggregate state.
assert world.history[0] == 'dinosaurs'
assert world.history[1] == 'trucks'
assert world.history[2] == 'internet'
```

Please note, that the decorated method body will be executed each time the event
is applied to evolve the state of the aggregate, both when the event is triggered
and when reconstructing aggregates from stored events. For this reason, return
statements are ignored: the decorated method body should not return any values.
If you need to return values from your aggregate command methods, use a non-decorated
method that calls a decorated method, and return the value from that method. Any
processing of command arguments that should not be repeated when reconstructing
aggregates from stored events should also be done in a separate method before the
event is triggered. For example, if the triggered event will have a new UUID, you
will need to use a separate method, and not generate the UUID in the decorated method
body, otherwise a new UUID will be created each time the aggregate is reconstructed,
rather than being fixed in the stored state of the aggregate, which is probably not
what you want. See the library's [domain module documentation](https://eventsourcing.readthedocs.io/)
for more information.

After the event has been applied to the aggregate, the subsequent events are
immediately appended to the aggregate's internal list of pending events, and
can be collected using the `collect_events()` method. Please note, if an
exception is raised in the method body, the event will not be appended to
the pending list – this can be used to validate method arguments, but be
careful to do all the validation before adjusting the state of the aggregate
if you wish to catch the exception in an application method and continue using
the same aggregate instance (otherwise you can retrieve a fresh instance from
the repository).

```python
# Collect events.
events += world.collect_events()
assert len(events) == 4
assert type(events[0]).__qualname__ == 'World.Created'
assert type(events[1]).__qualname__ == 'World.SomethingHappened'
assert type(events[2]).__qualname__ == 'World.SomethingHappened'
assert type(events[3]).__qualname__ == 'World.SomethingHappened'
```

The event objects can be used to reconstruct the state of
the aggregate. The application repository method `repository.get()`
reconstructs aggregates from stored events in this way (see below).

```python
copy = None
for event in events:
    copy = event.mutate(copy)

assert copy.history == world.history
assert copy.id == world.id
assert copy.version == world.version
assert copy.created_on == world.created_on
assert copy.modified_on == world.modified_on
```

This example can be adjusted and extended for any event-sourced domain model.


## Application

The command method `create_world()` of the `Worlds` application (defined above)
creates and saves a new instance of the aggregate class `World`, and returns
the UUID of the new instance. The command method `make_it_so()` uses the given
`world_id` to retrieve  an instance of the `World` aggregate class from the
application repository (reconstructs the aggregate from its stored events),
then calls  the aggregate command method `make_it_so()`, and then saves the
aggregate (collects and stores new aggregate event). The application query
method `get_history()` uses the given `world_id` to retrieve an instance of
the `World` aggregate class from the application repository, and then returns
the value of the aggregate's `history` attribute.

The application repository method `repository.get()` is used to retrieve
stored aggregates, by reconstructing them from their stored events.
Historical state of an aggregate can be obtained by using the optional
`version` argument.

The application notification log `log` can be used to read all the stored events
of the application as "event notifications" in the order they were
recorded.

```python
from eventsourcing.persistence import RecordConflictError
from eventsourcing.system import NotificationLogReader


def test(app: Worlds, expect_visible_in_db: bool):

    # Check app has zero event notifications.
    assert len(app.log['1,10'].items) == 0, len(app.log['1,10'].items)

    # Create a new aggregate.
    world_id = app.create_world()

    # Execute application commands.
    app.make_it_so(world_id, 'dinosaurs')
    app.make_it_so(world_id, 'trucks')

    # Check recorded state of the aggregate.
    assert app.get_history(world_id) == [
        'dinosaurs',
        'trucks'
    ]

    # Execute another command.
    app.make_it_so(world_id, 'internet')

    # Check recorded state of the aggregate.
    assert app.get_history(world_id) == [
        'dinosaurs',
        'trucks',
        'internet'
    ]

    # Check values are (or aren't visible) in the database.
    values = [b'dinosaurs', b'trucks', b'internet']
    if expect_visible_in_db:
        expected_num_visible = len(values)
    else:
        expected_num_visible = 0

    actual_num_visible = 0
    reader = NotificationLogReader(app.log)
    for notification in reader.read(start=1):
        for what in values:
            if what in notification.state:
                actual_num_visible += 1
                break
    assert expected_num_visible == actual_num_visible

    # Get historical state (at version 3, before 'internet' happened).
    old = app.repository.get(world_id, version=3)
    assert len(old.history) == 2
    assert old.history[-1] == 'trucks' # last thing to have happened was 'trucks'

    # Check app has four event notifications.
    assert len(app.log['1,10'].items) == 4, len(app.log['1,10'].items)

    # Optimistic concurrency control (no branches).
    old.make_it_so('future')
    try:
        app.save(old)
    except RecordConflictError:
        pass
    else:
        raise Exception("Shouldn't get here")

    # Check app still has only four event notifications.
    assert len(app.log['1,10'].items) == 4

    # Read event notifications.
    reader = NotificationLogReader(app.log)
    notifications = list(reader.read(start=1))
    assert len(notifications) == 4

    # Create eight more aggregate events.
    world_id = app.create_world()
    app.make_it_so(world_id, 'plants')
    app.make_it_so(world_id, 'fish')
    app.make_it_so(world_id, 'mammals')

    world_id = app.create_world()
    app.make_it_so(world_id, 'morning')
    app.make_it_so(world_id, 'afternoon')
    app.make_it_so(world_id, 'evening')

    # Get the new event notifications from the reader.
    last_id = notifications[-1].id
    notifications = list(reader.read(start=last_id + 1))
    assert len(notifications) == 8

    # Get all the event notifications from the application log.
    notifications = list(reader.read(start=1))
    assert len(notifications) == 12
```

This example can be adjusted and extended for any event-sourced application.

## Development environment

We can run the code in default "development" environment using
the default "Plain Old Python Object" infrastructure (which keeps
stored events in memory). The example below runs with no compression or
encryption of the stored events.

```python

# Construct an application object.
app = Worlds()

# Run the test.
test(app, expect_visible_in_db=True)

```

## SQLite environment

Configure "production" environment using SQLite infrastructure
(which keeps stored events in an SQLite database). The example below
uses zlib and AES to compress and encrypt the stored events.
An in-memory SQLite database is used, but it would work the
same way if a file path were set as the `SQLITE_DBNAME`.

```python
import os

from eventsourcing.cipher import AESCipher

# Generate a cipher key (keep this safe).
cipher_key = AESCipher.create_key(num_bytes=32)

# Cipher key.
os.environ['CIPHER_KEY'] = cipher_key
# Cipher topic.
os.environ['CIPHER_TOPIC'] = 'eventsourcing.cipher:AESCipher'
# Compressor topic.
os.environ['COMPRESSOR_TOPIC'] = 'eventsourcing.compressor:ZlibCompressor'

# Use SQLite infrastructure.
os.environ['INFRASTRUCTURE_FACTORY'] = 'eventsourcing.sqlite:Factory'
os.environ['SQLITE_DBNAME'] = ':memory:'  # Or path to a file on disk.
```

Run the code in "production" SQLite environment.

```python
# Construct an application object.
app = Worlds()

# Run the test.
test(app, expect_visible_in_db=False)
```

## PostgreSQL environment

Configure "production" environment using PostgresSQL infrastructure
(which keeps stored events in a PostgreSQL database). The example
below uses zlib and AES to compress and encrypt the stored events.
It is assumed the database and database user have already been
created, and the database server is running locally.

```python
import os

from eventsourcing.cipher import AESCipher

# Generate a cipher key (keep this safe).
cipher_key = AESCipher.create_key(num_bytes=32)

# Cipher key.
os.environ['CIPHER_KEY'] = cipher_key
# Cipher topic.
os.environ['CIPHER_TOPIC'] = 'eventsourcing.cipher:AESCipher'
# Compressor topic.
os.environ['COMPRESSOR_TOPIC'] = 'eventsourcing.compressor:ZlibCompressor'

# Use Postgres infrastructure.
os.environ['INFRASTRUCTURE_FACTORY'] = 'eventsourcing.postgres:Factory'
os.environ['POSTGRES_DBNAME'] = 'eventsourcing'
os.environ['POSTGRES_HOST'] = '127.0.0.1'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_USER'] = 'eventsourcing'
os.environ['POSTGRES_PASSWORD'] = 'eventsourcing'
```

Run the code in "production" PostgreSQL environment.

```python
# Construct an application object.
app = Worlds()

# Run the test.
test(app, expect_visible_in_db=False)
```


## Project

This project is [hosted on GitHub](https://github.com/johnbywater/eventsourcing).

Please register questions, requests and [issues on GitHub](https://github.com/johnbywater/eventsourcing/issues), or
post in the project's Slack channel.

There is a [Slack channel](https://join.slack.com/t/eventsourcinginpython/shared_invite/enQtMjczNTc2MzcxNDI0LTJjMmJjYTc3ODQ3M2YwOTMwMDJlODJkMjk3ZmE1MGYyZDM4MjIxODZmYmVkZmJkODRhZDg5N2MwZjk1YzU3NmY)
for this project, which you are [welcome to join](https://join.slack.com/t/eventsourcinginpython/shared_invite/enQtMjczNTc2MzcxNDI0LTJjMmJjYTc3ODQ3M2YwOTMwMDJlODJkMjk3ZmE1MGYyZDM4MjIxODZmYmVkZmJkODRhZDg5N2MwZjk1YzU3NmY).

Please refer to the [documentation](https://eventsourcing.readthedocs.io/) for installation and usage guides.
