"use strict";


const categoryState = {
    categories: [],
    editingCategoryId: null,
};


function getCategoryElement(
    id
) {
    return document.getElementById(
        id
    );
}


function setCategoryMessage(
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


function setCategoryButtonLoading(
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


function formatCategoryDate(
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


function renderCategories(
    categories
) {
    const tableBody =
        getCategoryElement(
            "admin-categories-table-body"
        );

    const emptyState =
        getCategoryElement(
            "admin-categories-empty"
        );

    const loading =
        getCategoryElement(
            "admin-categories-loading"
        );

    const count =
        getCategoryElement(
            "admin-categories-count"
        );

    if (!tableBody) {
        return;
    }

    tableBody.replaceChildren();


    if (count) {
        count.textContent =
            String(
                categories.length
            );
    }


    if (loading) {
        loading.hidden =
            true;
    }


    if (!categories.length) {

        if (emptyState) {
            emptyState.hidden =
                false;
        }

        return;
    }


    if (emptyState) {
        emptyState.hidden =
            true;
    }


    categories.forEach(
        (category) => {

            const row =
                document.createElement(
                    "tr"
                );


            const nameCell =
                document.createElement(
                    "td"
                );

            const nameWrapper =
                document.createElement(
                    "div"
                );

            nameWrapper.className =
                "admin-categories-name";


            const name =
                document.createElement(
                    "strong"
                );

            name.textContent =
                category.name ||
                "Sin nombre";


            const identifier =
                document.createElement(
                    "small"
                );

            identifier.textContent =
                `ID #${category.id}`;


            nameWrapper.append(
                name,
                identifier
            );

            nameCell.append(
                nameWrapper
            );


            const slugCell =
                document.createElement(
                    "td"
                );

            const slug =
                document.createElement(
                    "span"
                );

            slug.className =
                "admin-categories-slug";

            slug.textContent =
                category.slug ||
                "—";

            slugCell.append(
                slug
            );


            const statusCell =
                document.createElement(
                    "td"
                );

            const status =
                document.createElement(
                    "span"
                );

            const isActive =
                category.is_active === true;

            status.className =
                "admin-categories-status " +
                (
                    isActive
                        ? "admin-categories-status--active"
                        : "admin-categories-status--inactive"
                );

            status.textContent =
                isActive
                    ? "Activa"
                    : "Inactiva";

            statusCell.append(
                status
            );


            const createdCell =
                document.createElement(
                    "td"
                );

            const created =
                document.createElement(
                    "span"
                );

            created.className =
                "admin-categories-date";

            created.textContent =
                formatCategoryDate(
                    category.created_at
                );

            createdCell.append(
                created
            );


            const actionsCell =
                document.createElement(
                    "td"
                );

            const actions =
                document.createElement(
                    "div"
                );

            actions.className =
                "admin-categories-actions";


            const editButton =
                document.createElement(
                    "button"
                );

            editButton.type =
                "button";

            editButton.className =
                "admin-categories-action";

            editButton.textContent =
                "Editar";

            editButton.setAttribute(
                "aria-label",
                `Editar ${category.name}`
            );

            editButton.addEventListener(
                "click",
                () => {
                    openCategoryEditModal(
                        category
                    );
                }
            );


            const deleteButton =
                document.createElement(
                    "button"
                );

            deleteButton.type =
                "button";

            deleteButton.className =
                "admin-categories-action admin-categories-action--danger";

            deleteButton.textContent =
                "Eliminar";

            deleteButton.setAttribute(
                "aria-label",
                `Eliminar ${category.name}`
            );

            deleteButton.addEventListener(
                "click",
                () => {
                    void deleteCategory(
                        category
                    );
                }
            );


            actions.append(
                editButton,
                deleteButton
            );

            actionsCell.append(
                actions
            );


            row.append(
                nameCell,
                slugCell,
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


async function loadCategories() {
    const loading =
        getCategoryElement(
            "admin-categories-loading"
        );

    const message =
        getCategoryElement(
            "admin-category-list-message"
        );


    if (loading) {
        loading.hidden =
            false;
    }


    setCategoryMessage(
        message,
        ""
    );


    try {
        const response =
            await adminFetch(
                "/api/admin/categories"
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


        const categories =
            Array.isArray(
                data?.data
            )
                ? data.data
                : [];


        categoryState.categories =
            categories;


        renderCategories(
            categories
        );

    } catch (error) {

        if (
            error instanceof Error &&
            error.message ===
            "La sesión ha expirado."
        ) {
            return;
        }


        setCategoryMessage(
            message,
            error instanceof Error
                ? error.message
                : "No fue posible cargar las categorías."
        );


        if (loading) {
            loading.hidden =
                true;
        }
    }
}


function resetCategoryCreateForm() {
    const form =
        getCategoryElement(
            "admin-category-create-form"
        );

    if (form) {
        form.reset();
    }


    setCategoryMessage(
        getCategoryElement(
            "admin-category-create-message"
        ),
        ""
    );
}


function setupCategoryCreateForm() {
    const form =
        getCategoryElement(
            "admin-category-create-form"
        );

    if (!form) {
        return;
    }


    const name =
        getCategoryElement(
            "new-category-name"
        );

    const message =
        getCategoryElement(
            "admin-category-create-message"
        );

    const button =
        getCategoryElement(
            "admin-category-create-submit"
        );

    const label =
        getCategoryElement(
            "admin-category-create-submit-label"
        );


    form.addEventListener(
        "submit",
        async (
            event
        ) => {

            event.preventDefault();


            setCategoryMessage(
                message,
                ""
            );


            const nameValue =
                name.value.trim();


            if (!nameValue) {

                setCategoryMessage(
                    message,
                    "Ingresa el nombre de la categoría."
                );

                name.focus();

                return;
            }


            if (
                nameValue.length > 100
            ) {

                setCategoryMessage(
                    message,
                    "El nombre no puede superar los 100 caracteres."
                );

                name.focus();

                return;
            }


            setCategoryButtonLoading(
                button,
                label,
                true,
                "Creando...",
                "Crear categoría"
            );


            try {

                const response =
                    await adminFetch(
                        "/api/admin/categories",
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
                                        name:
                                            nameValue,
                                        is_active:
                                            true,
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


                resetCategoryCreateForm();

                await loadCategories();

            } catch (error) {

                setCategoryMessage(
                    message,
                    error instanceof Error
                        ? error.message
                        : "No fue posible crear la categoría."
                );

            } finally {

                setCategoryButtonLoading(
                    button,
                    label,
                    false,
                    "Creando...",
                    "Crear categoría"
                );
            }
        }
    );
}


function openCategoryEditModal(
    category
) {
    const modal =
        getCategoryElement(
            "admin-categories-modal"
        );

    const id =
        getCategoryElement(
            "edit-category-id"
        );

    const name =
        getCategoryElement(
            "edit-category-name"
        );

    const slug =
        getCategoryElement(
            "edit-category-slug"
        );

    const status =
        getCategoryElement(
            "edit-category-status"
        );

    const message =
        getCategoryElement(
            "admin-category-edit-message"
        );


    if (
        !modal ||
        !id ||
        !name ||
        !slug ||
        !status
    ) {
        return;
    }


    categoryState.editingCategoryId =
        category.id;


    id.value =
        String(
            category.id
        );

    name.value =
        category.name ||
        "";

    slug.value =
        category.slug ||
        "";

    status.value =
        category.is_active === true
            ? "true"
            : "false";


    setCategoryMessage(
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


    name.focus();
}


function closeCategoryEditModal() {
    const modal =
        getCategoryElement(
            "admin-categories-modal"
        );

    const form =
        getCategoryElement(
            "admin-category-edit-form"
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


    categoryState.editingCategoryId =
        null;


    if (form) {
        form.reset();
    }


    setCategoryMessage(
        getCategoryElement(
            "admin-category-edit-message"
        ),
        ""
    );
}


function setupCategoryEditModal() {
    const modal =
        getCategoryElement(
            "admin-categories-modal"
        );

    if (!modal) {
        return;
    }


    const closeButton =
        getCategoryElement(
            "admin-category-modal-close"
        );

    const cancelButton =
        getCategoryElement(
            "admin-category-edit-cancel"
        );


    closeButton?.addEventListener(
        "click",
        closeCategoryEditModal
    );


    cancelButton?.addEventListener(
        "click",
        closeCategoryEditModal
    );


    modal.querySelectorAll(
        "[data-category-modal-close]"
    ).forEach(
        (element) => {

            element.addEventListener(
                "click",
                closeCategoryEditModal
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
                closeCategoryEditModal();
            }

        }
    );


    const form =
        getCategoryElement(
            "admin-category-edit-form"
        );

    if (!form) {
        return;
    }


    const name =
        getCategoryElement(
            "edit-category-name"
        );

    const id =
        getCategoryElement(
            "edit-category-id"
        );

    const status =
        getCategoryElement(
            "edit-category-status"
        );

    const message =
        getCategoryElement(
            "admin-category-edit-message"
        );

    const button =
        getCategoryElement(
            "admin-category-edit-submit"
        );

    const label =
        getCategoryElement(
            "admin-category-edit-submit-label"
        );


    form.addEventListener(
        "submit",
        async (
            event
        ) => {

            event.preventDefault();


            setCategoryMessage(
                message,
                ""
            );


            const categoryId =
                Number(
                    id.value
                );


            if (
                !Number.isInteger(
                    categoryId
                ) ||
                categoryId <= 0
            ) {

                setCategoryMessage(
                    message,
                    "No se identificó correctamente la categoría."
                );

                return;
            }


            const nameValue =
                name.value.trim();


            if (!nameValue) {

                setCategoryMessage(
                    message,
                    "Ingresa el nombre de la categoría."
                );

                name.focus();

                return;
            }


            if (
                nameValue.length > 100
            ) {

                setCategoryMessage(
                    message,
                    "El nombre no puede superar los 100 caracteres."
                );

                name.focus();

                return;
            }


            setCategoryButtonLoading(
                button,
                label,
                true,
                "Guardando...",
                "Guardar cambios"
            );


            try {

                const response =
                    await adminFetch(
                        `/api/admin/categories/${categoryId}`,
                        {
                            method: "PUT",
                            headers: {
                                "Content-Type":
                                    "application/json",
                                "Accept":
                                    "application/json",
                            },
                            body:
                                JSON.stringify(
                                    {
                                        name:
                                            nameValue,
                                        is_active:
                                            status.value === "true",
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


                closeCategoryEditModal();

                await loadCategories();

            } catch (error) {

                setCategoryMessage(
                    message,
                    error instanceof Error
                        ? error.message
                        : "No fue posible actualizar la categoría."
                );

            } finally {

                setCategoryButtonLoading(
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


async function deleteCategory(
    category
) {
    if (
        !category ||
        !category.id
    ) {
        return;
    }


    const confirmed =
        window.confirm(
            `¿Deseas eliminar la categoría "${category.name}"?\n\nLa eliminación solo será posible si no tiene productos asociados.`
        );


    if (!confirmed) {
        return;
    }


    const message =
        getCategoryElement(
            "admin-category-list-message"
        );


    setCategoryMessage(
        message,
        ""
    );


    try {

        const response =
            await adminFetch(
                `/api/admin/categories/${category.id}`,
                {
                    method: "DELETE",
                    headers: {
                        Accept:
                            "application/json",
                    },
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


        await loadCategories();

    } catch (error) {

        setCategoryMessage(
            message,
            error instanceof Error
                ? error.message
                : "No fue posible eliminar la categoría."
        );
    }
}


function setupCategoriesPage() {
    if (
        !getCategoryElement(
            "admin-categories-table-body"
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


    setupCategoryCreateForm();

    setupCategoryEditModal();

    void loadCategories();
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        setupCategoriesPage();
    }
);