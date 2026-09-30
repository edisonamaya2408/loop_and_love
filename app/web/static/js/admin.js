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

    if (
        !productCount &&
        !categoryCount
    ) {
        return;
    }

    try {
        const [
            productsResponse,
            categoriesResponse,
        ] = await Promise.all(
            [
                adminFetch(
                    "/api/admin/products?page=1&per_page=1"
                ),
                adminFetch(
                    "/api/admin/categories"
                ),
            ]
        );

        const productsData =
            await parseJsonSafely(
                productsResponse
            );

        const categoriesData =
            await parseJsonSafely(
                categoriesResponse
            );

        if (
            !productsResponse.ok
        ) {
            throw new Error(
                getErrorMessage(
                    productsData
                )
            );
        }

        if (
            !categoriesResponse.ok
        ) {
            throw new Error(
                getErrorMessage(
                    categoriesData
                )
            );
        }

        if (productCount) {
            productCount.textContent =
                String(
                    productsData?.pagination?.total ?? 0
                );
        }

        if (categoryCount) {
            categoryCount.textContent =
                String(
                    Array.isArray(
                        categoriesData?.data
                    )
                        ? categoriesData.data.length
                        : 0
                );
        }

    } catch (error) {

        if (productCount) {
            productCount.textContent =
                "—";
        }

        if (categoryCount) {
            categoryCount.textContent =
                "—";
        }
    }
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