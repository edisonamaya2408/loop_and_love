"use strict";

const ORDER_NEXT_STATUS = Object.freeze({
    pending: "confirmed",
    confirmed: "preparing",
    preparing: "shipped",
    shipped: "delivered",
});

const ORDER_NEXT_STATUS_LABELS = Object.freeze({
    confirmed: "Confirmar pedido",
    preparing: "Iniciar preparación",
    shipped: "Marcar como enviado",
    delivered: "Marcar como entregado",
});

const ORDER_STATUS_WHATSAPP_GUIDANCE = Object.freeze({
    pending:
        "Hemos recibido tu pedido y está pendiente de confirmación. Te informaremos cuando la tienda lo revise.",

    confirmed:
        "La tienda ha confirmado tu pedido. Puedes contactarnos por este medio para coordinar los detalles de entrega.",

    preparing:
        "Tu pedido está en preparación. Estamos trabajando para tenerlo listo.",

    shipped:
        "Tu pedido figura como enviado. Puedes contactarnos para coordinar la recepción y consultar los detalles de entrega.",

    delivered:
        "Nuestro registro indica que tu pedido fue entregado. Si tienes alguna novedad, responde a este mensaje.",

    cancelled:
        "Tu pedido figura como cancelado. Si tienes dudas sobre este estado, responde a este mensaje para que podamos ayudarte.",
});

function getNextOrderStatus(status) {
    return ORDER_NEXT_STATUS[status] || null;
}

const ORDER_TRACKING_TOKEN_PATTERN =
    /^[A-Za-z0-9_-]{43}$/;


function getOrderTrackingToken(order) {
    const token =
        typeof order?.tracking_token === "string"
            ? order.tracking_token.trim()
            : "";

    return ORDER_TRACKING_TOKEN_PATTERN.test(token)
        ? token
        : "";
}

const adminOrdersState = {
    page: 1,
    perPage: 12,
    total: 0,
    pages: 0,
    search: "",
    status: "",
    orders: [],
    currentOrder: null,
    updatingStatus: false,
    autoRefreshEnabled: false,
    autoRefreshTimer: null,
    visibilityBound: false,
    requestInFlight: false,
    lastKnownPendingCount: null,
    unseenNewPendingCount: 0,
    pendingCountRequestInFlight: false,
    pendingNoticeDismissBound: false,
    detailFocusReturnElement: null,
    detailFocusOrderId: null,
    rotatingTrackingToken: false,
};


function getOrdersElement(
    id
) {
    return document.getElementById(
        id
    );
}


function getOrderDetailElement(
    id
) {
    return document.getElementById(
        id
    );
}


function normalizeAdminCustomerWhatsAppNumber(
    phone
) {
    const digits =
        String(
            phone || ""
        )
            .trim()
            .replace(
                /[^\d]/g,
                ""
            );


    if (
        digits.startsWith(
            "00"
        )
    ) {
        return digits.slice(
            2
        );
    }


    /*
     * Los pedidos actuales utilizan teléfonos
     * principalmente de Colombia.
     *
     * Un celular colombiano de 10 dígitos
     * que comienza por 3 se convierte a
     * formato internacional +57.
     */
    if (
        digits.length === 10 &&
        digits.startsWith("3")
    ) {
        return `57${digits}`;
    }


    return digits;
}


function isValidAdminCustomerWhatsAppNumber(
    number
) {
    return (
        /^57\d{10}$/.test(
            number
        ) ||
        /^\d{11,15}$/.test(
            number
        )
    );
}


function buildAdminCustomerWhatsAppMessage(
    order
) {
    const items =
        Array.isArray(
            order?.items
        )
            ? order.items
            : [];


    const lines = [
        `Hola ${order.name || "cliente"}, te contactamos de Loop & Love respecto a tu pedido #${order.id}.`,
        "",
        `*Estado:* ${getStatusLabel(order.status)}`,
        "",
        "*Productos:*",
    ];


    items.forEach(
        (
            item
        ) => {
            lines.push(
                `• ${item.name || "Producto"} x ${item.quantity ?? 0} — ${formatCurrency(item.line_total)}`
            );
        }
    );


    const subtotal = order.subtotal ??
        items.reduce(
            (sum, item) => (
                sum + Number(item.line_total || 0)
            ),
            0
        );

    const deliveryFee = order.delivery_fee ?? 0;

    lines.push(
        "",
        `*Subtotal productos:* ${formatCurrency(subtotal)}`,
        `*Domicilio:* ${formatCurrency(deliveryFee)}`,
        `*Total:* ${formatCurrency(order.total)}`,
        "",
        "*Datos de entrega:*",
        `Ciudad: ${order.city || "Sin ciudad"}`,
        `Dirección: ${order.address || "Sin dirección"}`
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


    lines.push(
        "",
        "Quedamos atentos."
    );


    return lines.join(
        "\n"
    );
}


function buildAdminCustomerWhatsAppUrl(
    number,
    order
) {
    return (
        `https://wa.me/${number}?text=${encodeURIComponent(
            buildAdminCustomerWhatsAppMessage(
                order
            )
        )}`
    );
}


function contactCustomerByWhatsApp(
    order
) {
    if (
        !order ||
        !order.id
    ) {
        return;
    }


    const number =
        normalizeAdminCustomerWhatsAppNumber(
            order.phone
        );


    const message =
        getOrderDetailElement(
            "admin-order-detail-message"
        );


    if (
        !isValidAdminCustomerWhatsAppNumber(
            number
        )
    ) {
        setOrderDetailMessage(
            message,
            "El teléfono del cliente no tiene un formato válido para WhatsApp."
        );

        return;
    }


    setOrderDetailMessage(
        message,
        ""
    );


    const whatsappUrl =
        buildAdminCustomerWhatsAppUrl(
            number,
            order
        );


    const whatsappWindow =
        window.open(
            whatsappUrl,
            "_blank",
            "noopener,noreferrer"
        );


    if (
        !whatsappWindow
    ) {
        setOrderDetailMessage(
            message,
            "El navegador bloqueó la ventana de WhatsApp. Permite ventanas emergentes para este sitio e inténtalo nuevamente."
        );
    }
}


function setOrderDetailMessage(
    element,
    message
) {
    if (!element) {
        return;
    }

    if (!message) {
        element.hidden = true;
        element.textContent = "";
        return;
    }

    element.hidden = false;
    element.textContent = message;
}


function setOrderTrackingFeedback(
    message,
    type = "success"
) {
    const feedback = getOrderDetailElement(
        "admin-order-tracking-feedback"
    );

    if (!feedback) {
        return;
    }

    feedback.className =
        "admin-orders-tracking__feedback";

    if (message && type === "error") {
        feedback.classList.add(
            "admin-orders-tracking__feedback--error"
        );
    }

    feedback.textContent = message || "";
    feedback.hidden = !message;
}


async function copyOrderTrackingToken() {
    const order = adminOrdersState.currentOrder;
    const token = getOrderTrackingToken(order);

    if (!token) {
        setOrderTrackingFeedback(
            "Este pedido no tiene un código de seguimiento válido.",
            "error"
        );

        return;
    }

    try {
        if (
            window.isSecureContext &&
            navigator.clipboard?.writeText
        ) {
            await navigator.clipboard.writeText(token);
        } else {
            // Alternativa para navegadores sin Clipboard API.
            const textarea =
                document.createElement("textarea");

            textarea.value = token;
            textarea.setAttribute("readonly", "");
            textarea.style.position = "fixed";
            textarea.style.left = "-9999px";

            document.body.appendChild(textarea);
            textarea.select();

            let copied = false;

            try {
                copied = document.execCommand("copy");
            } finally {
                textarea.remove();
            }

            if (!copied) {
                throw new Error(
                    "No fue posible copiar el código."
                );
            }
        }

        setOrderTrackingFeedback(
            "Código copiado. Ya puedes enviárselo al cliente."
        );
    } catch {
        setOrderTrackingFeedback(
            "No se pudo copiar automáticamente. Selecciona el código visible y cópialo manualmente.",
            "error"
        );
    }
}


function shareOrderTrackingByWhatsApp(order) {
    if (!order || !order.id) {
        return;
    }

    const token = getOrderTrackingToken(order);

    if (!token) {
        setOrderTrackingFeedback(
            "Este pedido no tiene un código de seguimiento válido.",
            "error"
        );

        return;
    }

    const number =
        normalizeAdminCustomerWhatsAppNumber(
            order.phone
        );

    if (!isValidAdminCustomerWhatsAppNumber(number)) {
        setOrderTrackingFeedback(
            "El teléfono del cliente no tiene un formato válido para WhatsApp. Copia el código y compártelo manualmente.",
            "error"
        );

        return;
    }

    const trackingUrl =
        `${window.location.origin}/#pedido`;

    const message = [
        `Hola ${order.name || "cliente"}, te compartimos nuevamente el código de seguimiento de tu pedido #${order.id} de Loop & Love.`,
        "",
        `Consulta el estado aquí: ${trackingUrl}`,
        "",
        `Código de seguimiento: ${token}`,
        "",
        "En la sección de seguimiento, pega el código y pulsa «Consultar estado»."
    ].join("\n");

    const whatsappUrl =
        `https://wa.me/${number}?text=${encodeURIComponent(message)}`;

    const whatsappWindow = window.open(
        whatsappUrl,
        "_blank"
    );

    if (!whatsappWindow) {
        setOrderTrackingFeedback(
            "El navegador bloqueó la ventana de WhatsApp. Permite ventanas emergentes e inténtalo nuevamente.",
            "error"
        );

        return;
    }

    // Evitar que la ventana de WhatsApp acceda a la página de origen.
    whatsappWindow.opener = null;

    setOrderTrackingFeedback(
        "Se abrió WhatsApp con el código y las instrucciones de seguimiento."
    );
}


function buildOrderStatusWhatsAppMessage(order) {
    const token = getOrderTrackingToken(order);

    const guidance =
        ORDER_STATUS_WHATSAPP_GUIDANCE[order.status] ||
        "Puedes responder a este mensaje si necesitas más información.";

    const trackingUrl =
        `${window.location.origin}/#pedido`;

    return [
        `Hola ${order.name || "cliente"}, te compartimos una actualización de tu pedido #${order.id} de Loop & Love.`,
        "",
        `*Estado actual:* ${getStatusLabel(order.status)}`,
        "",
        guidance,
        "",
        `*Consulta el seguimiento:* ${trackingUrl}`,
        "",
        `*Código de seguimiento:* ${token}`,
        "",
        "Entra en la sección de seguimiento del catálogo, pega el código y pulsa «Consultar estado».",
        "",
        "Por seguridad, mantén privado tu código de seguimiento.",
        "",
        "Gracias por comprar en Loop & Love."
    ].join("\n");
}


async function recordOrderStatusNotificationPrepared(
    orderId
) {
    const messageElement = getOrderDetailElement(
        "admin-order-detail-message"
    );

    try {
        const response = await adminFetch(
            `/api/admin/orders/${encodeURIComponent(
                orderId
            )}/status-notification/prepared`,
            {
                method: "POST",
            }
        );

        const data = await parseJsonSafely(response);

        if (!response.ok || data?.success !== true) {
            throw new Error(
                data?.error?.message
                || "No fue posible registrar la preparación de la notificación."
            );
        }

    } catch (error) {
        setOrderDetailMessage(
            messageElement,
            "WhatsApp se abrió, pero no fue posible registrar la preparación de la notificación en la auditoría."
        );
    }
}


function notifyOrderStatusByWhatsApp(order) {
    if (!order || !order.id) {
        return;
    }

    const messageElement = getOrderDetailElement(
        "admin-order-detail-message"
    );

    const token = getOrderTrackingToken(order);

    if (!token) {
        setOrderDetailMessage(
            messageElement,
            "Este pedido no tiene un código de seguimiento válido. Regenera el código antes de notificar al cliente."
        );

        return;
    }

    const number =
        normalizeAdminCustomerWhatsAppNumber(
            order.phone
        );

    if (!isValidAdminCustomerWhatsAppNumber(number)) {
        setOrderDetailMessage(
            messageElement,
            "El teléfono del cliente no tiene un formato válido para WhatsApp."
        );

        return;
    }

    setOrderDetailMessage(
        messageElement,
        ""
    );

    const message = buildOrderStatusWhatsAppMessage(
        order
    );

    const whatsappUrl =
        `https://wa.me/${number}?text=${encodeURIComponent(message)}`;

    const whatsappWindow = window.open(
        whatsappUrl,
        "_blank"
    );

    if (!whatsappWindow) {
        setOrderDetailMessage(
            messageElement,
            "El navegador bloqueó la ventana de WhatsApp. Permite las ventanas emergentes e inténtalo nuevamente."
        );

        return;
    }

    whatsappWindow.opener = null;

    setOrderDetailMessage(
        messageElement,
        "Se abrió WhatsApp con la actualización del pedido. Revisa el mensaje y pulsa Enviar para notificar al cliente."
    );

    void recordOrderStatusNotificationPrepared(
        order.id
    );
}


async function rotateOrderTrackingToken() {
    const order = adminOrdersState.currentOrder;

    if (
        !order ||
        !order.id ||
        adminOrdersState.rotatingTrackingToken
    ) {
        return;
    }

    const confirmed = window.confirm(
        "¿Regenerar el código del pedido #" +
        `${order.id}? El código anterior dejará de funcionar ` +
        "y tendrás que compartir el nuevo con el cliente."
    );

    if (!confirmed) {
        return;
    }

    const previousToken = getOrderTrackingToken(order);

    const rotateButton = getOrderDetailElement(
        "admin-order-tracking-rotate-button"
    );

    adminOrdersState.rotatingTrackingToken = true;

    if (rotateButton) {
        rotateButton.disabled = true;
    }

    setOrderTrackingFeedback(
        "Regenerando el código de seguimiento..."
    );

    try {
        const response = await adminFetch(
            `/api/admin/orders/${encodeURIComponent(
                order.id
            )}/tracking-token/rotate`,
            {
                method: "POST",
            }
        );

        const data = await parseJsonSafely(response);

        if (!response.ok) {
            throw new Error(getErrorMessage(data));
        }

        const updatedOrder = data?.data;

        if (
            !updatedOrder ||
            typeof updatedOrder !== "object"
        ) {
            throw new Error(
                "El servidor no devolvió un pedido válido."
            );
        }

        const newToken = getOrderTrackingToken(updatedOrder);

        if (
            !newToken ||
            newToken === previousToken
        ) {
            // La petición pudo completarse, pero la respuesta
            // no confirmó un token nuevo. Volvemos a consultar.
            await loadOrderDetail(order.id);

            throw new Error(
                "No se pudo confirmar el nuevo código. " +
                "Se volvió a consultar el pedido."
            );
        }

        renderOrderDetail(updatedOrder);

        updateOrderInCurrentPage(updatedOrder);

        renderOrders(adminOrdersState.orders);

        setOrderTrackingFeedback(
            "Código regenerado correctamente. El anterior " +
            "ya no funciona; comparte el nuevo con el cliente."
        );

    } catch (error) {
        if (
            error instanceof Error &&
            error.message === "La sesión ha expirado."
        ) {
            return;
        }

        setOrderTrackingFeedback(
            error instanceof Error
                ? error.message
                : "No fue posible regenerar el código.",
            "error"
        );

    } finally {
        adminOrdersState.rotatingTrackingToken = false;

        const currentButton = getOrderDetailElement(
            "admin-order-tracking-rotate-button"
        );

        if (currentButton) {
            currentButton.disabled = !(
                adminOrdersState.currentOrder?.id
            );
        }
    }
}


function setOrdersMessage(
    element,
    message
) {
    if (!element) {
        return;
    }

    if (!message) {
        element.hidden = true;
        element.textContent = "";
        return;
    }

    element.hidden = false;
    element.textContent = message;
}


function formatCurrency(
    value
) {
    const numericValue =
        Number(value);

    if (
        !Number.isFinite(
            numericValue
        )
    ) {
        return "$0";
    }

    return new Intl.NumberFormat(
        "es-CO",
        {
            style: "currency",
            currency: "COP",
            maximumFractionDigits: 0,
        }
    ).format(
        numericValue
    );
}


function formatDate(
    value
) {
    if (!value) {
        return "—";
    }

    const date =
        new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return "—";
    }

    return date.toLocaleString(
        "es-CO",
        {
            dateStyle: "medium",
            timeStyle: "short",
        }
    );
}


function formatRelativeTime(
    value,
    now = new Date()
) {
    if (!value) {
        return null;
    }

    const eventDate = new Date(value);
    const referenceDate = (
        now instanceof Date
            ? now
            : new Date(now)
    );

    if (
        Number.isNaN(eventDate.getTime()) ||
        Number.isNaN(referenceDate.getTime())
    ) {
        return null;
    }

    const differenceSeconds = Math.round(
        (eventDate.getTime() - referenceDate.getTime())
        / 1000
    );

    if (Math.abs(differenceSeconds) < 5) {
        return "ahora";
    }

    const absoluteSeconds = Math.abs(
        differenceSeconds
    );

    let unit;
    let divisor;
    let fallbackLabel;

    if (absoluteSeconds < 60) {
        unit = "second";
        divisor = 1;
        fallbackLabel = "segundo";
    } else if (absoluteSeconds < 3600) {
        unit = "minute";
        divisor = 60;
        fallbackLabel = "minuto";
    } else if (absoluteSeconds < 86400) {
        unit = "hour";
        divisor = 3600;
        fallbackLabel = "hora";
    } else if (absoluteSeconds < 2592000) {
        unit = "day";
        divisor = 86400;
        fallbackLabel = "día";
    } else if (absoluteSeconds < 31536000) {
        unit = "month";
        divisor = 2629800;
        fallbackLabel = "mes";
    } else {
        unit = "year";
        divisor = 31557600;
        fallbackLabel = "año";
    }

    const amount = Math.max(
        1,
        Math.round(
            absoluteSeconds / divisor
        )
    );

    if (
        typeof Intl.RelativeTimeFormat === "function"
    ) {
        const formatter = new Intl.RelativeTimeFormat(
            "es-CO",
            {
                numeric: "auto",
            }
        );

        const difference = (
            differenceSeconds < 0
                ? -amount
                : amount
        );

        return formatter.format(
            difference,
            unit
        );
    }

    const pluralLabel = (
        amount === 1
            ? fallbackLabel
            : fallbackLabel === "mes"
                ? "meses"
                : fallbackLabel === "día"
                    ? "días"
                    : `${fallbackLabel}s`
    );

    return differenceSeconds < 0
        ? `hace ${amount} ${pluralLabel}`
        : `dentro de ${amount} ${pluralLabel}`;
}


function getStatusLabel(
    status
) {
    const labels = {
        pending: "Pendiente",
        confirmed: "Confirmado",
        preparing: "En preparación",
        shipped: "Enviado",
        delivered: "Entregado",
        cancelled: "Cancelado",
    };

    return (
        labels[status]
        || status
        || "Sin estado"
    );
}


function getPendingAgePresentation(
    createdAt,
    now = new Date()
) {
    if (!createdAt) {
        return null;
    }

    const createdDate = new Date(createdAt);
    const currentTimestamp = now.getTime();

    if (
        Number.isNaN(createdDate.getTime()) ||
        Number.isNaN(currentTimestamp)
    ) {
        return null;
    }

    const elapsedMilliseconds = Math.max(
        0,
        currentTimestamp - createdDate.getTime()
    );

    const elapsedMinutes = Math.floor(
        elapsedMilliseconds / 60000
    );

    let elapsedLabel;

    if (elapsedMinutes < 1) {
        elapsedLabel = "menos de 1 min";
    } else if (elapsedMinutes < 60) {
        elapsedLabel = `${elapsedMinutes} min`;
    } else {
        const elapsedHours = Math.floor(
            elapsedMinutes / 60
        );

        if (elapsedHours < 24) {
            elapsedLabel = `${elapsedHours} h`;
        } else {
            const days = Math.floor(
                elapsedHours / 24
            );

            const hours = elapsedHours % 24;

            elapsedLabel =
                `${days} ${days === 1 ? "día" : "días"}`;

            if (hours > 0) {
                elapsedLabel += ` ${hours} h`;
            }
        }
    }

    let tone = "fresh";

    if (elapsedMinutes >= 240) {
        tone = "urgent";
    } else if (elapsedMinutes >= 60) {
        tone = "attention";
    }

    return {
        label: `Pendiente hace ${elapsedLabel}`,
        tone,
        elapsedMinutes,
    };
}


function renderOrderStatusHistory(
    history,
    currentStatus
) {
    const container =
        getOrderDetailElement(
            "admin-order-status-history"
        );


    if (!container) {
        return;
    }


    container.replaceChildren();


    const normalizedHistory =
        Array.isArray(
            history
        )
            ? [...history].reverse()
            : [];


    if (
        !normalizedHistory.length
    ) {

        container.append(
            createTextElement(
                "p",
                "admin-orders-status-history__empty",
                "No hay historial de estados disponible."
            )
        );

        return;
    }


    const latestEntry = normalizedHistory[0];

    if (
        latestEntry &&
        latestEntry.new_status === currentStatus
    ) {
        const relativeTime = formatRelativeTime(
            latestEntry.changed_at
        );

        if (relativeTime) {
            const currentSummary =
                document.createElement("div");

            currentSummary.className =
                "admin-orders-status-current-summary";

            const currentStatusLabel =
                createTextElement(
                    "strong",
                    null,
                    `Estado actual: ${getStatusLabel(
                        currentStatus
                    )}`
                );

            const currentStatusDuration =
                createTextElement(
                    "span",
                    null,
                    `Desde ${formatDate(
                        latestEntry.changed_at
                    )} · ${relativeTime}`
                );

            currentSummary.append(
                currentStatusLabel,
                currentStatusDuration
            );

            container.append(
                currentSummary
            );
        }
    }


    normalizedHistory.forEach(
        (
            entry,
            index
        ) => {

            const item =
                document.createElement(
                    "article"
                );


            item.className =
                "admin-orders-status-history__item";


            if (
                index ===
                normalizedHistory.length - 1
            ) {
                item.classList.add(
                    "admin-orders-status-history__item--last"
                );
            }


            const marker =
                document.createElement(
                    "span"
                );


            marker.className =
                "admin-orders-status-history__marker";


            marker.setAttribute(
                "aria-hidden",
                "true"
            );


            const content =
                document.createElement(
                    "div"
                );


            content.className =
                "admin-orders-status-history__content";


            const transition =
                document.createElement(
                    "strong"
                );


            const previousStatus =
                entry?.previous_status;


            const newStatus =
                entry?.new_status;


            if (
                previousStatus
            ) {
                transition.textContent =
                    `${getStatusLabel(
                        previousStatus
                    )} → ${getStatusLabel(
                        newStatus
                    )}`;
            } else {
                transition.textContent =
                    `Pedido creado · ${getStatusLabel(
                        newStatus
                    )}`;
            }


            const status =
                document.createElement(
                    "span"
                );


            status.className =
                "admin-orders-status " +
                `admin-orders-status--${newStatus}`;


            status.textContent =
                getStatusLabel(
                    newStatus
                );


            const date =
                document.createElement(
                    "time"
                );


            date.className =
                "admin-orders-status-history__date";


            date.dateTime =
                entry?.changed_at
                || "";


            date.textContent =
                formatDate(
                    entry?.changed_at
                );


            date.title = formatDate(
                entry?.changed_at
            );


            const relativeTime = formatRelativeTime(
                entry?.changed_at
            );


            const changedByName = (
                typeof entry?.changed_by_name === "string"
                && entry.changed_by_name.trim()
            )
                ? entry.changed_by_name.trim()
                : "";

            const changedByEmail = (
                typeof entry?.changed_by_email === "string"
                && entry.changed_by_email.trim()
            )
                ? entry.changed_by_email.trim()
                : "";

            let actorAttribution;

            if (changedByName) {
                actorAttribution = `Responsable: ${changedByName}`;

                if (changedByEmail) {
                    actorAttribution += ` (${changedByEmail})`;
                }
            } else if (previousStatus) {
                actorAttribution =
                    "Responsable no registrado (evento histórico)";
            } else {
                actorAttribution =
                    "Actor no registrado en el evento inicial";
            }

            const actorElement = createTextElement(
                "span",
                "admin-orders-status-history__actor",
                actorAttribution
            );

            if (relativeTime) {
                const relativeDate = createTextElement(
                    "span",
                    "admin-orders-status-history__relative",
                    relativeTime
                );

                relativeDate.setAttribute(
                    "aria-label",
                    `Tiempo transcurrido desde este cambio: ${relativeTime}`
                );

                content.append(
                    transition,
                    status,
                    date,
                    relativeDate,
                    actorElement
                );
            } else {
                content.append(
                    transition,
                    status,
                    date,
                    actorElement
                );
            }


            item.append(
                marker,
                content
            );


            container.append(
                item
            );
        }
    );
}


function renderOrderDetail(
    order
) {
    adminOrdersState.currentOrder =
        order;

    const content =
        getOrderDetailElement(
            "admin-order-detail-content"
        );

    const loading =
        getOrderDetailElement(
            "admin-order-detail-loading"
        );

    const title =
        getOrderDetailElement(
            "admin-order-detail-title"
        );

    const name =
        getOrderDetailElement(
            "admin-order-detail-name"
        );

    const phone =
        getOrderDetailElement(
            "admin-order-detail-phone"
        );

    const city =
        getOrderDetailElement(
            "admin-order-detail-city"
        );

    const address =
        getOrderDetailElement(
            "admin-order-detail-address"
        );

    const status =
        getOrderDetailElement(
            "admin-order-detail-status"
        );

    const trackingTokenElement =
        getOrderDetailElement(
            "admin-order-tracking-token"
        );

    const copyTrackingButton =
        getOrderDetailElement(
            "admin-order-tracking-copy-button"
        );

    const shareTrackingButton =
        getOrderDetailElement(
            "admin-order-tracking-whatsapp-button"
        );

    const rotateTrackingButton =
        getOrderDetailElement(
            "admin-order-tracking-rotate-button"
        );

    const total =
        getOrderDetailElement(
            "admin-order-detail-total"
        );

    const subtotalElement = getOrderDetailElement(
        "admin-order-detail-subtotal"
    );

    const deliveryFeeElement = getOrderDetailElement(
        "admin-order-detail-delivery-fee"
    );

    const deliveryDistanceElement = getOrderDetailElement(
        "admin-order-detail-delivery-distance"
    );

    const deliveryBillableKmElement = getOrderDetailElement(
        "admin-order-detail-delivery-billable-km"
    );

    const observations =
        getOrderDetailElement(
            "admin-order-detail-observations"
        );

    const created =
        getOrderDetailElement(
            "admin-order-detail-created"
        );

    const updated =
        getOrderDetailElement(
            "admin-order-detail-updated"
        );

    const items =
        getOrderDetailElement(
            "admin-order-detail-items"
        );


    if (loading) {
        loading.hidden = true;
    }

    if (content) {
        content.hidden = false;
    }


    if (title) {
        title.textContent =
            `Pedido #${order.id}`;
    }

    if (name) {
        name.textContent =
            order.name || "Sin nombre";
    }

    if (phone) {
        phone.textContent =
            order.phone || "Sin teléfono";
    }

    if (city) {
        city.textContent =
            order.city || "Sin ciudad";
    }

    if (address) {
        address.textContent =
            order.address || "Sin dirección";
    }

    if (status) {
        status.className =
            "admin-orders-status " +
            `admin-orders-status--${order.status}`;

        status.textContent =
            getStatusLabel(
                order.status
            );
    }

    updateOrderStatusActions(
        order.status
    );

    const trackingToken =
        getOrderTrackingToken(order);

    if (trackingTokenElement) {
        trackingTokenElement.textContent =
            trackingToken || "No disponible";
    }

    if (copyTrackingButton) {
        copyTrackingButton.disabled =
            !trackingToken;
    }

    if (shareTrackingButton) {
        shareTrackingButton.disabled =
            !trackingToken;
    }

    if (rotateTrackingButton) {
        rotateTrackingButton.disabled = (
            !order.id ||
            adminOrdersState.rotatingTrackingToken
        );
    }

    setOrderTrackingFeedback("");

    renderOrderStatusHistory(
        order.status_history,
        order.status
    );

    if (total) {
        total.textContent =
            formatCurrency(
                order.total
            );
    }

    const itemsSubtotal = Array.isArray(order.items)
        ? order.items.reduce(
            (sum, item) => (
                sum + Number(item.line_total || 0)
            ),
            0
        )
        : 0;

    if (subtotalElement) {
        subtotalElement.textContent = formatCurrency(
            order.subtotal ?? itemsSubtotal
        );
    }

    if (deliveryFeeElement) {
        deliveryFeeElement.textContent = formatCurrency(
            order.delivery_fee ?? 0
        );
    }

    if (deliveryDistanceElement) {
        deliveryDistanceElement.textContent =
            order.delivery_distance_km == null
                ? "No disponible"
                : `${order.delivery_distance_km} km`;
    }

    if (deliveryBillableKmElement) {
        deliveryBillableKmElement.textContent =
            order.delivery_billable_km == null
                ? ""
                : `${order.delivery_billable_km} km cobrados`;
    }

    if (observations) {
        observations.textContent =
            order.observations
            || "Sin observaciones.";
    }

    if (created) {
        created.textContent =
            formatDate(
                order.created_at
            );
    }

    if (updated) {
        updated.textContent =
            formatDate(
                order.updated_at
            );
    }


    if (!items) {
        return;
    }

    items.replaceChildren();


    const orderItems =
        Array.isArray(
            order.items
        )
            ? order.items
            : [];


    orderItems.forEach(
        (item) => {

            const row =
                document.createElement(
                    "tr"
                );


            const productCell =
                createCell();

            productCell.append(
                createTextElement(
                    "strong",
                    null,
                    item.name
                    || "Producto"
                )
            );


            const codeCell =
                createCell();

            codeCell.textContent =
                item.code || "—";


            const quantityCell =
                createCell();

            quantityCell.textContent =
                String(
                    item.quantity
                    ?? 0
                );


            const priceCell =
                createCell();

            priceCell.textContent =
                formatCurrency(
                    item.unit_price
                );


            const subtotalCell =
                createCell();

            subtotalCell.textContent =
                formatCurrency(
                    item.line_total
                );


            row.append(
                productCell,
                codeCell,
                quantityCell,
                priceCell,
                subtotalCell
            );

            items.append(
                row
            );
        }
    );
}


function setOrderStatusButtonsDisabled(
    disabled
) {
    const confirmButton =
        getOrderDetailElement(
            "admin-order-confirm-button"
        );

    const cancelButton =
        getOrderDetailElement(
            "admin-order-cancel-button"
        );

    if (confirmButton) {
        confirmButton.disabled =
            disabled;
    }

    if (cancelButton) {
        cancelButton.disabled =
            disabled;
    }
}


function updateOrderStatusActions(status) {
    const actions = getOrderDetailElement(
        "admin-order-status-actions"
    );

    const confirmButton = getOrderDetailElement(
        "admin-order-confirm-button"
    );

    const cancelButton = getOrderDetailElement(
        "admin-order-cancel-button"
    );

    const nextStatus = getNextOrderStatus(status);
    const canCancel = status === "pending";
    const hasActions = Boolean(nextStatus || canCancel);

    if (actions) {
        actions.hidden = !hasActions;
    }

    if (confirmButton) {
        confirmButton.hidden = !nextStatus;

        if (nextStatus) {
            confirmButton.textContent =
                ORDER_NEXT_STATUS_LABELS[nextStatus];
        }
    }

    if (cancelButton) {
        cancelButton.hidden = !canCancel;
    }

    if (!hasActions) {
        setOrderStatusButtonsDisabled(false);
    }
}


function updateOrderInCurrentPage(
    order
) {
    const index =
        adminOrdersState.orders.findIndex(
            (item) =>
                Number(item.id) ===
                Number(order.id)
        );

    if (index === -1) {
        return;
    }

    adminOrdersState.orders[index] =
        order;
}


async function updateOrderStatus(
    status
) {
    const order =
        adminOrdersState.currentOrder;

    const expectedNextStatus = order
        ? getNextOrderStatus(order.status)
        : null;

    const isAllowedCancellation = Boolean(
        order &&
        order.status === "pending" &&
        status === "cancelled"
    );

    if (
        !order ||
        (
            status !== expectedNextStatus &&
            !isAllowedCancellation
        )
    ) {
        return;
    }

    if (
        status === "cancelled" &&
        !window.confirm(
            "¿Confirmas que deseas cancelar este pedido?"
        )
    ) {
        return;
    }

    const message =
        getOrderDetailElement(
            "admin-order-detail-message"
        );

    setOrderDetailMessage(
        message,
        ""
    );

    adminOrdersState.updatingStatus =
        true;

    setOrderStatusButtonsDisabled(
        true
    );

    try {
        const response =
            await adminFetch(
                `/api/admin/orders/${encodeURIComponent(
                    order.id
                )}/status`,
                {
                    method: "PATCH",
                    headers: {
                        "Content-Type":
                            "application/json",
                    },
                    body: JSON.stringify({
                        status,
                    }),
                }
            );


        const data =
            await parseJsonSafely(
                response
            );


        if (!response.ok) {
            throw new Error(
                getErrorMessage(
                    data
                )
            );
        }


        const updatedOrder =
            data?.data;


        if (
            !updatedOrder ||
            typeof updatedOrder !== "object"
        ) {
            throw new Error(
                "El servidor no devolvió un pedido válido."
            );
        }


        renderOrderDetail(
            updatedOrder
        );


        updateOrderInCurrentPage(
            updatedOrder
        );


        renderOrders(
            adminOrdersState.orders
        );


        setOrderDetailMessage(
            message,
            "El estado del pedido se actualizó correctamente."
        );

    } catch (error) {

        if (
            error instanceof Error &&
            error.message ===
            "La sesión ha expirado."
        ) {
            return;
        }


        setOrderDetailMessage(
            message,
            error instanceof Error
                ? error.message
                : "No fue posible actualizar el estado del pedido."
        );

    } finally {

        adminOrdersState.updatingStatus =
            false;

        const currentStatus =
            adminOrdersState.currentOrder?.status;

        if (
            currentStatus === "pending" ||
            getNextOrderStatus(currentStatus)
        ) {
            setOrderStatusButtonsDisabled(false);
        }

    }
}


async function loadOrderDetail(
    orderId
) {
    const loading =
        getOrderDetailElement(
            "admin-order-detail-loading"
        );

    const content =
        getOrderDetailElement(
            "admin-order-detail-content"
        );

    const message =
        getOrderDetailElement(
            "admin-order-detail-message"
        );


    setOrderDetailMessage(
        message,
        ""
    );


    if (loading) {
        loading.hidden = false;
    }

    if (content) {
        content.hidden = true;
    }


    try {

        const response =
            await adminFetch(
                `/api/admin/orders/${encodeURIComponent(
                    orderId
                )}`
            );


        const data =
            await parseJsonSafely(
                response
            );


        if (!response.ok) {
            throw new Error(
                getErrorMessage(
                    data
                )
            );
        }


        const order =
            data?.data;


        if (
            !order ||
            typeof order !== "object"
        ) {
            throw new Error(
                "El servidor no devolvió un pedido válido."
            );
        }


        renderOrderDetail(
            order
        );

    } catch (error) {

        if (
            error instanceof Error &&
            error.message ===
            "La sesión ha expirado."
        ) {
            return;
        }


        if (loading) {
            loading.hidden = true;
        }


        setOrderDetailMessage(
            message,
            error instanceof Error
                ? error.message
                : "No fue posible cargar el pedido."
        );
    }
}


function getOrderDetailFocusableElements() {
    const modal = getOrderDetailElement(
        "admin-order-detail-modal"
    );

    const dialog = modal?.querySelector(
        ".admin-orders-modal__dialog"
    );

    if (!dialog) {
        return [];
    }

    const selector = [
        "a[href]",
        "button:not([disabled])",
        "input:not([disabled])",
        "select:not([disabled])",
        "textarea:not([disabled])",
        "[tabindex]:not([tabindex='-1'])",
    ].join(",");

    return Array.from(
        dialog.querySelectorAll(selector)
    ).filter((element) => {
        if (
            element.hidden ||
            element.closest("[hidden]") ||
            element.getAttribute("aria-hidden") === "true"
        ) {
            return false;
        }

        const style = window.getComputedStyle(element);

        return (
            style.display !== "none" &&
            style.visibility !== "hidden"
        );
    });
}


function restoreOrderDetailFocus() {
    const returnElement =
        adminOrdersState.detailFocusReturnElement;

    const orderId =
        adminOrdersState.detailFocusOrderId;

    adminOrdersState.detailFocusReturnElement = null;
    adminOrdersState.detailFocusOrderId = null;

    if (
        returnElement &&
        returnElement.isConnected &&
        !returnElement.disabled &&
        !returnElement.closest("[hidden]")
    ) {
        returnElement.focus();
        return;
    }

    if (orderId !== null) {
        const orderButton = Array.from(
            document.querySelectorAll(
                ".admin-orders-order__button[data-order-id]"
            )
        ).find(
            (element) =>
                element.dataset.orderId === String(orderId)
        );

        if (orderButton) {
            orderButton.focus();
            return;
        }
    }

    const search = getOrdersElement(
        "admin-orders-search"
    );

    if (search) {
        search.focus();
    }
}


function handleOrderDetailModalKeydown(event) {
    const modal = getOrderDetailElement(
        "admin-order-detail-modal"
    );

    if (!modal || modal.hidden) {
        return;
    }

    if (event.key === "Escape") {
        event.preventDefault();
        closeOrderDetail();
        return;
    }

    if (event.key !== "Tab") {
        return;
    }

    const dialog = modal.querySelector(
        ".admin-orders-modal__dialog"
    );

    const focusableElements =
        getOrderDetailFocusableElements();

    if (!focusableElements.length) {
        event.preventDefault();
        dialog?.focus();
        return;
    }

    const first = focusableElements[0];
    const last = focusableElements[
        focusableElements.length - 1
    ];

    const activeElement = document.activeElement;
    const focusIsInsideDialog =
        dialog?.contains(activeElement);

    if (event.shiftKey) {
        if (
            activeElement === first ||
            !focusIsInsideDialog
        ) {
            event.preventDefault();
            last.focus();
        }

        return;
    }

    if (
        activeElement === last ||
        !focusIsInsideDialog
    ) {
        event.preventDefault();
        first.focus();
    }
}


function openOrderDetail(
    orderId,
    triggerElement = document.activeElement
) {
    const modal = getOrderDetailElement(
        "admin-order-detail-modal"
    );

    if (!modal) {
        return;
    }

    adminOrdersState.detailFocusReturnElement = (
        triggerElement &&
        triggerElement !== document.body &&
        typeof triggerElement.focus === "function"
    )
        ? triggerElement
        : null;

    adminOrdersState.detailFocusOrderId =
        String(orderId);

    adminOrdersState.currentOrder = null;
    adminOrdersState.updatingStatus = false;

    updateOrderStatusActions(null);

    modal.hidden = false;

    modal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.classList.add(
        "admin-modal-open"
    );

    const closeButton = getOrderDetailElement(
        "admin-order-detail-close"
    );

    if (closeButton) {
        closeButton.focus();
    }

    loadOrderDetail(orderId);
}


function closeOrderDetail() {
    const modal = getOrderDetailElement(
        "admin-order-detail-modal"
    );

    if (!modal) {
        return;
    }

    const wasOpen = !modal.hidden;

    modal.hidden = true;

    modal.setAttribute(
        "aria-hidden",
        "true"
    );

    document.body.classList.remove(
        "admin-modal-open"
    );

    adminOrdersState.currentOrder = null;
    adminOrdersState.updatingStatus = false;

    updateOrderStatusActions(null);

    if (wasOpen) {
        restoreOrderDetailFocus();
    }
}


function createCell() {
    return document.createElement(
        "td"
    );
}


function createTextElement(
    tag,
    className,
    text
) {
    const element =
        document.createElement(
            tag
        );

    if (className) {
        element.className =
            className;
    }

    element.textContent =
        text;

    return element;
}


function renderOrders(
    orders
) {
    adminOrdersState.orders =
        Array.isArray(orders)
            ? orders
            : [];

    const tableBody =
        getOrdersElement(
            "admin-orders-table-body"
        );

    const emptyState =
        getOrdersElement(
            "admin-orders-empty"
        );

    const loading =
        getOrdersElement(
            "admin-orders-loading"
        );

    const count =
        getOrdersElement(
            "admin-orders-count"
        );


    if (!tableBody) {
        return;
    }


    tableBody.replaceChildren();


    if (loading) {
        loading.hidden = true;
    }


    if (count) {
        count.textContent =
            String(
                adminOrdersState.total
            );
    }


    if (!orders.length) {

        if (emptyState) {
            emptyState.hidden = false;
        }

        return;
    }


    if (emptyState) {
        emptyState.hidden = true;
    }


    orders.forEach(
        (order) => {

            const row =
                document.createElement(
                    "tr"
                );


            const orderCell =
                createCell();


            const orderWrapper =
                document.createElement(
                    "div"
                );


            orderWrapper.className =
                "admin-orders-order";


            const orderButton =
                document.createElement(
                    "button"
                );


            orderButton.type =
                "button";

            orderButton.className =
                "admin-orders-order__button";

            orderButton.textContent =
                `#${order.id}`;

            orderButton.dataset.orderId =
                String(
                    order.id
                );


            orderButton.addEventListener(
                "click",
                () => {
                    openOrderDetail(
                        order.id,
                        orderButton
                    );
                }
            );


            orderWrapper.append(
                orderButton,
                createTextElement(
                    "span",
                    null,
                    `${order.items?.length || 0} producto(s)`
                )
            );


            orderCell.append(
                orderWrapper
            );


            const customerCell =
                createCell();


            const customerWrapper =
                document.createElement(
                    "div"
                );


            customerWrapper.className =
                "admin-orders-customer";


            customerWrapper.append(
                createTextElement(
                    "strong",
                    null,
                    order.name || "Sin nombre"
                ),
                createTextElement(
                    "span",
                    null,
                    order.phone || "Sin teléfono"
                )
            );


            customerCell.append(
                customerWrapper
            );


            const locationCell =
                createCell();


            const locationWrapper =
                document.createElement(
                    "div"
                );


            locationWrapper.className =
                "admin-orders-location";


            locationWrapper.append(
                createTextElement(
                    "strong",
                    null,
                    order.city || "Sin ciudad"
                ),
                createTextElement(
                    "span",
                    null,
                    order.address || "Sin dirección"
                )
            );


            locationCell.append(
                locationWrapper
            );


            const totalCell =
                createCell();


            totalCell.append(
                createTextElement(
                    "strong",
                    "admin-orders-total",
                    formatCurrency(
                        order.total
                    )
                )
            );


            const statusCell = createCell();

            const status = document.createElement("span");

            status.className =
                "admin-orders-status " +
                `admin-orders-status--${order.status}`;

            status.textContent = getStatusLabel(order.status);

            const statusGroup = document.createElement("div");
            statusGroup.className = "admin-orders-status-group";

            statusGroup.append(status);

            if (order.status === "pending") {
                const pendingAge = getPendingAgePresentation(
                    order.created_at
                );

                if (pendingAge) {
                    const ageElement = createTextElement(
                        "span",
                        "admin-orders-pending-age " +
                        `admin-orders-pending-age--${pendingAge.tone}`,
                        pendingAge.label
                    );

                    ageElement.setAttribute(
                        "aria-label",
                        `Antigüedad del pedido: ${pendingAge.label}`
                    );

                    statusGroup.append(ageElement);
                }
            }

            statusCell.append(statusGroup);


            const dateCell =
                createCell();


            dateCell.append(
                createTextElement(
                    "span",
                    "admin-orders-date",
                    formatDate(
                        order.created_at
                    )
                )
            );


            row.append(
                orderCell,
                customerCell,
                locationCell,
                totalCell,
                statusCell,
                dateCell
            );


            tableBody.append(
                row
            );
        }
    );
}


function updatePagination(
    pagination
) {
    const previous =
        getOrdersElement(
            "admin-orders-prev"
        );

    const next =
        getOrdersElement(
            "admin-orders-next"
        );

    const info =
        getOrdersElement(
            "admin-orders-pagination-info"
        );


    if (pagination) {

        adminOrdersState.page =
            pagination.page;

        adminOrdersState.perPage =
            pagination.per_page;

        adminOrdersState.total =
            pagination.total;

        adminOrdersState.pages =
            pagination.pages;

    }


    if (previous) {
        previous.disabled =
            !pagination ||
            !pagination.has_previous;
    }


    if (next) {
        next.disabled =
            !pagination ||
            !pagination.has_next;
    }


    if (info) {

        const pages =
            pagination?.pages || 0;

        info.textContent =
            `Página ${pagination?.page || 1
            } de ${pages || 1}`;
    }
}


async function loadOrders(
    options = {}
) {
    const silent =
        options.silent === true;


    if (
        adminOrdersState.requestInFlight
    ) {
        return;
    }


    adminOrdersState.requestInFlight =
        true;


    const loading =
        getOrdersElement(
            "admin-orders-loading"
        );

    const message =
        getOrdersElement(
            "admin-orders-message"
        );

    const emptyState =
        getOrdersElement(
            "admin-orders-empty"
        );


    if (!silent) {
        setOrdersMessage(
            message,
            ""
        );


        if (loading) {
            loading.hidden = false;
        }


        if (emptyState) {
            emptyState.hidden = true;
        }
    }


    const params =
        new URLSearchParams();


    params.set(
        "page",
        String(
            adminOrdersState.page
        )
    );


    params.set(
        "per_page",
        String(
            adminOrdersState.perPage
        )
    );


    if (
        adminOrdersState.search
    ) {
        params.set(
            "search",
            adminOrdersState.search
        );
    }


    if (
        adminOrdersState.status
    ) {
        params.set(
            "status",
            adminOrdersState.status
        );
    }


    try {

        const response =
            await adminFetch(
                `/api/admin/orders?${params.toString()}`
            );


        const data =
            await parseJsonSafely(
                response
            );


        if (!response.ok) {
            throw new Error(
                getErrorMessage(
                    data
                )
            );
        }


        const orders =
            Array.isArray(
                data?.data
            )
                ? data.data
                : [];


        renderOrders(
            orders
        );


        updatePagination(
            data?.pagination
        );


        if (silent) {
            setOrdersMessage(
                message,
                ""
            );
        }

    } catch (error) {

        if (
            error instanceof Error &&
            error.message ===
            "La sesión ha expirado."
        ) {
            return;
        }


        /*
         * Una actualización automática no debe borrar
         * la información actualmente visible por un error
         * temporal de red o del servidor.
         */

        if (!silent) {

            setOrdersMessage(
                message,
                error instanceof Error
                    ? error.message
                    : "No fue posible cargar los pedidos."
            );


            if (loading) {
                loading.hidden = true;
            }


            updatePagination(
                null
            );
        }

    } finally {

        adminOrdersState.requestInFlight =
            false;
    }
}


function setupFilters() {
    const form =
        getOrdersElement(
            "admin-orders-filter-form"
        );

    const search =
        getOrdersElement(
            "admin-orders-search"
        );

    const status =
        getOrdersElement(
            "admin-orders-status"
        );

    const clearButton =
        getOrdersElement(
            "admin-orders-clear-button"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        (event) => {

            event.preventDefault();


            adminOrdersState.search =
                search
                    ? search.value.trim()
                    : "";


            adminOrdersState.status =
                status
                    ? status.value
                    : "";


            adminOrdersState.page =
                1;


            loadOrders();
        }
    );


    if (clearButton) {

        clearButton.addEventListener(
            "click",
            () => {

                if (search) {
                    search.value = "";
                }


                if (status) {
                    status.value = "";
                }


                adminOrdersState.search =
                    "";

                adminOrdersState.status =
                    "";

                adminOrdersState.page =
                    1;


                loadOrders();
            }
        );
    }
}


function setupPagination() {
    const previous =
        getOrdersElement(
            "admin-orders-prev"
        );

    const next =
        getOrdersElement(
            "admin-orders-next"
        );


    if (previous) {

        previous.addEventListener(
            "click",
            () => {

                if (
                    adminOrdersState.page
                    <= 1
                ) {
                    return;
                }


                adminOrdersState.page -=
                    1;


                loadOrders();
            }
        );
    }


    if (next) {

        next.addEventListener(
            "click",
            () => {

                if (
                    adminOrdersState.page
                    >= adminOrdersState.pages
                ) {
                    return;
                }


                adminOrdersState.page +=
                    1;


                loadOrders();
            }
        );
    }
}


function setupOrderDetailModal() {
    const closeButton =
        getOrderDetailElement(
            "admin-order-detail-close"
        );

    const confirmButton =
        getOrderDetailElement(
            "admin-order-confirm-button"
        );

    const cancelButton =
        getOrderDetailElement(
            "admin-order-cancel-button"
        );

    const rotateTrackingButton =
        getOrderDetailElement(
            "admin-order-tracking-rotate-button"
        );

    const whatsappButton =
        getOrderDetailElement(
            "admin-order-whatsapp-button"
        );

    const statusWhatsAppButton =
        getOrderDetailElement(
            "admin-order-status-whatsapp-button"
        );

    const copyTrackingButton =
        getOrderDetailElement(
            "admin-order-tracking-copy-button"
        );

    const shareTrackingButton =
        getOrderDetailElement(
            "admin-order-tracking-whatsapp-button"
        );

    const backdrop =
        document.querySelector(
            "[data-order-detail-close]"
        );


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeOrderDetail
        );
    }


    if (confirmButton) {
        confirmButton.addEventListener(
            "click",
            () => {
                const nextStatus = getNextOrderStatus(
                    adminOrdersState.currentOrder?.status
                );

                if (nextStatus) {
                    updateOrderStatus(nextStatus);
                }
            }
        );
    }


    if (cancelButton) {

        cancelButton.addEventListener(
            "click",
            () => {
                updateOrderStatus(
                    "cancelled"
                );
            }
        );
    }


    if (whatsappButton) {

        whatsappButton.addEventListener(
            "click",
            () => {
                contactCustomerByWhatsApp(
                    adminOrdersState.currentOrder
                );
            }
        );
    }

    if (statusWhatsAppButton) {
        statusWhatsAppButton.addEventListener(
            "click",
            () => {
                notifyOrderStatusByWhatsApp(
                    adminOrdersState.currentOrder
                );
            }
        );
    }

    if (copyTrackingButton) {
        copyTrackingButton.addEventListener(
            "click",
            () => {
                void copyOrderTrackingToken();
            }
        );
    }

    if (shareTrackingButton) {
        shareTrackingButton.addEventListener(
            "click",
            () => {
                shareOrderTrackingByWhatsApp(
                    adminOrdersState.currentOrder
                );
            }
        );
    }

    if (rotateTrackingButton) {
        rotateTrackingButton.addEventListener(
            "click",
            () => {
                void rotateOrderTrackingToken();
            }
        );
    }


    if (backdrop) {

        backdrop.addEventListener(
            "click",
            closeOrderDetail
        );
    }


    document.addEventListener(
        "keydown",
        handleOrderDetailModalKeydown
    );
}


function applyOrderFiltersFromQueryString() {
    const params =
        new URLSearchParams(
            window.location.search
        );


    const statusParam =
        params.get(
            "status"
        );


    if (
        !statusParam
    ) {
        return;
    }


    const validStatuses = new Set([
        "pending",
        "confirmed",
        "preparing",
        "shipped",
        "delivered",
        "cancelled",
    ]);


    if (
        !validStatuses.has(
            statusParam
        )
    ) {
        return;
    }


    const statusSelect =
        getOrdersElement(
            "admin-orders-status"
        );


    adminOrdersState.status =
        statusParam;

    adminOrdersState.page =
        1;


    if (statusSelect) {
        statusSelect.value =
            statusParam;
    }
}


function openOrderFromQueryString() {
    const params =
        new URLSearchParams(
            window.location.search
        );


    const orderId =
        params.get(
            "order_id"
        );


    if (!orderId) {
        return;
    }


    if (
        !/^\d+$/.test(
            orderId
        )
    ) {
        return;
    }


    const numericOrderId =
        Number(
            orderId
        );


    if (
        !Number.isSafeInteger(
            numericOrderId
        ) ||
        numericOrderId <= 0
    ) {
        return;
    }


    openOrderDetail(
        numericOrderId
    );
}


function renderAdminOrdersNewPendingNotice() {
    const notice =
        getOrdersElement(
            "admin-orders-new-pending-notice"
        );

    const message =
        getOrdersElement(
            "admin-orders-new-pending-notice-message"
        );

    if (!notice || !message) {
        return;
    }

    const count =
        adminOrdersState.unseenNewPendingCount;

    if (count <= 0) {
        notice.hidden = true;
        message.textContent = "";
        return;
    }

    message.textContent =
        count === 1
            ? "Llegó 1 nuevo pedido pendiente desde la última actualización."
            : `Llegaron ${count} nuevos pedidos pendientes desde la última actualización.`;

    notice.hidden = false;
}


function observeAdminOrdersPendingCount(
    totalValue
) {
    const currentCount =
        Number(totalValue);

    if (
        !Number.isSafeInteger(currentCount) ||
        currentCount < 0
    ) {
        return;
    }

    /*
     * En la primera consulta solo establecemos
     * la referencia, sin alertar por pedidos antiguos.
     */
    if (
        adminOrdersState.lastKnownPendingCount === null
    ) {
        adminOrdersState.lastKnownPendingCount =
            currentCount;

        return;
    }

    const increase =
        currentCount -
        adminOrdersState.lastKnownPendingCount;

    adminOrdersState.lastKnownPendingCount =
        currentCount;

    if (increase > 0) {
        adminOrdersState.unseenNewPendingCount +=
            increase;

        renderAdminOrdersNewPendingNotice();
    }
}


async function checkForNewPendingOrders() {
    if (
        document.visibilityState !== "visible" ||
        adminOrdersState.pendingCountRequestInFlight ||
        adminOrdersState.updatingStatus
    ) {
        return;
    }

    adminOrdersState.pendingCountRequestInFlight =
        true;

    try {
        const response =
            await adminFetch(
                "/api/admin/orders?page=1&per_page=1&status=pending"
            );

        const data =
            await parseJsonSafely(
                response
            );

        if (!response.ok) {
            return;
        }

        const totalPending =
            data?.pagination?.total;

        if (
            totalPending === undefined ||
            totalPending === null
        ) {
            return;
        }

        observeAdminOrdersPendingCount(
            totalPending
        );

    } catch (error) {
        /*
         * La comprobación es auxiliar.
         * Un fallo temporal no debe borrar la tabla
         * ni interrumpir el trabajo del administrador.
         */
    } finally {
        adminOrdersState.pendingCountRequestInFlight =
            false;
    }
}


function dismissAdminOrdersNewPendingNotice() {
    adminOrdersState.unseenNewPendingCount = 0;

    renderAdminOrdersNewPendingNotice();
}


function setupAdminOrdersNewPendingNotice() {
    if (
        adminOrdersState.pendingNoticeDismissBound
    ) {
        return;
    }

    const dismissButton =
        getOrdersElement(
            "admin-orders-new-pending-notice-dismiss"
        );

    if (!dismissButton) {
        return;
    }

    dismissButton.addEventListener(
        "click",
        dismissAdminOrdersNewPendingNotice
    );

    adminOrdersState.pendingNoticeDismissBound =
        true;
}


function refreshAdminOrdersData() {
    if (
        document.visibilityState !==
        "visible"
    ) {
        return;
    }


    if (
        adminOrdersState.updatingStatus
    ) {
        return;
    }


    void loadOrders(
        {
            silent: true,
        }
    );

    void checkForNewPendingOrders();
}


function handleAdminOrdersVisibilityChange() {
    if (
        document.visibilityState ===
        "visible"
    ) {
        refreshAdminOrdersData();
    }
}


function setupAdminOrdersAutoRefresh() {
    if (
        adminOrdersState.autoRefreshEnabled
    ) {
        return;
    }


    adminOrdersState.autoRefreshEnabled =
        true;


    setupAdminOrdersNewPendingNotice();

    void checkForNewPendingOrders();


    adminOrdersState.autoRefreshTimer =
        window.setInterval(
            refreshAdminOrdersData,
            ADMIN_DATA_REFRESH_INTERVAL_MS
        );


    if (
        adminOrdersState.visibilityBound
    ) {
        return;
    }


    adminOrdersState.visibilityBound =
        true;


    document.addEventListener(
        "visibilitychange",
        handleAdminOrdersVisibilityChange
    );
}


function initializeAdminOrders() {
    setupFilters();
    setupPagination();
    setupOrderDetailModal();
    applyOrderFiltersFromQueryString();

    void loadOrders();

    openOrderFromQueryString();

    setupAdminOrdersAutoRefresh();
}


document.addEventListener(
    "DOMContentLoaded",
    initializeAdminOrders
);