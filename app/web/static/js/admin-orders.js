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


async function loadOrders() {
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

    } catch (error) {

        if (
            error instanceof Error &&
            error.message ===
            "La sesión ha expirado."
        ) {
            return;
        }


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


function initializeAdminOrders() {
    setupFilters();
    setupPagination();
    setupOrderDetailModal();
    loadOrders();
}


document.addEventListener(
    "DOMContentLoaded",
    initializeAdminOrders
);