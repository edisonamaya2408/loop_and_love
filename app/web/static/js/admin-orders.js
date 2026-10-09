"use strict";


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


    lines.push(
        "",
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


function getStatusLabel(
    status
) {
    const labels = {
        pending: "Pendiente",
        confirmed: "Confirmado",
        cancelled: "Cancelado",
    };

    return (
        labels[status]
        || status
        || "Sin estado"
    );
}


function renderOrderStatusHistory(
    history
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


            content.append(
                transition,
                status,
                date
            );


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

    const total =
        getOrderDetailElement(
            "admin-order-detail-total"
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

    renderOrderStatusHistory(
        order.status_history
    );

    if (total) {
        total.textContent =
            formatCurrency(
                order.total
            );
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


function updateOrderStatusActions(
    status
) {
    const actions =
        getOrderDetailElement(
            "admin-order-status-actions"
        );

    const confirmButton =
        getOrderDetailElement(
            "admin-order-confirm-button"
        );

    const cancelButton =
        getOrderDetailElement(
            "admin-order-cancel-button"
        );

    const isPending =
        status === "pending";

    if (actions) {
        actions.hidden =
            !isPending;
    }

    if (confirmButton) {
        confirmButton.hidden =
            !isPending;
    }

    if (cancelButton) {
        cancelButton.hidden =
            !isPending;
    }

    if (!isPending) {
        setOrderStatusButtonsDisabled(
            false
        );
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

    if (
        !order ||
        order.status !== "pending"
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

        if (
            adminOrdersState.currentOrder?.status ===
            "pending"
        ) {
            setOrderStatusButtonsDisabled(
                false
            );
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


function openOrderDetail(
    orderId
) {
    const modal =
        getOrderDetailElement(
            "admin-order-detail-modal"
        );

    if (!modal) {
        return;
    }


    adminOrdersState.currentOrder =
        null;

    adminOrdersState.updatingStatus =
        false;

    updateOrderStatusActions(
        null
    );


    modal.hidden = false;

    modal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.classList.add(
        "admin-modal-open"
    );


    loadOrderDetail(
        orderId
    );
}


function closeOrderDetail() {
    const modal =
        getOrderDetailElement(
            "admin-order-detail-modal"
        );

    if (!modal) {
        return;
    }

    modal.hidden = true;

    modal.setAttribute(
        "aria-hidden",
        "true"
    );

    document.body.classList.remove(
        "admin-modal-open"
    );

    adminOrdersState.currentOrder =
        null;

    adminOrdersState.updatingStatus =
        false;

    updateOrderStatusActions(
        null
    );
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
                        order.id
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


            const statusCell =
                createCell();


            const status =
                document.createElement(
                    "span"
                );


            status.className =
                "admin-orders-status " +
                `admin-orders-status--${order.status}`;


            status.textContent =
                getStatusLabel(
                    order.status
                );


            statusCell.append(
                status
            );


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

    const whatsappButton =
        getOrderDetailElement(
            "admin-order-whatsapp-button"
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
                updateOrderStatus(
                    "confirmed"
                );
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


    if (backdrop) {

        backdrop.addEventListener(
            "click",
            closeOrderDetail
        );
    }


    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Escape"
            ) {
                closeOrderDetail();
            }

        }
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


    const validStatuses = new Set(
        [
            "pending",
            "confirmed",
            "cancelled",
        ]
    );


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