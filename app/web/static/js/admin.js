"use strict";


const ADMIN_TOKEN_KEY =
    "loop_and_love.admin.access_token";


function getAdminToken() {
    return sessionStorage.getItem(
        ADMIN_TOKEN_KEY
    );
}


function setAdminToken(token) {
    sessionStorage.setItem(
        ADMIN_TOKEN_KEY,
        token
    );
}


function clearAdminToken() {
    sessionStorage.removeItem(
        ADMIN_TOKEN_KEY
    );
}


function redirectToLogin() {
    window.location.href = "/admin/login";
}


function parseJsonSafely(response) {
    return response
        .json()
        .catch(
            () => ({
                success: false,
                error: {
                    message:
                        "La respuesta del servidor no es válida.",
                },
            })
        );
}


function getErrorMessage(data) {
    if (
        data &&
        data.error &&
        typeof data.error.message === "string"
    ) {
        return data.error.message;
    }

    if (
        data &&
        typeof data.message === "string"
    ) {
        return data.message;
    }

    return "No fue posible completar la operación.";
}


async function adminFetch(
    url,
    options = {}
) {
    const token =
        getAdminToken();

    if (!token) {
        redirectToLogin();

        throw new Error(
            "Sesión administrativa no disponible."
        );
    }

    const headers = new Headers(
        options.headers || {}
    );

    headers.set(
        "Authorization",
        `Bearer ${token}`
    );

    const response =
        await fetch(
            url,
            {
                ...options,
                headers,
            }
        );

    if (response.status === 401) {
        clearAdminToken();
        redirectToLogin();

        throw new Error(
            "La sesión ha expirado."
        );
    }

    return response;
}


function setLoginMessage(
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


function setupLoginForm() {
    const form =
        document.getElementById(
            "admin-login-form"
        );

    if (!form) {
        return;
    }

    const emailInput =
        document.getElementById(
            "email"
        );

    const passwordInput =
        document.getElementById(
            "password"
        );

    const message =
        document.getElementById(
            "login-message"
        );

    const button =
        document.getElementById(
            "login-submit"
        );

    const buttonLabel =
        document.getElementById(
            "login-submit-label"
        );

    form.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();

            const email =
                emailInput.value.trim();

            const password =
                passwordInput.value;

            setLoginMessage(
                message,
                ""
            );

            if (!email) {
                setLoginMessage(
                    message,
                    "Ingresa tu correo electrónico."
                );

                emailInput.focus();
                return;
            }

            if (!password) {
                setLoginMessage(
                    message,
                    "Ingresa tu contraseña."
                );

                passwordInput.focus();
                return;
            }

            button.disabled = true;

            buttonLabel.textContent =
                "Ingresando...";

            try {
                const response =
                    await fetch(
                        "/api/auth/login",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                                "Accept":
                                    "application/json",
                            },
                            body: JSON.stringify(
                                {
                                    email,
                                    password,
                                }
                            ),
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

                const token =
                    data?.data?.access_token;

                if (
                    !token ||
                    typeof token !== "string"
                ) {
                    throw new Error(
                        "El servidor no devolvió un token de acceso válido."
                    );
                }

                setAdminToken(
                    token
                );

                window.location.href =
                    "/admin/dashboard";

            } catch (error) {

                setLoginMessage(
                    message,
                    error instanceof Error
                        ? error.message
                        : "No fue posible iniciar sesión."
                );

            } finally {

                button.disabled = false;

                buttonLabel.textContent =
                    "Ingresar";
            }
        }
    );
}


async function logout() {
    const token =
        getAdminToken();

    try {
        if (token) {
            await fetch(
                "/api/auth/logout",
                {
                    method: "POST",
                    headers: {
                        Authorization:
                            `Bearer ${token}`,
                        Accept:
                            "application/json",
                    },
                }
            );
        }
    } catch (error) {
        /*
         * La sesión se elimina localmente incluso si
         * el servidor no responde.
         */
    } finally {
        clearAdminToken();

        redirectToLogin();
    }
}


function setupLogoutButtons() {
    const buttons = [
        document.getElementById(
            "logout-button-sidebar"
        ),
        document.getElementById(
            "logout-button-topbar"
        ),
    ].filter(Boolean);

    buttons.forEach(
        (button) => {

            /*
             * Evita registrar el mismo listener más de una vez
             * sobre el mismo botón si esta función fuera invocada
             * nuevamente desde otro contexto.
             */

            if (
                button.dataset.logoutBound === "true"
            ) {
                return;
            }

            button.dataset.logoutBound =
                "true";

            button.addEventListener(
                "click",
                () => {
                    void logout();
                }
            );
        }
    );
}


function setupMobileMenu() {
    const shell =
        document.getElementById(
            "admin-shell"
        );

    const toggle =
        document.getElementById(
            "admin-menu-toggle"
        );

    const overlay =
        document.getElementById(
            "admin-overlay"
        );

    if (
        !shell ||
        !toggle ||
        !overlay
    ) {
        return;
    }


    /*
     * Esta protección evita que los listeners se dupliquen
     * si setupMobileMenu() se llega a invocar nuevamente.
     */

    if (
        shell.dataset.mobileMenuBound === "true"
    ) {
        return;
    }

    shell.dataset.mobileMenuBound =
        "true";


    const closeMenu = () => {

        shell.classList.remove(
            "admin-shell--menu-open"
        );

        toggle.setAttribute(
            "aria-expanded",
            "false"
        );

        overlay.hidden = true;

        document.body.classList.remove(
            "admin-menu-open"
        );
    };


    const openMenu = () => {

        shell.classList.add(
            "admin-shell--menu-open"
        );

        toggle.setAttribute(
            "aria-expanded",
            "true"
        );

        overlay.hidden = false;

        document.body.classList.add(
            "admin-menu-open"
        );
    };


    /*
     * Estado inicial consistente.
     */

    closeMenu();


    toggle.addEventListener(
        "click",
        () => {

            const isOpen =
                shell.classList.contains(
                    "admin-shell--menu-open"
                );

            if (isOpen) {
                closeMenu();
            } else {
                openMenu();
            }
        }
    );


    overlay.addEventListener(
        "click",
        closeMenu
    );


    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Escape" &&
                shell.classList.contains(
                    "admin-shell--menu-open"
                )
            ) {
                closeMenu();
            }
        }
    );


    window.addEventListener(
        "resize",
        () => {

            if (
                window.innerWidth > 820
            ) {
                closeMenu();
            }
        }
    );


    /*
     * En móvil, al navegar a otra sección mediante un
     * enlace del sidebar, el menú se cierra antes de cambiar
     * de página.
     */

    const navigationLinks =
        shell.querySelectorAll(
            ".admin-nav a"
        );

    navigationLinks.forEach(
        (link) => {

            link.addEventListener(
                "click",
                () => {
                    closeMenu();
                }
            );
        }
    );
}


async function loadDashboardSummary() {
    const productCount =
        document.getElementById(
            "admin-product-count"
        );

    const categoryCount =
        document.getElementById(
            "admin-category-count"
        );

    const orderCount =
        document.getElementById(
            "admin-order-count"
        );

    const pendingOrderCount =
        document.getElementById(
            "admin-pending-order-count"
        );


    if (
        !productCount &&
        !categoryCount &&
        !orderCount &&
        !pendingOrderCount
    ) {
        return;
    }


    const results =
        await Promise.allSettled(
            [
                adminFetch(
                    "/api/admin/products?page=1&per_page=1"
                ),

                adminFetch(
                    "/api/admin/categories"
                ),

                adminFetch(
                    "/api/admin/orders?page=1&per_page=5"
                ),

                adminFetch(
                    "/api/admin/orders?page=1&per_page=1&status=pending"
                ),
            ]
        );


    const readResponse =
        async (
            result
        ) => {

            if (
                result.status ===
                "rejected"
            ) {
                throw (
                    result.reason
                        instanceof Error
                        ? result.reason
                        : new Error(
                            "No fue posible consultar el servidor."
                        )
                );
            }


            const response =
                result.value;


            const data =
                await parseJsonSafely(
                    response
                );


            if (
                !response.ok
            ) {
                throw new Error(
                    getErrorMessage(
                        data
                    )
                );
            }


            return data;
        };


    try {

        const data =
            await readResponse(
                results[0]
            );


        if (productCount) {
            productCount.textContent =
                String(
                    data?.pagination?.total
                    ?? 0
                );
        }

    } catch (error) {

        if (productCount) {
            productCount.textContent =
                "—";
        }
    }


    try {

        const data =
            await readResponse(
                results[1]
            );


        if (categoryCount) {
            categoryCount.textContent =
                String(
                    Array.isArray(
                        data?.data
                    )
                        ? data.data.length
                        : 0
                );
        }

    } catch (error) {

        if (categoryCount) {
            categoryCount.textContent =
                "—";
        }
    }


    try {

        const data =
            await readResponse(
                results[2]
            );


        if (orderCount) {
            orderCount.textContent =
                String(
                    data?.pagination?.total
                    ?? 0
                );
        }

        renderDashboardRecentOrders(
            data?.data
        );

    } catch (error) {

        renderDashboardRecentOrders(
            []
        );
    }


    try {

        const data =
            await readResponse(
                results[3]
            );


        if (pendingOrderCount) {
            pendingOrderCount.textContent =
                String(
                    data?.pagination?.total
                    ?? 0
                );
        }

    } catch (error) {

        if (pendingOrderCount) {
            pendingOrderCount.textContent =
                "—";
        }
    }
}


function renderDashboardRecentOrders(
    orders
) {
    const tableBody =
        document.getElementById(
            "admin-dashboard-orders-body"
        );

    const loading =
        document.getElementById(
            "admin-dashboard-orders-loading"
        );

    const empty =
        document.getElementById(
            "admin-dashboard-orders-empty"
        );


    if (!tableBody) {
        return;
    }


    tableBody.replaceChildren();


    if (loading) {
        loading.hidden = true;
    }


    const normalizedOrders =
        Array.isArray(orders)
            ? orders
            : [];


    if (!normalizedOrders.length) {

        if (empty) {
            empty.hidden = false;
        }

        return;
    }


    if (empty) {
        empty.hidden = true;
    }


    normalizedOrders.forEach(
        (order) => {

            const row =
                document.createElement(
                    "tr"
                );


            const orderCell =
                document.createElement(
                    "td"
                );


            const orderLink =
                document.createElement(
                    "a"
                );


            orderLink.href =
                `/admin/orders?order_id=${encodeURIComponent(
                    order.id
                )}`;


            orderLink.className =
                "admin-dashboard-orders-table__order";


            orderLink.textContent =
                `#${order.id}`;


            orderCell.append(
                orderLink
            );


            const customerCell =
                document.createElement(
                    "td"
                );


            const customerName =
                document.createElement(
                    "strong"
                );


            customerName.textContent =
                order.name ||
                "Sin nombre";


            const customerPhone =
                document.createElement(
                    "small"
                );


            customerPhone.textContent =
                order.phone ||
                "Sin teléfono";


            customerCell.append(
                customerName,
                customerPhone
            );


            const totalCell =
                document.createElement(
                    "td"
                );


            totalCell.textContent =
                formatDashboardCurrency(
                    order.total
                );

            const statusCell =
                document.createElement(
                    "td"
                );


            const status =
                document.createElement(
                    "span"
                );


            status.className =
                "admin-dashboard-order-status " +
                `admin-dashboard-order-status--${order.status}`;


            status.textContent =
                getDashboardOrderStatusLabel(
                    order.status
                );


            statusCell.append(
                status
            );


            const dateCell =
                document.createElement(
                    "td"
                );


            dateCell.textContent =
                formatDashboardOrderDate(
                    order.created_at
                );


            row.append(
                orderCell,
                customerCell,
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


function formatDashboardCurrency(
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


function getDashboardOrderStatusLabel(
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


function formatDashboardOrderDate(
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


function setupAdminDashboard() {
    const dashboard =
        document.getElementById(
            "admin-product-count"
        );

    if (!dashboard) {
        return;
    }

    if (!getAdminToken()) {
        redirectToLogin();
        return;
    }

    void loadDashboardSummary();
}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupLoginForm();

        setupAdminDashboard();


        /*
         * Las funciones globales de logout y menú se ejecutan
         * una sola vez por página.
         */

        if (
            document.getElementById(
                "admin-shell"
            )
        ) {
            setupLogoutButtons();
            setupMobileMenu();
        }
    }
);