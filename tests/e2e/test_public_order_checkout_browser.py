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
    delivery_quote_requests = []
    whatsapp_urls = []
    browser_errors = []
    tracking_statuses = {
        TRACKING_TOKEN: "pending",
        "b" * 43: "confirmed",
        "c" * 43: "cancelled",
        "d" * 43: "preparing",
        "e" * 43: "shipped",
        "f" * 43: "delivered",
    }

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


    def handle_delivery_config(route):
        fulfill_json(
            route,
            {
                "success": True,
                "data": {
                    "map_center_latitude": "6.2500000",
                    "map_center_longitude": "-75.5700000",
                    "max_distance_km": "50.00",
                },
            },
        )

    def handle_delivery_quote(route):
        payload = json.loads(
            route.request.post_data or "{}"
        )

        delivery_quote_requests.append(payload)

        if (
            "latitude" not in payload
            or "longitude" not in payload
        ):
            fulfill_json(
                route,
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_DELIVERY_LOCATION",
                        "message": "La ubicación no es válida.",
                    },
                },
                status=400,
            )
            return

        fulfill_json(
            route,
            {
                "success": True,
                "data": {
                    "delivery_fee": "5900.00",
                    "currency": "COP",
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

        subtotal = PRODUCT_PRICE * quantity
        delivery_fee = 5900
        total = subtotal + delivery_fee

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
                    "line_total": f"{subtotal:.2f}",
                }
            ],
            "subtotal": f"{subtotal:.2f}",
            "delivery_fee": f"{delivery_fee:.2f}",
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

        status = tracking_statuses.get(token)

        if status is None:
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

        history = [
            {
                "previous_status": None,
                "new_status": "pending",
                "changed_at": "2026-10-18T15:00:00+00:00",
            }
        ]

        if status in {"confirmed", "cancelled"}:
            history.append(
                {
                    "previous_status": "pending",
                    "new_status": status,
                    "changed_at": "2026-10-18T16:00:00+00:00",
                }
            )

        fulfill_json(
            route,
            {
                "success": True,
                "data": {
                    "id": ORDER_ID,
                    "status": status,
                    "created_at": "2026-10-18T15:00:00+00:00",
                    "updated_at": (
                        "2026-10-18T15:00:00+00:00"
                        if status == "pending"
                        else "2026-10-18T16:00:00+00:00"
                    ),
                    "status_history": history,
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

    def click_tracking_submit(page):
        """Centra el botón antes de pulsarlo para evitar el encabezado fijo."""
        submit_button = page.locator("#order-tracking-submit")

        submit_button.evaluate(
            """element => element.scrollIntoView({
                block: "center",
                inline: "nearest",
                behavior: "instant"
            })"""
        )

        submit_button.click()

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
                    re.compile(r".*/api/delivery/config/?$"),
                    handle_delivery_config,
                )
                context.route(
                    re.compile(r".*/api/delivery/quote/?$"),
                    handle_delivery_quote,
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

                # Debe instalarse antes de navegar para controlar
                # los setTimeout creados por el JavaScript del catálogo.
                page.clock.install(
                    time="2026-10-18T14:59:00Z"
                )

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

                # La página y los recursos iniciales ya cargaron.
                # Ahora pausamos el reloj para controlar los temporizadores
                # únicamente mediante fast_forward().
                page.clock.pause_at(
                    "2026-10-18T15:00:00Z"
                )

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

                page.wait_for_function(
                    """
                    document.querySelector(
                        "#delivery-destination-map"
                    )?.classList.contains(
                        "leaflet-container"
                    )
                    """
                )

                # La cotización debe estar oculta hasta seleccionar
                # una ubicación y recibir un precio válido.
                expect(
                    page.locator(
                        "#delivery-quote-summary"
                    )
                ).to_be_hidden()

                # Seleccionar el punto de entrega en el mapa.
                page.locator(
                    "#delivery-destination-map"
                ).click(
                    position={
                        "x": 180,
                        "y": 130,
                    }
                )

                # delivery.js utiliza un temporizador de 350 ms
                # antes de solicitar la cotización.
                # El reloj está pausado, por lo que debemos avanzarlo.
                page.clock.fast_forward(350)

                # Esperar la respuesta de cotización simulada.
                expect(
                    page.locator(
                        "#delivery-quote-summary"
                    )
                ).to_be_visible()

                expect(
                    page.locator(
                        "#delivery-quote-fee"
                    )
                ).to_contain_text("5.900")

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

                # La advertencia con una acción de recuperación
                # debe permanecer visible incluso después de 20 s.
                page.clock.fast_forward(20_000)

                expect(retry_button).to_be_visible()

                expect(
                    page.locator("#order-feedback")
                ).to_contain_text(
                    "No pudimos confirmar la respuesta del servidor."
                )

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
                    
                    success_message = page.locator(
                        "#order-feedback "
                        ".catalog-order-feedback__text"
                    )

                    # A los 5.999 ms el mensaje debe seguir visible.
                    page.clock.fast_forward(5999)

                    expect(
                        success_message
                    ).to_be_visible()

                    # Al completar los 6.000 ms se elimina solo el texto.
                    page.clock.fast_forward(1)

                    expect(
                        success_message
                    ).to_have_count(0)

                    # La información útil debe seguir disponible.
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
                    ).to_be_visible()

                    expect(
                        page.locator(
                            "#order-tracking-feedback"
                        )
                    ).to_be_hidden()

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
                    
                    # 1. Confirmar y cancelar deben mostrar una
                    # instrucción específica para el cliente.
                    tracking_scenarios = [
                        (
                            "b" * 43,
                            "Confirmado",
                            "La tienda confirmó tu pedido.",
                        ),
                        (
                            "c" * 43,
                            "Cancelado",
                            "Este pedido figura como cancelado.",
                        ),
                    ]

                    for token, expected_status, expected_guidance in (
                        tracking_scenarios
                    ):
                        page.locator(
                            "#order-tracking-token"
                        ).fill(token)

                        click_tracking_submit(page)

                        expect(
                            page.locator(
                                "#order-tracking-result "
                                ".catalog-order-tracking__status"
                            )
                        ).to_have_text(expected_status)

                        expect(
                            page.locator(
                                "#order-tracking-result "
                                ".catalog-order-tracking__guidance"
                            )
                        ).to_contain_text(expected_guidance)

                        expect(
                            page.locator(
                                "#order-tracking-feedback"
                            )
                        ).to_contain_text(
                            "Consulta completada correctamente."
                        )

                        # El aviso se elimina después de 6 s simulados.
                        page.clock.fast_forward(6000)

                        expect(
                            page.locator(
                                "#order-tracking-feedback"
                            )
                        ).to_be_hidden()

                        # La información del pedido permanece visible.
                        expect(
                            page.locator(
                                "#order-tracking-result"
                            )
                        ).to_be_visible()

                    # 2. Un código inexistente debe generar un error.
                    invalid_token = "z" * 43

                    page.locator(
                        "#order-tracking-token"
                    ).fill(invalid_token)

                    click_tracking_submit(page)

                    expect(
                        page.locator(
                            "#order-tracking-feedback"
                        )
                    ).to_contain_text(
                        "No encontramos un pedido con ese código."
                    )

                    # No se deben conservar datos del pedido anterior.
                    expect(
                        page.locator(
                            "#order-tracking-result"
                        )
                    ).to_be_hidden()

                    # Los errores de seguimiento desaparecen a los 8 s.
                    page.clock.fast_forward(7999)

                    expect(
                        page.locator(
                            "#order-tracking-feedback"
                        )
                    ).to_be_visible()

                    page.clock.fast_forward(1)

                    expect(
                        page.locator(
                            "#order-tracking-feedback"
                        )
                    ).to_be_hidden()

                    # 3. Después de un error debe poder hacerse
                    # una consulta válida y recuperar el resultado.
                    page.locator(
                        "#order-tracking-token"
                    ).fill(TRACKING_TOKEN)

                    click_tracking_submit(page)

                    expect(
                        page.locator(
                            "#order-tracking-result "
                            ".catalog-order-tracking__status"
                        )
                    ).to_have_text("Pendiente")

                    expect(
                        page.locator(
                            "#order-tracking-feedback"
                        )
                    ).to_contain_text(
                        "Consulta completada correctamente."
                    )

                    page.clock.fast_forward(6000)

                    expect(
                        page.locator(
                            "#order-tracking-feedback"
                        )
                    ).to_be_hidden()

                    expect(
                        page.locator(
                            "#order-tracking-result"
                        )
                    ).to_be_visible()

                    # Consultar seguimiento nunca debe volver a crear
                    # el pedido ni repetir el checkout.
                    assert len(order_requests) == 2

                    assert len(delivery_quote_requests) >= 1

                    first_payload = order_requests[0]["payload"]

                    assert (
                        first_payload["delivery_latitude"]
                        is not None
                    )

                    assert (
                        first_payload["delivery_longitude"]
                        is not None
                    )

                    assert first_payload["delivery_latitude"] == (
                        order_requests[1]["payload"][
                            "delivery_latitude"
                        ]
                    )

                    assert first_payload["delivery_longitude"] == (
                        order_requests[1]["payload"][
                            "delivery_longitude"
                        ]
                    )

                    assert not browser_errors, (
                        "Errores JavaScript:\n"
                        + "\n".join(browser_errors)
                    )

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

                    
                    # Todas las consultas deben enviar el token
                    # en el cuerpo, nunca dentro de la URL.
                    assert tracking_requests

                    expected_tracking_tokens = {
                        TRACKING_TOKEN,
                        "b" * 43,
                        "c" * 43,
                        "z" * 43,
                    }

                    assert all(
                        request["token"] in expected_tracking_tokens
                        for request in tracking_requests
                    )

                    # Debe haberse consultado el pedido creado.
                    assert any(
                        request["token"] == TRACKING_TOKEN
                        for request in tracking_requests
                    )

                    # Ningún código de seguimiento debe aparecer en la URL.
                    assert all(
                        request["token"] not in request["url"]
                        for request in tracking_requests
                    )

                    assert all(
                        not urlsplit(request["url"]).query
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
