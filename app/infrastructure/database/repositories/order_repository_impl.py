from decimal import Decimal

from sqlalchemy.orm import Session, selectinload

from sqlalchemy import or_

from app.domain.entities.order import (
    OrderEntity,
    OrderItemEntity,
)
from app.domain.repositories.order_repository import (
    OrderRepository,
)
from app.extensions import db
from app.infrastructure.database.models.order_model import (
    Order,
    OrderItem,
)


class SQLAlchemyOrderRepository(OrderRepository):
    """Implementación del repositorio de pedidos con SQLAlchemy."""

    def __init__(
        self,
        session: Session | None = None,
    ):
        self.session = session or db.session

    @staticmethod
    def _to_entity(
        model: Order,
    ) -> OrderEntity:
        items = [
            OrderItemEntity(
                id=item.id,
                product_id=item.product_id,
                product_code=item.product_code,
                product_name=item.product_name,
                unit_price=Decimal(
                    str(item.unit_price)
                ),
                quantity=item.quantity,
                line_total=Decimal(
                    str(item.line_total)
                ),
            )
            for item in model.items
        ]

        return OrderEntity(
            id=model.id,
            customer_name=model.customer_name,
            phone=model.phone,
            city=model.city,
            address=model.address,
            observations=model.observations,
            status=model.status,
            total=Decimal(
                str(model.total)
            ),
            items=items,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def create(
        self,
        order: OrderEntity,
    ) -> OrderEntity:
        model = Order(
            customer_name=order.customer_name,
            phone=order.phone,
            city=order.city,
            address=order.address,
            observations=order.observations,
            status=order.status,
            total=order.total,
        )

        model.items = [
            OrderItem(
                product_id=item.product_id,
                product_code=item.product_code,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                line_total=item.line_total,
            )
            for item in order.items
        ]

        self.session.add(model)

        try:
            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(model)

        return self._to_entity(model)

    def get_by_id(
        self,
        order_id: int,
    ) -> OrderEntity | None:
        model = (
            self.session.query(Order)
            .options(
                selectinload(
                    Order.items
                )
            )
            .filter(
                Order.id == order_id
            )
            .first()
        )

        if model is None:
            return None

        return self._to_entity(model)

    def update_status(
        self,
        order_id: int,
        status: str,
    ) -> OrderEntity | None:

        model = (
            self.session.query(Order)
            .filter(
                Order.id == order_id
            )
            .first()
        )

        if model is None:
            return None

        model.status = status

        try:
            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(model)

        return self.get_by_id(
            order_id
        )

    def get_all_paginated(
        self,
        search: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 12,
    ) -> tuple[list[OrderEntity], int]:

        query = (
            self.session.query(Order)
            .options(
                selectinload(
                    Order.items
                )
            )
        )

        if search:
            search_pattern = (
                f"%{search}%"
            )

            query = query.filter(
                or_(
                    Order.customer_name.ilike(
                        search_pattern
                    ),
                    Order.phone.ilike(
                        search_pattern
                    ),
                    Order.city.ilike(
                        search_pattern
                    ),
                    Order.address.ilike(
                        search_pattern
                    ),
                )
            )

        if status is not None:
            query = query.filter(
                Order.status == status
            )

        total = query.count()

        models = (
            query
            .order_by(
                Order.created_at.desc(),
                Order.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        orders = [
            self._to_entity(
                model
            )
            for model in models
        ]

        return orders, total