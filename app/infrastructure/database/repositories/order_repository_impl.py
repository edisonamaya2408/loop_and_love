from decimal import Decimal

from sqlalchemy.orm import Session, selectinload

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