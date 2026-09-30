"use strict";


const USERS_TABLE_BODY =
    "admin-users-table-body";


const usersState = {
    users: [],
    editingUserId: null,
};


function getUsersElement(
    id
) {
    return document.getElementById(
        id
    );
}


function setUsersMessage(
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


function setButtonLoading(
    button,
    labelElement,
    loading,
    loadingLabel,
    defaultLabel
) {
    if (!button) {
        return;
    }

    button.disabled = loading;

    if (labelElement) {
        labelElement.textContent =
            loading
                ? loadingLabel
                : defaultLabel;
    }
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


function createCell() {
    return document.createElement(
        "td"
    );
}


function renderUsers(
    users
) {
    const tableBody =
        getUsersElement(
            USERS_TABLE_BODY
        );

    const emptyState =
        getUsersElement(
            "admin-users-empty"
        );

    const loading =
        getUsersElement(
            "admin-users-loading"
        );

    const count =
        getUsersElement(
            "admin-users-count"
        );

    if (!tableBody) {
        return;
    }

    tableBody.replaceChildren();

    if (count) {
        count.textContent = String(
            users.length
        );
    }

    if (loading) {
        loading.hidden = true;
    }

    if (!users.length) {
        if (emptyState) {
            emptyState.hidden = false;
        }

        return;
    }

    if (emptyState) {
        emptyState.hidden = true;
    }

    users.forEach(
        (user) => {
            const row =
                document.createElement(
                    "tr"
                );

            const userCell =
                createCell();

            const userWrapper =
                document.createElement(
                    "div"
                );

            userWrapper.className =
                "admin-users-user";

            const email =
                document.createElement(
                    "strong"
                );

            email.className =
                "admin-users-user__email";

            email.textContent =
                user.email ||
                "Sin correo";

            const identifier =
                document.createElement(
                    "span"
                );

            identifier.className =
                "admin-users-user__id";

            identifier.textContent =
                `ID #${user.id}`;

            userWrapper.append(
                email,
                identifier
            );

            userCell.append(
                userWrapper
            );


            const statusCell =
                createCell();

            const status =
                document.createElement(
                    "span"
                );

            const isActive =
                user.is_active === true;

            status.className =
                "admin-users-status " +
                (
                    isActive
                        ? "admin-users-status--active"
                        : "admin-users-status--inactive"
                );

            status.textContent =
                isActive
                    ? "Activo"
                    : "Inactivo";

            statusCell.append(
                status
            );


            const createdCell =
                createCell();

            const created =
                document.createElement(
                    "span"
                );

            created.className =
                "admin-users-date";

            created.textContent =
                formatDate(
                    user.created_at
                );

            createdCell.append(
                created
            );


            const actionsCell =
                createCell();

            const actions =
                document.createElement(
                    "div"
                );

            actions.className =
                "admin-users-actions";

            const editButton =
                document.createElement(
                    "button"
                );

            editButton.type =
                "button";

            editButton.className =
                "admin-users-action";

            editButton.textContent =
                "Editar";

            editButton.setAttribute(
                "aria-label",
                `Editar ${user.email}`
            );

            editButton.addEventListener(
                "click",
                () => {
                    openEditModal(
                        user
                    );
                }
            );

            actions.append(
                editButton
            );

            actionsCell.append(
                actions
            );


            row.append(
                userCell,
                statusCell,
                createdCell,
                actionsCell
            );

            tableBody.append(
                row
            );
        }
    );
}


async function loadUsers() {
    const loading =
        getUsersElement(
            "admin-users-loading"
        );

    const message =
        getUsersElement(
            "admin-users-list-message"
        );

    if (loading) {
        loading.hidden = false;
    }

    setUsersMessage(
        message,
        ""
    );

    try {
        const response =
            await adminFetch(
                "/api/admin/users"
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

        const users =
            Array.isArray(
                data?.data
            )
                ? data.data
                : [];

        usersState.users =
            users;

        renderUsers(
            users
        );

    } catch (error) {

        if (
            error instanceof Error &&
            error.message ===
                "La sesión ha expirado."
        ) {
            return;
        }

        setUsersMessage(
            message,
            error instanceof Error
                ? error.message
                : "No fue posible cargar los usuarios."
        );

        if (loading) {
            loading.hidden = true;
        }
    }
}


function resetCreateForm() {
    const form =
        getUsersElement(
            "admin-user-create-form"
        );

    if (form) {
        form.reset();
    }

    setUsersMessage(
        getUsersElement(
            "admin-user-create-message"
        ),
        ""
    );
}


function setupCreateForm() {
    const form =
        getUsersElement(
            "admin-user-create-form"
        );

    if (!form) {
        return;
    }

    const email =
        getUsersElement(
            "new-user-email"
        );

    const password =
        getUsersElement(
            "new-user-password"
        );

    const confirmation =
        getUsersElement(
            "new-user-password-confirmation"
        );

    const message =
        getUsersElement(
            "admin-user-create-message"
        );

    const button =
        getUsersElement(
            "admin-user-create-submit"
        );

    const label =
        getUsersElement(
            "admin-user-create-submit-label"
        );


    form.addEventListener(
        "submit",
        async (
            event
        ) => {

            event.preventDefault();

            setUsersMessage(
                message,
                ""
            );

            const emailValue =
                email.value.trim();

            const passwordValue =
                password.value;

            const confirmationValue =
                confirmation.value;

            if (!emailValue) {
                setUsersMessage(
                    message,
                    "Ingresa el correo electrónico."
                );

                email.focus();

                return;
            }

            if (!passwordValue) {
                setUsersMessage(
                    message,
                    "Ingresa una contraseña."
                );

                password.focus();

                return;
            }

            if (passwordValue.length < 8) {
                setUsersMessage(
                    message,
                    "La contraseña debe tener al menos 8 caracteres."
                );

                password.focus();

                return;
            }

            if (
                passwordValue !==
                confirmationValue
            ) {
                setUsersMessage(
                    message,
                    "Las contraseñas no coinciden."
                );

                confirmation.focus();

                return;
            }


            setButtonLoading(
                button,
                label,
                true,
                "Creando...",
                "Crear administrador"
            );


            try {
                const response =
                    await adminFetch(
                        "/api/admin/users",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                                "Accept":
                                    "application/json",
                            },
                            body:
                                JSON.stringify(
                                    {
                                        email:
                                            emailValue,
                                        password:
                                            passwordValue,
                                        password_confirmation:
                                            confirmationValue,
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

                resetCreateForm();

                await loadUsers();

            } catch (error) {

                setUsersMessage(
                    message,
                    error instanceof Error
                        ? error.message
                        : "No fue posible crear el administrador."
                );

            } finally {

                setButtonLoading(
                    button,
                    label,
                    false,
                    "Creando...",
                    "Crear administrador"
                );
            }
        }
    );
}


function openEditModal(
    user
) {
    const modal =
        getUsersElement(
            "admin-users-modal"
        );

    const id =
        getUsersElement(
            "edit-user-id"
        );

    const email =
        getUsersElement(
            "edit-user-email"
        );

    const status =
        getUsersElement(
            "edit-user-status"
        );

    const password =
        getUsersElement(
            "edit-user-password"
        );

    const confirmation =
        getUsersElement(
            "edit-user-password-confirmation"
        );

    const message =
        getUsersElement(
            "admin-user-edit-message"
        );


    if (
        !modal ||
        !id ||
        !email ||
        !status ||
        !password ||
        !confirmation
    ) {
        return;
    }


    usersState.editingUserId =
        user.id;


    id.value =
        String(user.id);

    email.value =
        user.email || "";

    status.value =
        user.is_active === true
            ? "true"
            : "false";

    password.value =
        "";

    confirmation.value =
        "";


    setUsersMessage(
        message,
        ""
    );


    modal.hidden =
        false;

    modal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.style.overflow =
        "hidden";

    email.focus();
}


function closeEditModal() {
    const modal =
        getUsersElement(
            "admin-users-modal"
        );

    const form =
        getUsersElement(
            "admin-user-edit-form"
        );

    if (!modal) {
        return;
    }

    modal.hidden =
        true;

    modal.setAttribute(
        "aria-hidden",
        "true"
    );

    document.body.style.overflow =
        "";

    usersState.editingUserId =
        null;

    if (form) {
        form.reset();
    }

    setUsersMessage(
        getUsersElement(
            "admin-user-edit-message"
        ),
        ""
    );
}


function setupEditModal() {
    const modal =
        getUsersElement(
            "admin-users-modal"
        );

    if (!modal) {
        return;
    }


    const closeButton =
        getUsersElement(
            "admin-user-modal-close"
        );

    const cancelButton =
        getUsersElement(
            "admin-user-edit-cancel"
        );


    closeButton?.addEventListener(
        "click",
        closeEditModal
    );

    cancelButton?.addEventListener(
        "click",
        closeEditModal
    );


    modal.querySelectorAll(
        "[data-user-modal-close]"
    ).forEach(
        (element) => {
            element.addEventListener(
                "click",
                closeEditModal
            );
        }
    );


    document.addEventListener(
        "keydown",
        (event) => {
            if (
                event.key === "Escape" &&
                !modal.hidden
            ) {
                closeEditModal();
            }
        }
    );


    const form =
        getUsersElement(
            "admin-user-edit-form"
        );

    if (!form) {
        return;
    }


    const email =
        getUsersElement(
            "edit-user-email"
        );

    const status =
        getUsersElement(
            "edit-user-status"
        );

    const password =
        getUsersElement(
            "edit-user-password"
        );

    const confirmation =
        getUsersElement(
            "edit-user-password-confirmation"
        );

    const message =
        getUsersElement(
            "admin-user-edit-message"
        );

    const button =
        getUsersElement(
            "admin-user-edit-submit"
        );

    const label =
        getUsersElement(
            "admin-user-edit-submit-label"
        );


    form.addEventListener(
        "submit",
        async (
            event
        ) => {

            event.preventDefault();

            setUsersMessage(
                message,
                ""
            );


            const userId =
                usersState.editingUserId;

            if (!userId) {
                setUsersMessage(
                    message,
                    "No se identificó el administrador."
                );

                return;
            }


            const emailValue =
                email.value.trim();

            const passwordValue =
                password.value;

            const confirmationValue =
                confirmation.value;

            const isActive =
                status.value === "true";


            if (!emailValue) {
                setUsersMessage(
                    message,
                    "Ingresa el correo electrónico."
                );

                email.focus();

                return;
            }


            if (
                passwordValue &&
                passwordValue.length < 8
            ) {
                setUsersMessage(
                    message,
                    "La nueva contraseña debe tener al menos 8 caracteres."
                );

                password.focus();

                return;
            }


            if (
                passwordValue !==
                    confirmationValue
                &&
                (
                    passwordValue ||
                    confirmationValue
                )
            ) {
                setUsersMessage(
                    message,
                    "Las contraseñas no coinciden."
                );

                confirmation.focus();

                return;
            }


            const changes = {
                email:
                    emailValue,
                is_active:
                    isActive,
            };


            if (passwordValue) {
                changes.password =
                    passwordValue;

                changes.password_confirmation =
                    confirmationValue;
            }


            setButtonLoading(
                button,
                label,
                true,
                "Guardando...",
                "Guardar cambios"
            );


            try {
                const response =
                    await adminFetch(
                        `/api/admin/users/${userId}`,
                        {
                            method: "PATCH",
                            headers: {
                                "Content-Type":
                                    "application/json",
                                "Accept":
                                    "application/json",
                            },
                            body:
                                JSON.stringify(
                                    changes
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


                closeEditModal();

                await loadUsers();

            } catch (error) {

                setUsersMessage(
                    message,
                    error instanceof Error
                        ? error.message
                        : "No fue posible actualizar el administrador."
                );

            } finally {

                setButtonLoading(
                    button,
                    label,
                    false,
                    "Guardando...",
                    "Guardar cambios"
                );
            }
        }
    );
}


function setupUsersPage() {
    if (
        !getUsersElement(
            "admin-users-table-body"
        )
    ) {
        return;
    }


    if (
        typeof getAdminToken !==
        "function"
    ) {
        redirectToLogin();

        return;
    }


    if (!getAdminToken()) {
        redirectToLogin();

        return;
    }


    setupCreateForm();
    setupEditModal();

    void loadUsers();
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        setupUsersPage();
    }
);