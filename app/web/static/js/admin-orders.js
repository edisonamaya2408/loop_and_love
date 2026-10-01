"use strict";


const adminOrdersState = {
    page: 1,
    perPage: 12,
    total: 0,
    pages: 0,
    search: "",
    status: "",
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