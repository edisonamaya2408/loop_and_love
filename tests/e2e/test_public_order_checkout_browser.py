import os
import json
import re
import threading
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server


PRODUCT_ID = 987654
PRODUCT_CODE = "E2E-LOOPLOVE-001"
PRODUCT_NAME = "Producto E2E Móvil"
PRODUCT_PRICE = 12900
ORDER_ID = 91001
TRACKING_TOKEN = "a" * 43
WHATSAPP_NUMBER = "573001234567"


@pytest.mark.e2e
def test_mobile_b2b_checkout_recovers_after_lost_response(app):
    app.config["WHATSAPP_NUMBER"] = WHATSAPP_NUMBER

    server = make_server(
        "127.0.0.1",
        0,
        app,
        threaded=True,
    )

    server_thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    server_thread.start()

    base_url = f"http://127.0.0.1:{server.server_port}"

    order_requests = []
    stored_orders = {}
    tracking_requests = []
    whatsapp_urls = []
    browser_errors = []

    def fulfill_json(route, payload, status=200):
        route.fulfill(
            status=status,
            content_type="application/json; charset=utf-8",
            body=json.dumps(payload, ensure_ascii=False),
        )

    def handle_categories(route):
        fulfill_json(
            route,
            {
                "success": True,
                "data": [
                    {
                        "id": 456,
                        "name": "Tejidos E2E",
                        "slug": "tejidos-e2e",
                        "is_active": True,
                        "created_at": None,
                        "updated_at": None,
                    }
                ],
            },
        )

    def handle_products(route):
        fulfill_json(
            route,
            {
                "success": True,
                "data": [
                    {
                        "id": PRODUCT_ID,
                        "code": PRODUCT_CODE,
                        "name": PRODUCT_NAME,
                        "description": (
                            "Producto de prueba para el "
                            "checkout móvil."
                        ),
                        "price": f"{PRODUCT_PRICE:.2f}",
                        "category_id": 456,
                        "category": {
                            "id": 456,
                            "name": "Tejidos E2E",
                            "slug": "tejidos-e2e",
                        },
                        "image_url": None,
                        "is_active": True,
                        "created_at": None,
                        "updated_at": None,
                    }
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 12,
                    "total": 1,
                    "pages": 1,
                    "has_next": False,
                    "has_previous": False,
                },
            },
        )

    def make_order_response(payload):
        items = payload.get("items", [])

        if len(items) != 1:
            raise AssertionError(
                "La prueba esperaba una sola línea de pedido."
            )

        requested_item = items[0]

        quantity = int(requested_item["quantity"])

        if int(requested_item["product_id"]) != PRODUCT_ID:
            raise AssertionError(
                "El producto recibido no es el esperado."
            )

        total = PRODUCT_PRICE * quantity

        return {
            "id": ORDER_ID,
            "name": payload["name"],
            "phone": payload["phone"],
            "city": payload["city"],
            "address": payload["address"],
            "observations": payload.get("observations"),
            "status": "pending",
            "items": [
                {
                    "product_id": PRODUCT_ID,
                    "code": PRODUCT_CODE,
                    "name": PRODUCT_NAME,
                    "unit_price": f"{PRODUCT_PRICE:.2f}",
                    "quantity": quantity,
                    "line_total": f"{total:.2f}",
                }
            ],
            "total": f"{total:.2f}",
            "created_at": "2026-10-18T15:00:00+00:00",
            "updated_at": "2026-10-18T15:00:00+00:00",
            "tracking_token": TRACKING_TOKEN,
        }

    def handle_create_order(route):
        request = route.request
        payload = json.loads(request.post_data or "{}")

        key = request.headers.get("idempotency-key")

        order_requests.append(
            {
                "key": key,
                "payload": payload,
                "url": request.url,
            }
        )

        if not key:
            fulfill_json(
                route,
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Falta la clave de idempotencia.",
                    },
                },
                status=400,
            )
            return

        existing = stored_orders.get(key)

        if existing is None:
            # Simular que el pedido queda guardado y que se pierde
            # la respuesta que debía recibir el navegador.
            stored_orders[key] = {
                "payload": payload,
                "order": make_order_response(payload),
            }

            route.abort("failed")
            return

        if existing["payload"] != payload:
            fulfill_json(
                route,
                {
                    "success": False,
                    "error": {
                        "code": "IDEMPOTENCY_KEY_REUSED",
                        "message": (
                            "La clave se utilizó con otros datos."
                        ),
                    },
                },
                status=409,
            )
            return

        # Un reintento idéntico recupera el pedido original.
        fulfill_json(
            route,
            {
                "success": True,
                "data": existing["order"],
            },
            status=200,
        )

    def handle_tracking(route):
        request = route.request
        payload = json.loads(request.post_data or "{}")
        token = payload.get("tracking_token")

        tracking_requests.append(
            {
                "token": token,
                "url": request.url,
            }
        )

        if token != TRACKING_TOKEN:
            fulfill_json(
                route,
                {
                    "success": False,
                    "error": {
                        "code": "ORDER_TRACKING_NOT_FOUND",
                        "message": (
                            "No encontramos un pedido con ese código."
                        ),
                    },
                },
                status=404,
            )
            return

        fulfill_json(
            route,
            {
                "success": True,
                "data": {
                    "id": ORDER_ID,
                    "status": "pending",
                    "created_at": "2026-10-18T15:00:00+00:00",
                    "updated_at": "2026-10-18T15:00:00+00:00",
                    "status_history": [
                        {
                            "previous_status": None,
                            "new_status": "pending",
                            "changed_at": (
                                "2026-10-18T15:00:00+00:00"
                            ),
                        }
                    ],
                },
            },
        )

    def handle_whatsapp(route):
        whatsapp_urls.append(route.request.url)

        # Nunca abrimos el servicio real durante la prueba.
        route.fulfill(
            status=200,
            content_type="text/html; charset=utf-8",
            body=(
                "<!doctype html><html><head>"
                "<title>WhatsApp simulado</title>"
                "</head><body>Destino simulado</body></html>"
            ),
        )

    try:
        with sync_playwright() as playwright:
            browser_channel = os.getenv(
                "PLAYWRIGHT_BROWSER_CHANNEL",
                "",
            ).strip()

            if browser_channel:
                browser = playwright.chromium.launch(
                    channel=browser_channel,
                )
            else:
                # En CI se mantiene el Chromium instalado por Playwright.
                browser = playwright.chromium.launch()

            try:
                context = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    is_mobile=True,
                    has_touch=True,
                    device_scale_factor=1,
                )

                context.route(
                    re.compile(r".*/api/categories(?:\?.*)?$"),
                    handle_categories,
                )
                context.route(
                    re.compile(r".*/api/products(?:\?.*)?$"),
                    handle_products,
                )
                context.route(
                    re.compile(r".*/api/orders/track/?$"),
                    handle_tracking,
                )
                context.route(
                    re.compile(r".*/api/orders/?$"),
                    handle_create_order,
                )
                context.route(
                    re.compile(r"^https://wa\.me/.*$"),
                    handle_whatsapp,
                )

                page = context.new_page()
                page.set_default_timeout(8000)

                page.on(
                    "pageerror",
                    lambda error: browser_errors.append(str(error)),
                )

                page.goto(
                    base_url,
                    wait_until="domcontentloaded",
                )

                card = page.locator(
                    ".catalog-product-card"
                ).filter(
                    has_text=PRODUCT_NAME
                )

                expect(card).to_have_count(1)

                add_button = card.locator(
                    ".catalog-product-card__add"
                )

                expect(add_button).to_be_visible()

                # Agregar dos unidades del mismo producto.
                add_button.click()
                add_button.click()

                expect(
                    page.locator(
                        "#cart-items .catalog-cart-item"
                    )
                ).to_have_count(1)

                expect(
                    page.locator(
                        "#cart-items .catalog-cart-item__quantity"
                    )
                ).to_have_text("2")

                # Completar los campos obligatorios del formulario.
                page.locator(
                    "#order-customer-name"
                ).fill("Cliente Prueba E2E")

                page.locator(
                    "#order-customer-phone"
                ).fill("3001234567")

                page.locator(
                    "#order-customer-city"
                ).fill("Medellín")

                page.locator(
                    "#order-customer-address"
                ).fill("Calle 10 # 25-30")

                page.locator(
                    "#order-customer-observations"
                ).fill("Prueba automatizada móvil.")

                page.locator("#order-submit").click()

                # El primer intento perdió la respuesta.
                expect(
                    page.locator("#order-feedback")
                ).to_contain_text(
                    "No pudimos confirmar la respuesta del servidor."
                )

                retry_button = page.get_by_role(
                    "button",
                    name="Reintentar el mismo pedido",
                )

                expect(retry_button).to_be_visible()

                with page.expect_popup() as popup_info:
                    retry_button.click()

                whatsapp_page = popup_info.value

                try:
                    # El reintento muestra el pedido recuperado.
                    expect(
                        page.locator("#order-feedback")
                    ).to_contain_text(
                        f"Pedido #{ORDER_ID} registrado correctamente"
                    )

                    expect(
                        page.locator(
                            "#order-feedback "
                            ".catalog-order-feedback__summary"
                        )
                    ).to_be_visible()

                    expect(
                        page.locator(
                            "#order-tracking-result"
                        )
                    ).to_contain_text(
                        f"Pedido #{ORDER_ID}"
                    )

                    expect(
                        page.locator(
                            "#order-tracking-result "
                            ".catalog-order-tracking__status"
                        )
                    ).to_have_text("Pendiente")

                    # El carrito queda vacío tras la confirmación.
                    expect(
                        page.locator(
                            "#cart-items .catalog-cart-item"
                        )
                    ).to_have_count(0)

                    # Dos solicitudes idénticas, una clave, un pedido.
                    assert len(order_requests) == 2

                    first = order_requests[0]
                    second = order_requests[1]

                    assert first["key"]
                    assert first["key"] == second["key"]
                    assert first["payload"] == second["payload"]

                    assert first["payload"]["items"] == [
                        {
                            "product_id": PRODUCT_ID,
                            "quantity": 2,
                        }
                    ]

                    assert len(stored_orders) == 1

                    expect(
                        whatsapp_page
                    ).to_have_url(
                        re.compile(
                            r"^https://wa\.me/573001234567\?text="
                        )
                    )

                    whatsapp_message = parse_qs(
                        urlsplit(
                            whatsapp_urls[-1]
                        ).query
                    ).get(
                        "text",
                        [""],
                    )[0]

                    assert f"Pedido #{ORDER_ID}" in whatsapp_message
                    assert PRODUCT_NAME in whatsapp_message
                    assert "x 2" in whatsapp_message
                    assert "Total:" in whatsapp_message
                    assert "Cliente Prueba E2E" in whatsapp_message

                    # El token se envía en el cuerpo, no en la URL.
                    assert tracking_requests

                    assert all(
                        request["token"] == TRACKING_TOKEN
                        for request in tracking_requests
                    )

                    assert all(
                        TRACKING_TOKEN not in request["url"]
                        for request in tracking_requests
                    )

                    # Después de recargar, se recupera el seguimiento
                    # desde sessionStorage sin crear otro pedido.
                    previous_tracking_count = len(
                        tracking_requests
                    )

                    page.reload(
                        wait_until="domcontentloaded"
                    )

                    expect(
                        page.locator("#order-tracking-result")
                    ).to_contain_text(
                        f"Pedido #{ORDER_ID}"
                    )

                    expect(
                        page.locator("#order-tracking-token")
                    ).to_have_value(TRACKING_TOKEN)

                    assert len(
                        tracking_requests
                    ) > previous_tracking_count

                    assert len(order_requests) == 2

                    assert not browser_errors, (
                        "Errores JavaScript:\n"
                        + "\n".join(browser_errors)
                    )

                finally:
                    if not whatsapp_page.is_closed():
                        whatsapp_page.close()

                context.close()

            finally:
                browser.close()

    finally:
        server.shutdown()
        server_thread.join(timeout=5)
