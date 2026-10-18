"use strict";


const ORDER_API_URL =
    "/api/orders";

const ORDER_ATTEMPT_STORAGE_KEY =
    "loop_and_love.b2b_order_attempt";

const ORDER_IDEMPOTENCY_KEY_PATTERN =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const ORDER_TRACKING_SESSION_KEY =
    "loop_and_love.b2b_tracking_token";

const ORDER_TRACKING_LOCAL_KEY =
    "loop_and_love.b2b_tracking_token.remembered";

const ORDER_TRACKING_TOKEN_PATTERN =
    /^[A-Za-z0-9_-]{43}$/;

const ORDER_TRACKING_STATUS_LABELS = {
    pending: "Pendiente",
    confirmed: "Confirmado",
    cancelled: "Cancelado",
};

const orderTrackingState = {
    submitting: false,
    lastVerifiedToken: null,
};

const orderState = {
    submitting: false,
    lastAttempt: null,
    pendingRetry: null,
    blockedAttempt: null,
};


/* ==================================================
   DOM
================================================== */

function getOrderElement(
    id
) {
    return document.getElementById(
        id
    );
}


/* ==================================================
   FORMAT
================================================== */

function formatOrderPrice(
    value
) {
    const numericValue =
        Number(
            value
        );


    if (
        !Number.isFinite(
            numericValue
        )
    ) {
        return "Precio no disponible";
    }


    return new Intl.NumberFormat(
        "es-CO",
        {
            style:
                "currency",

            currency:
                "COP",

            minimumFractionDigits:
                0,

            maximumFractionDigits:
                2,
        }
    ).format(
        numericValue
    );
}


/* ==================================================
   CART PAYLOAD
================================================== */

function getOrderCartItems() {
    if (
        typeof cartState ===
        "undefined" ||
        !cartState ||
        !Array.isArray(
            cartState.items
        )
    ) {
        return [];
    }


    return cartState.items
        .filter(
            (
                item
            ) =>
                item &&
                Number.isInteger(
                    Number(
                        item.product_id
                    )
                ) &&
                Number(
                    item.product_id
                ) > 0 &&
                Number.isInteger(
                    Number(
                        item.quantity
                    )
                ) &&
                Number(
                    item.quantity
                ) > 0
        )
        .map(
            (
                item
            ) => ({
                product_id:
                    Number(
                        item.product_id
                    ),

                quantity:
                    Math.floor(
                        Number(
                            item.quantity
                        )
                    ),
            })
        );
}


function fingerprintOrderPayload(payload) {
    const source = JSON.stringify(payload);

    let hashOne = 2166136261;
    let hashTwo = 2246822519;

    for (let index = 0; index < source.length; index += 1) {
        const code = source.charCodeAt(index);

        hashOne = Math.imul(
            hashOne ^ code,
            16777619
        );

        hashTwo = Math.imul(
            hashTwo ^ code,
            3266489917
        );
    }

    return (
        `v1-${(hashOne >>> 0).toString(16)}-` +
        `${(hashTwo >>> 0).toString(16)}`
    );
}


function createOrderIdempotencyKey() {
    if (
        window.crypto &&
        typeof window.crypto.randomUUID === "function"
    ) {
        return window.crypto.randomUUID();
    }

    const bytes = new Uint8Array(16);

    if (
        window.crypto &&
        typeof window.crypto.getRandomValues === "function"
    ) {
        window.crypto.getRandomValues(bytes);
    } else {
        for (let index = 0; index < bytes.length; index += 1) {
            bytes[index] = Math.floor(Math.random() * 256);
        }
    }

    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    const hex = Array.from(
        bytes,
        (value) => value.toString(16).padStart(2, "0")
    ).join("");

    return [
        hex.slice(0, 8),
        hex.slice(8, 12),
        hex.slice(12, 16),
        hex.slice(16, 20),
        hex.slice(20, 32),
    ].join("-");
}



function readStoredOrderAttempt() {
    let rawValue;

    try {
        rawValue = window.localStorage.getItem(
            ORDER_ATTEMPT_STORAGE_KEY
        );
    } catch (error) {
        return orderState.lastAttempt;
    }

    if (rawValue === null) {
        return orderState.lastAttempt;
    }

    try {
        const attempt = JSON.parse(rawValue);

        if (
            attempt &&
            typeof attempt === "object" &&
            !Array.isArray(attempt)
        ) {
            return attempt;
        }
    } catch (error) {
        // Un registro ilegible no debe provocar una nueva clave
        // automática: podría corresponder a un pedido ya guardado.
    }

    return {
        invalid: true,
    };
}


function getOrderIdempotencyKey(payload) {
    if (
        orderState.pendingRetry ||
        orderState.blockedAttempt
    ) {
        return null;
    }

    const fingerprint = fingerprintOrderPayload(payload);
    const previousAttempt = readStoredOrderAttempt();

    if (previousAttempt) {
        if (
            previousAttempt.fingerprint === fingerprint &&
            ORDER_IDEMPOTENCY_KEY_PATTERN.test(
                previousAttempt.key || ""
            )
        ) {
            orderState.lastAttempt = previousAttempt;

            return previousAttempt.key;
        }

        // No sustituir una clave si la solicitud anterior
        // todavía no tiene un resultado confirmado.
        orderState.blockedAttempt = previousAttempt;

        return null;
    }

    const attempt = {
        key: createOrderIdempotencyKey(),
        fingerprint,
    };

    orderState.lastAttempt = attempt;

    try {
        window.localStorage.setItem(
            ORDER_ATTEMPT_STORAGE_KEY,
            JSON.stringify(attempt)
        );
    } catch (error) {
        // Se conserva en memoria para permitir reintentos
        // mientras esta página continúe abierta.
    }

    return attempt.key;
}


function clearOrderIdempotencyAttempt() {
    orderState.lastAttempt = null;
    orderState.pendingRetry = null;
    orderState.blockedAttempt = null;

    try {
        window.localStorage.removeItem(
            ORDER_ATTEMPT_STORAGE_KEY
        );
    } catch (error) {
        // No interrumpimos el flujo por un fallo de almacenamiento.
    }
}



/* ==================================================
   WHATSAPP
================================================== */

function getWhatsAppNumber() {
    const orderSection =
        getOrderElement(
            "pedido"
        );


    const rawNumber =
        orderSection?.dataset
            ?.whatsappNumber ||
        "";


    const normalized =
        String(
            rawNumber
        )
            .trim()
            .replace(
                /[^\d]/g,
                ""
            );


    if (
        normalized.startsWith(
            "00"
        )
    ) {
        return normalized.slice(
            2
        );
    }


    return normalized;
}


function isValidWhatsAppNumber(
    number
) {
    return (
        /^\d{8,15}$/.test(
            number
        )
    );
}


/* ==================================================
   RESPONSE
================================================== */

async function parseOrderResponse(
    response
) {
    try {
        return await response.json();

    } catch (
    error
    ) {
        return {
            success:
                false,

            error: {
                message:
                    "La respuesta del servidor no es válida.",
            },
        };
    }
}


function getOrderApiError(
    data,
    fallback
) {
    if (
        data &&
        data.error &&
        typeof data.error.message ===
        "string"
    ) {
        return data.error.message;
    }


    if (
        data &&
        typeof data.message ===
        "string"
    ) {
        return data.message;
    }


    return fallback;
}


/* ==================================================
   FEEDBACK
================================================== */

function clearOrderFeedback() {
    const feedback =
        getOrderElement(
            "order-feedback"
        );


    if (!feedback) {
        return;
    }


    feedback.hidden =
        true;


    feedback.className =
        "catalog-order-feedback";


    feedback.replaceChildren();
}



function showOrderFeedback(
    message,
    type = "error",
    whatsappUrl = "",
    options = {}
) {
    const feedback = getOrderElement("order-feedback");

    if (!feedback) {
        return;
    }

    feedback.replaceChildren();
    feedback.hidden = false;
    feedback.className =
        `catalog-order-feedback catalog-order-feedback--${type}`;

    const text = document.createElement("p");
    text.className = "catalog-order-feedback__text";
    text.textContent = message;

    feedback.append(text);

    if (options.summary) {
        const summary = options.summary;

        const summaryElement = document.createElement("div");
        summaryElement.className =
            "catalog-order-feedback__summary";

        const heading = document.createElement("h3");
        heading.textContent = "Resumen del pedido";

        const list = document.createElement("dl");
        list.className = "catalog-order-feedback__summary-list";

        const rows = [
            ["Número de pedido", `#${summary.orderId}`],
            ["Unidades", String(summary.itemCount)],
            ["Total", formatOrderPrice(summary.total)],
        ];

        rows.forEach(([label, value]) => {
            const term = document.createElement("dt");
            term.textContent = label;

            const description = document.createElement("dd");
            description.textContent = value;

            list.append(term, description);
        });

        summaryElement.append(heading, list);
        feedback.append(summaryElement);
    }

    if (whatsappUrl) {
        const link = document.createElement("a");

        link.className = "catalog-order-feedback__link";
        link.href = whatsappUrl;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Abrir WhatsApp";

        feedback.append(link);
    }

    if (
        typeof options.actionLabel === "string" &&
        typeof options.onAction === "function"
    ) {
        const action = document.createElement("button");

        action.type = "button";
        action.className =
            "catalog-order-feedback__action";
        action.textContent = options.actionLabel;

        action.addEventListener(
            "click",
            options.onAction
        );

        feedback.append(action);
    }
}



/* ==================================================
   SUBMITTING STATE
================================================== */


function setOrderSubmitting(submitting) {
    orderState.submitting = submitting;

    const retryPending = Boolean(orderState.pendingRetry);
    const attemptBlocked = Boolean(orderState.blockedAttempt);

    const locked =
        submitting || retryPending || attemptBlocked;

    const button = getOrderElement("order-submit");
    const clearButton = getOrderElement("cart-clear");
    const form = getOrderElement("catalog-order-form");

    if (button) {
        button.disabled = locked;

        if (submitting) {
            button.textContent = "Registrando pedido...";
        } else if (retryPending) {
            button.textContent = "Pedido pendiente de confirmar";
        } else if (attemptBlocked) {
            button.textContent = "Verifica el intento anterior";
        } else {
            button.textContent = "Enviar pedido por WhatsApp";
        }
    }

    if (clearButton) {
        clearButton.disabled = locked;
    }

    form?.querySelectorAll(
        "input, select, textarea"
    ).forEach((control) => {
        control.disabled = locked;
    });

    document.querySelectorAll(
        "#cart-items [data-cart-action]"
    ).forEach((button) => {
        button.disabled = locked;
    });

    document.querySelectorAll(
        ".catalog-product-card__add"
    ).forEach((button) => {
        button.disabled = locked;
    });
}



/* ==================================================
   WHATSAPP WINDOW
================================================== */

function openWhatsAppWindow() {
    let whatsappWindow =
        null;


    try {
        /*
         * La ventana se abre sin URL en el mismo gesto del usuario.
         * Así el navegador la considera una ventana iniciada por el
         * usuario y no por una tarea asíncrona posterior.
         */
        whatsappWindow =
            window.open(
                "",
                "_blank"
            );

    } catch (
    error
    ) {
        whatsappWindow =
            null;
    }


    if (
        !whatsappWindow
    ) {
        return null;
    }


    /*
     * Mientras esperamos la respuesta del servidor mostramos
     * contenido en lugar de dejar la pestaña completamente vacía.
     */
    try {
        whatsappWindow.document.title =
            "Loop & Love | WhatsApp";

        whatsappWindow.document.body.innerHTML = `
            <div style="
                min-height:100vh;
                display:flex;
                align-items:center;
                justify-content:center;
                padding:24px;
                margin:0;
                background:#FCF7F2;
                color:#614438;
                font-family:Arial,sans-serif;
                text-align:center;
            ">
                <div>
                    <strong>
                        Preparando tu pedido...
                    </strong>
                    <p>
                        Estamos preparando el mensaje para WhatsApp.
                    </p>
                </div>
            </div>
        `;

    } catch (
    error
    ) {
        /*
         * Si el navegador no permite modificar el documento de la
         * ventana temporal, la navegación posterior sigue siendo válida.
         */
    }


    return whatsappWindow;
}


/* ==================================================
   WHATSAPP MESSAGE
================================================== */

function buildWhatsAppMessage(
    order
) {
    const items =
        Array.isArray(
            order?.items
        )
            ? order.items
            : [];


    const lines = [
        "Hola, quiero enviar el siguiente pedido a Loop & Love.",
        "",
        `Pedido #${order.id}`,
        "",
        "*Productos:*",
    ];


    items.forEach(
        (
            item
        ) => {
            lines.push(
                `• ${item.name} x ${item.quantity} — ${formatOrderPrice(item.line_total)}`
            );
        }
    );


    lines.push(
        "",
        `*Total:* ${formatOrderPrice(order.total)}`,
        "",
        "*Datos del cliente:*",
        `Nombre: ${order.name}`,
        `Teléfono: ${order.phone}`,
        `Ciudad: ${order.city}`,
        `Dirección: ${order.address}`
    );


    if (
        typeof order.observations ===
        "string" &&
        order.observations.trim()
    ) {
        lines.push(
            `Observaciones: ${order.observations.trim()}`
        );
    }


    return lines.join(
        "\n"
    );
}


function buildWhatsAppUrl(
    number,
    order
) {
    const message =
        buildWhatsAppMessage(
            order
        );


    return (
        `https://wa.me/${number}?text=${encodeURIComponent(message)}`
    );
}


/* ==================================================
   RESET
================================================== */

function resetOrderForm() {
    const form =
        getOrderElement(
            "catalog-order-form"
        );


    if (form) {
        form.reset();
    }
}


function closeTemporaryWhatsAppWindow(whatsappWindow) {
    if (
        whatsappWindow &&
        !whatsappWindow.closed
    ) {
        try {
            whatsappWindow.close();
        } catch (error) {
            // No interrumpir la recuperación del pedido.
        }
    }
}


function discardUnresolvedOrderAttempt() {
    const confirmed = window.confirm(
        "Esta acción elimina la clave guardada en este navegador, " +
        "pero no cancela ni verifica el pedido en el servidor. " +
        "Si el pedido anterior sí se registró, podrías crear un " +
        "duplicado. ¿Has comprobado que no existe?"
    );

    if (!confirmed) {
        return;
    }

    clearOrderIdempotencyAttempt();
    setOrderSubmitting(false);

    showOrderFeedback(
        "Se descartó la clave guardada localmente. " +
        "Revisa el carrito y los datos antes de iniciar otro pedido.",
        "info"
    );
}


function showUnresolvedAttemptFeedback(message) {
    if (!orderState.blockedAttempt) {
        orderState.blockedAttempt =
            readStoredOrderAttempt() || {
                invalid: true,
            };
    }

    setOrderSubmitting(false);

    showOrderFeedback(
        message ||
        "Hay un intento anterior cuyo resultado no se pudo " +
        "confirmar. Para evitar duplicados, no enviaremos " +
        "automáticamente un pedido con una clave diferente. " +
        "Comprueba si el pedido original quedó registrado.",
        "warning",
        "",
        {
            actionLabel:
                "He comprobado que no existe; iniciar otro intento",
            onAction:
                discardUnresolvedOrderAttempt,
        }
    );
}


function showUncertainOrderResult(
    payload,
    idempotencyKey,
    whatsappWindow
) {
    closeTemporaryWhatsAppWindow(whatsappWindow);

    orderState.pendingRetry = {
        payload: JSON.parse(JSON.stringify(payload)),
        idempotencyKey,
    };

    orderState.lastAttempt = {
        key: idempotencyKey,
        fingerprint: fingerprintOrderPayload(payload),
    };

    setOrderSubmitting(false);

    showOrderFeedback(
        "No pudimos confirmar la respuesta del servidor. " +
        "El pedido podría haberse registrado. Conservamos los datos " +
        "de este intento para que puedas reintentarlo sin crear " +
        "intencionalmente una solicitud nueva. No cambies el carrito " +
        "ni los datos mientras lo resolvemos.",
        "warning",
        "",
        {
            actionLabel: "Reintentar el mismo pedido",
            onAction: retryPendingOrder,
        }
    );
}


function retryPendingOrder() {
    if (
        orderState.submitting ||
        !orderState.pendingRetry
    ) {
        return;
    }

    const attempt = orderState.pendingRetry;
    const whatsappWindow = openWhatsAppWindow();

    void performOrderSubmission(
        attempt.payload,
        attempt.idempotencyKey,
        whatsappWindow
    );
}


async function performOrderSubmission(
    payload,
    idempotencyKey,
    whatsappWindow
) {
    setOrderSubmitting(true);

    showOrderFeedback(
        "Estamos intentando registrar tu pedido...",
        "pending"
    );

    let confirmedOrder = null;

    try {
        const response = await fetch(
            ORDER_API_URL,
            {
                method: "POST",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotencyKey,
                },
                body: JSON.stringify(payload),
            }
        );

        const data = await parseOrderResponse(response);

        if (
            response.status === 409 &&
            data?.error?.code === "IDEMPOTENCY_KEY_REUSED"
        ) {
            orderState.blockedAttempt = {
                key: idempotencyKey,
                fingerprint: fingerprintOrderPayload(payload),
            };

            showUnresolvedAttemptFeedback(
                "El servidor indicó que esta clave se utilizó " +
                "con datos diferentes. No enviaremos otra solicitud " +
                "automáticamente. Verifica si el pedido original " +
                "ya existe antes de iniciar uno nuevo."
            );

            closeTemporaryWhatsAppWindow(whatsappWindow);
            return;
        }

        if (
            !response.ok ||
            data?.success !== true ||
            !data?.data ||
            data.data.id === undefined ||
            data.data.id === null
        ) {
            const uncertain =
                response.status >= 500 || response.ok;

            const message = getOrderApiError(
                data,
                "No fue posible registrar el pedido."
            );

            closeTemporaryWhatsAppWindow(whatsappWindow);

            if (uncertain) {
                showUncertainOrderResult(
                    payload,
                    idempotencyKey,
                    null
                );
            } else {
                clearOrderIdempotencyAttempt();

                showOrderFeedback(
                    message,
                    "error"
                );
            }

            return;
        }

        confirmedOrder = data.data;

        if (
            typeof confirmedOrder.tracking_token === "string" &&
            ORDER_TRACKING_TOKEN_PATTERN.test(
                confirmedOrder.tracking_token
            )
        ) {
            saveOrderTrackingToken(
                confirmedOrder.tracking_token
            );

            const forgetButton = getOrderElement(
                "order-tracking-forget"
            );

            if (forgetButton) {
                forgetButton.hidden = false;
            }

            void loadOrderTracking(
                confirmedOrder.tracking_token
            );
        } else {
            showOrderTrackingFeedback(
                "El pedido fue registrado, pero no recibimos " +
                "un código de seguimiento válido. Conserva el " +
                "número de pedido para solicitar ayuda.",
                "warning"
            );
        }

        const whatsappNumber = getWhatsAppNumber();

        const whatsappUrl = buildWhatsAppUrl(
            whatsappNumber,
            confirmedOrder
        );

        const itemCount = (
            Array.isArray(confirmedOrder.items)
                ? confirmedOrder.items
                : []
        ).reduce(
            (sum, item) => (
                sum + Math.max(0, Number(item.quantity) || 0)
            ),
            0
        );

        const summary = {
            orderId: confirmedOrder.id,
            total: confirmedOrder.total,
            itemCount,
        };

        /*
         * El servidor confirmó la creación. Ahora limpiamos
         * los datos locales y después eliminamos la clave.
         */
        try {
            if (typeof clearCart === "function") {
                clearCart();
            } else {
                window.localStorage.removeItem(
                    "loop_and_love.b2b_cart"
                );
            }
        } catch (cleanupError) {
            console.error(
                "No se pudo limpiar el carrito después de confirmar el pedido."
            );
        }

        resetOrderForm();
        clearOrderIdempotencyAttempt();

        const successMessage =
            `Pedido #${confirmedOrder.id} registrado correctamente. ` +
            "Revisa el resumen y envía el mensaje desde WhatsApp " +
            "para completar el contacto.";

        if (whatsappWindow) {
            showOrderFeedback(
                successMessage,
                "success",
                "",
                { summary }
            );

            try {
                whatsappWindow.location.replace(whatsappUrl);
            } catch (navigationError) {
                showOrderFeedback(
                    successMessage,
                    "success",
                    whatsappUrl,
                    { summary }
                );
            }
        } else {
            showOrderFeedback(
                successMessage,
                "success",
                whatsappUrl,
                { summary }
            );
        }

    } catch (error) {
        closeTemporaryWhatsAppWindow(whatsappWindow);

        if (confirmedOrder) {
            /*
             * La respuesta confirmó el pedido. Un problema posterior
             * al crear el pedido no debe presentarse como un fallo
             * de creación.
             */
            let whatsappUrl = "";

            try {
                whatsappUrl = buildWhatsAppUrl(
                    getWhatsAppNumber(),
                    confirmedOrder
                );
            } catch (urlError) {
                // El pedido permanece confirmado.
            }

            showOrderFeedback(
                `El pedido #${confirmedOrder.id} está registrado, ` +
                "pero no pudimos preparar automáticamente WhatsApp. " +
                "Puedes intentar abrir el enlace.",
                "success",
                whatsappUrl,
                {
                    summary: {
                        orderId: confirmedOrder.id,
                        total: confirmedOrder.total,
                        itemCount: (
                            Array.isArray(confirmedOrder.items)
                                ? confirmedOrder.items
                                : []
                        ).reduce(
                            (sum, item) => (
                                sum + Math.max(
                                    0,
                                    Number(item.quantity) || 0
                                )
                            ),
                            0
                        ),
                    },
                }
            );

        } else {
            /*
             * Un error de red puede ocurrir después de que el servidor
             * guarde el pedido. Conservamos la misma clave para reintentar.
             */
            showUncertainOrderResult(
                payload,
                idempotencyKey,
                null
            );
        }

    } finally {
        setOrderSubmitting(false);
    }
}


/* ==================================================
   SUBMIT
================================================== */

async function submitCatalogOrder(event) {
    event.preventDefault();

    if (
        orderState.submitting ||
        orderState.pendingRetry
    ) {
        return;
    }

    if (orderState.blockedAttempt) {
        showUnresolvedAttemptFeedback();
        return;
    }

    clearOrderFeedback();

    const form = getOrderElement("catalog-order-form");

    if (!form) {
        return;
    }

    const items = getOrderCartItems();

    if (!items.length) {
        showOrderFeedback(
            "Agrega al menos un producto antes de enviar el pedido."
        );

        return;
    }

    if (!form.reportValidity()) {
        return;
    }

    const whatsappNumber = getWhatsAppNumber();

    if (!isValidWhatsAppNumber(whatsappNumber)) {
        showOrderFeedback(
            "El número de WhatsApp no está configurado correctamente. " +
            "Intenta nuevamente más tarde."
        );

        return;
    }

    const payload = {
        name:
            getOrderElement("order-customer-name")?.value || "",

        phone:
            getOrderElement("order-customer-phone")?.value || "",

        city:
            getOrderElement("order-customer-city")?.value || "",

        address:
            getOrderElement("order-customer-address")?.value || "",

        observations:
            getOrderElement("order-customer-observations")?.value || null,

        items,
    };

    const idempotencyKey =
        getOrderIdempotencyKey(payload);

    if (!idempotencyKey) {
        showUnresolvedAttemptFeedback();
        return;
    }

    /*
     * Abrimos WhatsApp desde el gesto original del cliente
     * para evitar que el navegador bloquee la ventana.
     */
    const whatsappWindow = openWhatsAppWindow();

    await performOrderSubmission(
        payload,
        idempotencyKey,
        whatsappWindow
    );
}


function getOrderTrackingStatusLabel(status) {
    return ORDER_TRACKING_STATUS_LABELS[status]
        || "Estado no disponible";
}


function formatOrderTrackingDate(value) {
    if (!value) {
        return "Fecha no disponible";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Fecha no disponible";
    }

    return new Intl.DateTimeFormat(
        "es-CO",
        {
            dateStyle: "medium",
            timeStyle: "short",
        }
    ).format(date);
}


function showOrderTrackingFeedback(
    message,
    type = "info"
) {
    const feedback = getOrderElement(
        "order-tracking-feedback"
    );

    if (!feedback) {
        return;
    }

    feedback.textContent = message;
    feedback.className =
        `catalog-order-tracking__feedback ` +
        `catalog-order-tracking__feedback--${type}`;

    feedback.hidden = false;
}


function hideOrderTrackingFeedback() {
    const feedback = getOrderElement(
        "order-tracking-feedback"
    );

    if (!feedback) {
        return;
    }

    feedback.hidden = true;
    feedback.textContent = "";
}


function clearOrderTrackingResult() {
    const result = getOrderElement(
        "order-tracking-result"
    );

    if (!result) {
        return;
    }

    result.replaceChildren();
    result.hidden = true;
}


function saveOrderTrackingToken(token) {
    if (
        typeof token !== "string" ||
        !ORDER_TRACKING_TOKEN_PATTERN.test(token)
    ) {
        return false;
    }

    const tokenInput = getOrderElement(
        "order-tracking-token"
    );

    const rememberCheckbox = getOrderElement(
        "order-tracking-remember"
    );

    if (tokenInput) {
        tokenInput.value = token;
    }

    orderTrackingState.lastVerifiedToken = token;

    if (rememberCheckbox?.checked) {
        try {
            window.localStorage.setItem(
                ORDER_TRACKING_LOCAL_KEY,
                token
            );

            try {
                window.sessionStorage.removeItem(
                    ORDER_TRACKING_SESSION_KEY
                );
            } catch (error) {
                // El token persistente ya quedó guardado.
            }

            return true;
        } catch (error) {
            // Si localStorage no está disponible, usamos la sesión.
        }
    }

    try {
        window.sessionStorage.setItem(
            ORDER_TRACKING_SESSION_KEY,
            token
        );
    } catch (error) {
        // El seguimiento manual seguirá disponible en esta página.
    }

    try {
        window.localStorage.removeItem(
            ORDER_TRACKING_LOCAL_KEY
        );
    } catch (error) {
        // La limpieza del almacenamiento es de mejor esfuerzo.
    }

    return true;
}


function readSavedOrderTrackingToken() {
    const rememberCheckbox = getOrderElement(
        "order-tracking-remember"
    );

    try {
        const rememberedToken =
            window.localStorage.getItem(
                ORDER_TRACKING_LOCAL_KEY
            );

        if (
            rememberedToken &&
            ORDER_TRACKING_TOKEN_PATTERN.test(
                rememberedToken
            )
        ) {
            if (rememberCheckbox) {
                rememberCheckbox.checked = true;
            }

            return rememberedToken;
        }

        if (rememberedToken) {
            window.localStorage.removeItem(
                ORDER_TRACKING_LOCAL_KEY
            );
        }
    } catch (error) {
        // Intentar después con sessionStorage.
    }

    try {
        const sessionToken =
            window.sessionStorage.getItem(
                ORDER_TRACKING_SESSION_KEY
            );

        if (
            sessionToken &&
            ORDER_TRACKING_TOKEN_PATTERN.test(
                sessionToken
            )
        ) {
            if (rememberCheckbox) {
                rememberCheckbox.checked = false;
            }

            return sessionToken;
        }

        if (sessionToken) {
            window.sessionStorage.removeItem(
                ORDER_TRACKING_SESSION_KEY
            );
        }
    } catch (error) {
        // No es imprescindible disponer de almacenamiento local.
    }

    return null;
}


function clearSavedOrderTrackingToken() {
    try {
        window.sessionStorage.removeItem(
            ORDER_TRACKING_SESSION_KEY
        );
    } catch (error) {
        // Continuar con el intento de limpieza.
    }

    try {
        window.localStorage.removeItem(
            ORDER_TRACKING_LOCAL_KEY
        );
    } catch (error) {
        // Continuar con la limpieza visual.
    }

    orderTrackingState.lastVerifiedToken = null;

    const tokenInput = getOrderElement(
        "order-tracking-token"
    );

    const rememberCheckbox = getOrderElement(
        "order-tracking-remember"
    );

    const forgetButton = getOrderElement(
        "order-tracking-forget"
    );

    if (tokenInput) {
        tokenInput.value = "";
    }

    if (rememberCheckbox) {
        rememberCheckbox.checked = false;
    }

    if (forgetButton) {
        forgetButton.hidden = true;
    }

    hideOrderTrackingFeedback();
    clearOrderTrackingResult();
}


function renderOrderTrackingResult(data) {
    const result = getOrderElement(
        "order-tracking-result"
    );

    if (!result) {
        return;
    }

    result.replaceChildren();

    const heading = document.createElement("h4");
    heading.className =
        "catalog-order-tracking__result-title";

    heading.textContent = `Pedido #${data.id}`;

    const currentStatus = document.createElement("span");

    const knownStatus =
        Object.prototype.hasOwnProperty.call(
            ORDER_TRACKING_STATUS_LABELS,
            data.status
        );

    currentStatus.className =
        "catalog-order-tracking__status" +
        (
            knownStatus
                ? ` catalog-order-tracking__status--${data.status}`
                : ""
        );

    currentStatus.textContent =
        getOrderTrackingStatusLabel(data.status);

    const createdDate = document.createElement("p");

    createdDate.textContent =
        `Creado: ${formatOrderTrackingDate(data.created_at)}`;

    const updatedDate = document.createElement("p");

    updatedDate.textContent =
        `Última actualización: ${formatOrderTrackingDate(data.updated_at)
        }`;

    const historyHeading = document.createElement("h5");
    historyHeading.textContent = "Historial del pedido";

    const historyList = document.createElement("ol");

    historyList.className =
        "catalog-order-tracking__history";

    const history = Array.isArray(data.status_history)
        ? data.status_history
        : [];

    history.forEach((entry) => {
        const item = document.createElement("li");

        const transition = document.createElement("strong");

        if (entry.previous_status) {
            transition.textContent =
                `${getOrderTrackingStatusLabel(entry.previous_status)} ` +
                `→ ${getOrderTrackingStatusLabel(entry.new_status)}`;
        } else {
            transition.textContent =
                `Pedido registrado · ${getOrderTrackingStatusLabel(entry.new_status)
                }`;
        }

        const date = document.createElement("time");

        date.textContent = formatOrderTrackingDate(
            entry.changed_at
        );

        if (entry.changed_at) {
            date.dateTime = entry.changed_at;
        }

        item.append(
            transition,
            date
        );

        historyList.append(item);
    });

    result.append(
        heading,
        currentStatus,
        createdDate,
        updatedDate,
        historyHeading
    );

    if (history.length) {
        result.append(historyList);
    } else {
        const empty = document.createElement("p");

        empty.textContent =
            "Todavía no hay eventos disponibles en el historial.";

        result.append(empty);
    }

    result.hidden = false;
}


async function loadOrderTracking(token) {
    if (orderTrackingState.submitting) {
        return;
    }

    const normalizedToken = (
        typeof token === "string"
            ? token.trim()
            : ""
    );

    const tokenInput = getOrderElement(
        "order-tracking-token"
    );

    const submitButton = getOrderElement(
        "order-tracking-submit"
    );

    const forgetButton = getOrderElement(
        "order-tracking-forget"
    );

    if (
        !ORDER_TRACKING_TOKEN_PATTERN.test(
            normalizedToken
        )
    ) {
        showOrderTrackingFeedback(
            "Ingresa un código válido de 43 caracteres.",
            "error"
        );

        clearOrderTrackingResult();
        return;
    }

    orderTrackingState.submitting = true;

    if (tokenInput) {
        tokenInput.disabled = true;
    }

    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Consultando...";
    }

    hideOrderTrackingFeedback();

    showOrderTrackingFeedback(
        "Consultando el estado del pedido...",
        "pending"
    );

    try {
        const response = await fetch(
            `${ORDER_API_URL}/track`,
            {
                method: "POST",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    tracking_token: normalizedToken,
                }),
            }
        );

        const data = await response.json().catch(
            () => null
        );

        if (
            !response.ok ||
            data?.success !== true ||
            !data?.data
        ) {
            if (response.status === 404) {
                throw new Error(
                    "No encontramos un pedido con ese código. " +
                    "Verifica que lo hayas copiado completo."
                );
            }

            if (response.status === 429) {
                throw new Error(
                    "Se realizaron demasiadas consultas. " +
                    "Espera un momento e inténtalo nuevamente."
                );
            }

            throw new Error(
                "No pudimos consultar el pedido. " +
                "Comprueba tu conexión e inténtalo nuevamente."
            );
        }

        saveOrderTrackingToken(normalizedToken);

        if (forgetButton) {
            forgetButton.hidden = false;
        }

        renderOrderTrackingResult(data.data);

        showOrderTrackingFeedback(
            "Consulta completada correctamente.",
            "success"
        );

    } catch (error) {
        showOrderTrackingFeedback(
            error instanceof Error
                ? error.message
                : "No pudimos consultar el pedido.",
            "error"
        );
    } finally {
        orderTrackingState.submitting = false;

        if (tokenInput) {
            tokenInput.disabled = false;
        }

        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = "Consultar estado";
        }
    }
}


function setupCatalogOrderTracking() {
    const form = getOrderElement(
        "order-tracking-form"
    );

    const tokenInput = getOrderElement(
        "order-tracking-token"
    );

    const rememberCheckbox = getOrderElement(
        "order-tracking-remember"
    );

    const forgetButton = getOrderElement(
        "order-tracking-forget"
    );

    if (
        !form ||
        !tokenInput
    ) {
        return;
    }

    form.addEventListener(
        "submit",
        (event) => {
            event.preventDefault();

            void loadOrderTracking(
                tokenInput.value
            );
        }
    );

    rememberCheckbox?.addEventListener(
        "change",
        () => {
            const verifiedToken =
                orderTrackingState.lastVerifiedToken;

            if (
                verifiedToken &&
                ORDER_TRACKING_TOKEN_PATTERN.test(
                    verifiedToken
                )
            ) {
                saveOrderTrackingToken(
                    verifiedToken
                );
            }
        }
    );

    forgetButton?.addEventListener(
        "click",
        clearSavedOrderTrackingToken
    );

    const storedToken =
        readSavedOrderTrackingToken();

    if (storedToken) {
        tokenInput.value = storedToken;

        if (forgetButton) {
            forgetButton.hidden = false;
        }

        void loadOrderTracking(
            storedToken
        );
    }
}


/* ==================================================
   INITIALIZE
================================================== */

function setupCatalogOrderForm() {
    const form =
        getOrderElement(
            "catalog-order-form"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        (
            event
        ) => {
            void submitCatalogOrder(
                event
            );
        }
    );
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        setupCatalogOrderForm();
        setupCatalogOrderTracking();
    }
);