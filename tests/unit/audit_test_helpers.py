from dataclasses import replace
from datetime import datetime, timezone


class InMemoryAdminAuditRepository:
    """Repositorio aislado para pruebas unitarias de auditoría."""

    def __init__(self):
        self.events = []

    def record(self, event):
        stored_event = replace(
            event,
            id=len(self.events) + 1,
            created_at=(
                event.created_at
                or datetime.now(timezone.utc)
            ),
        )

        self.events.append(stored_event)
        return stored_event

    def list_paginated(
        self,
        *,
        actor=None,
        action=None,
        entity_type=None,
        entity_id=None,
        date_from=None,
        date_to_exclusive=None,
        offset=0,
        limit=25,
    ):
        events = list(self.events)

        if actor:
            needle = actor.casefold()
            events = [
                event for event in events
                if needle in event.actor_name.casefold()
                or needle in event.actor_email.casefold()
            ]

        if action:
            events = [
                event for event in events
                if event.action == action
            ]

        if entity_type:
            events = [
                event for event in events
                if event.entity_type == entity_type
            ]

        if entity_id:
            events = [
                event for event in events
                if event.entity_id == entity_id
            ]

        if date_from is not None:
            events = [
                event for event in events
                if event.created_at is not None
                and event.created_at >= date_from
            ]

        if date_to_exclusive is not None:
            events = [
                event for event in events
                if event.created_at is not None
                and event.created_at < date_to_exclusive
            ]

        events.sort(
            key=lambda event: (
                event.created_at
                or datetime.min.replace(
                    tzinfo=timezone.utc
                ),
                event.id or 0,
            ),
            reverse=True,
        )

        total = len(events)

        return events[offset:offset + limit], total