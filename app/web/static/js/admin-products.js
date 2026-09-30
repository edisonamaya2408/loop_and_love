"use strict";


const productState = {
    categories: [],
    products: [],
    pagination: {
        page: 1,
        perPage: 12,
        total: 0,
        pages: 1,
        hasNext: false,
        hasPrevious: false,
    },
    editingProductId: null,
    deletingProductId: null,
};


function getProductElement(
    id
) {
    return document.getElementById(
        id
    );
}


function setProductMessage(
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


function setProductButtonLoading(
    button,
    labelElement,
    loading,
    loadingLabel,
    defaultLabel
) {
    if (!button) {
        return;
    }

    button.disabled =
        loading;

    if (labelElement) {
        labelElement.textContent =
            loading
                ? loadingLabel
                : defaultLabel;
    }
}


function formatProductPrice(
    value
) {
    const numericValue =
        Number(value);

    if (
        Number.isNaN(
            numericValue
        )
    ) {
        return "—";
    }

    return new Intl.NumberFormat(
        "es-CO",
        {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }
    ).format(
        numericValue
    );
}


function formatProductDate(
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


function resetProductPagination() {
    productState.pagination.page =
        1;
}


function getProductFilters() {
    return {
        search:
            getProductElement(
                "product-search"
            )?.value.trim() || "",

        category_id:
            getProductElement(
                "product-category-filter"
            )?.value || "",

        is_active:
            getProductElement(
                "product-status-filter"
            )?.value || "",

        min_price:
            getProductElement(
                "product-min-price"
            )?.value || "",

        max_price:
            getProductElement(
                "product-max-price"
            )?.value || "",
    };
}


function buildProductListUrl() {
    const filters =
        getProductFilters();

    const params =
        new URLSearchParams();

    params.set(
        "page",
        String(
            productState.pagination.page
        )
    );

    params.set(
        "per_page",
        String(
            productState.pagination.perPage
        )
    );

    Object.entries(
        filters
    ).forEach(
        ([key, value]) => {

            if (value !== "") {
                params.set(
                    key,
                    value
                );
            }

        }
    );

    return (
        "/api/admin/products?" +
        params.toString()
    );
}


async function loadCategories() {
    const message =
        getProductElement(
            "admin-product-list-message"
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

        productState.categories =
            categories;

        populateCategorySelects();

    } catch (error) {

        if (
            error instanceof Error &&
            error.message ===
            "La sesión ha expirado."
        ) {
            return;
        }

        setProductMessage(
            message,
            error instanceof Error
                ? error.message
                : "No fue posible cargar las categorías."
        );
    }
}


function populateCategorySelects() {
    const filterSelect =
        getProductElement(
            "product-category-filter"
        );

    const formSelect =
        getProductElement(
            "admin-product-category"
        );


    if (filterSelect) {

        const currentValue =
            filterSelect.value;

        filterSelect.replaceChildren();


        const allOption =
            document.createElement(
                "option"
            );

        allOption.value =
            "";

        allOption.textContent =
            "Todas las categorías";

        filterSelect.append(
            allOption
        );


        productState.categories.forEach(
            (category) => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    String(
                        category.id
                    );

                option.textContent =
                    category.name +
                    (
                        category.is_active
                            ? ""
                            : " — Inactiva"
                    );

                filterSelect.append(
                    option
                );
            }
        );


        filterSelect.value =
            currentValue;
    }


    if (formSelect) {

        const currentValue =
            formSelect.value;

        formSelect.replaceChildren();


        const placeholder =
            document.createElement(
                "option"
            );

        placeholder.value =
            "";

        placeholder.textContent =
            "Selecciona una categoría";

        formSelect.append(
            placeholder
        );


        productState.categories.forEach(
            (category) => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    String(
                        category.id
                    );

                option.textContent =
                    category.name;


                if (
                    category.is_active !== true
                ) {
                    option.disabled =
                        true;

                    option.textContent +=
                        " — Inactiva";
                }


                formSelect.append(
                    option
                );
            }
        );


        formSelect.value =
            currentValue;
    }
}


function renderProducts(
    products
) {
    const tableBody =
        getProductElement(
            "admin-products-table-body"
        );

    const loading =
        getProductElement(
            "admin-products-loading"
        );

    const empty =
        getProductElement(
            "admin-products-empty"
        );

    const count =
        getProductElement(
            "admin-products-count"
        );


    if (!tableBody) {
        return;
    }


    tableBody.replaceChildren();


    if (loading) {
        loading.hidden =
            true;
    }


    if (count) {
        count.textContent =
            String(
                productState.pagination.total
            );
    }


    if (!products.length) {

        if (empty) {
            empty.hidden =
                false;
        }

        return;
    }


    if (empty) {
        empty.hidden =
            true;
    }


    products.forEach(
        (product) => {

            const row =
                document.createElement(
                    "tr"
                );


            const productCell =
                document.createElement(
                    "td"
                );


            const productWrapper =
                document.createElement(
                    "div"
                );

            productWrapper.className =
                "admin-products-product";


            const imageWrapper =
                document.createElement(
                    "div"
                );

            imageWrapper.className =
                "admin-products-product__image";


            if (
                product.image_url
            ) {

                const image =
                    document.createElement(
                        "img"
                    );

                image.src =
                    product.image_url;

                image.alt =
                    product.name ||
                    "Producto";

                image.loading =
                    "lazy";

                imageWrapper.append(
                    image
                );

            } else {

                const placeholder =
                    document.createElement(
                        "span"
                    );

                placeholder.className =
                    "admin-products-product__placeholder";

                placeholder.textContent =
                    "◇";

                placeholder.setAttribute(
                    "aria-hidden",
                    "true"
                );

                imageWrapper.append(
                    placeholder
                );
            }


            const productContent =
                document.createElement(
                    "div"
                );

            productContent.className =
                "admin-products-product__content";


            const productName =
                document.createElement(
                    "strong"
                );

            productName.className =
                "admin-products-product__name";

            productName.textContent =
                product.name ||
                "Sin nombre";


            const productCode =
                document.createElement(
                    "span"
                );

            productCode.className =
                "admin-products-product__code";

            productCode.textContent =
                product.code ||
                "Sin código";


            productContent.append(
                productName,
                productCode
            );


            productWrapper.append(
                imageWrapper,
                productContent
            );


            productCell.append(
                productWrapper
            );


            const categoryCell =
                document.createElement(
                    "td"
                );

            const category =
                document.createElement(
                    "span"
                );

            category.className =
                "admin-products-category";

            category.textContent =
                product.category?.name ||
                "Sin categoría";

            categoryCell.append(
                category
            );


            const priceCell =
                document.createElement(
                    "td"
                );

            const price =
                document.createElement(
                    "span"
                );

            price.className =
                "admin-products-price";

            price.textContent =
                formatProductPrice(
                    product.price
                );

            priceCell.append(
                price
            );


            const statusCell =
                document.createElement(
                    "td"
                );

            const status =
                document.createElement(
                    "span"
                );

            const active =
                product.is_active === true;

            status.className =
                "admin-products-status " +
                (
                    active
                        ? "admin-products-status--active"
                        : "admin-products-status--inactive"
                );

            status.textContent =
                active
                    ? "Activo"
                    : "Inactivo";

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
                "admin-products-date";

            created.textContent =
                formatProductDate(
                    product.created_at
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
                "admin-products-actions";


            const editButton =
                document.createElement(
                    "button"
                );

            editButton.type =
                "button";

            editButton.className =
                "admin-products-action";

            editButton.textContent =
                "Editar";

            editButton.addEventListener(
                "click",
                () => {
                    void openProductEdit(
                        product.id
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
                "admin-products-action admin-products-action--danger";

            deleteButton.textContent =
                "Eliminar";

            deleteButton.addEventListener(
                "click",
                () => {
                    openDeleteConfirmation(
                        product
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
                productCell,
                categoryCell,
                priceCell,
                statusCell,
                createdCell,
                actionsCell
            );


            tableBody.append(
                row
            );
        }
    );


    updateProductPagination();
}


function updateProductPagination() {
    const previous =
        getProductElement(
            "admin-product-previous"
        );

    const next =
        getProductElement(
            "admin-product-next"
        );

    const indicator =
        getProductElement(
            "admin-product-page-indicator"
        );


    if (previous) {
        previous.disabled =
            !productState.pagination.hasPrevious;
    }


    if (next) {
        next.disabled =
            !productState.pagination.hasNext;
    }


    if (indicator) {
        indicator.textContent =
            `Página ${productState.pagination.page} de ${productState.pagination.pages}`;
    }
}


async function loadProducts() {
    const tableBody =
        getProductElement(
            "admin-products-table-body"
        );

    const loading =
        getProductElement(
            "admin-products-loading"
        );

    const empty =
        getProductElement(
            "admin-products-empty"
        );

    const message =
        getProductElement(
            "admin-product-list-message"
        );


    if (!tableBody) {
        return;
    }


    if (loading) {
        loading.hidden =
            false;
    }


    if (empty) {
        empty.hidden =
            true;
    }


    setProductMessage(
        message,
        ""
    );


    try {

        const response =
            await adminFetch(
                buildProductListUrl()
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


        const products =
            Array.isArray(
                data?.data
            )
                ? data.data
                : [];


        const pagination =
            data?.pagination || {};


        productState.products =
            products;


        productState.pagination = {
            page:
                Number(
                    pagination.page
                ) || 1,

            perPage:
                Number(
                    pagination.per_page
                ) ||
                productState.pagination.perPage,

            total:
                Number(
                    pagination.total
                ) || 0,

            pages:
                Number(
                    pagination.pages
                ) || 1,

            hasNext:
                pagination.has_next === true,

            hasPrevious:
                pagination.has_previous === true,
        };


        renderProducts(
            products
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
            loading.hidden =
                true;
        }


        setProductMessage(
            message,
            error instanceof Error
                ? error.message
                : "No fue posible cargar los productos."
        );
    }
}


function resetProductForm() {
    const form =
        getProductElement(
            "admin-product-form"
        );

    if (form) {
        form.reset();
    }


    const id =
        getProductElement(
            "admin-product-id"
        );

    if (id) {
        id.value =
            "";
    }


    const status =
        getProductElement(
            "admin-product-status"
        );

    if (status) {
        status.value =
            "true";
    }


    setProductMessage(
        getProductElement(
            "admin-product-form-message"
        ),
        ""
    );


    resetProductImagePreview();
}


function resetProductImagePreview() {
    const box =
        getProductElement(
            "admin-product-image-box"
        );

    const preview =
        getProductElement(
            "admin-product-image-preview"
        );

    const imageInput =
        getProductElement(
            "admin-product-image"
        );

    const imageStatus =
        getProductElement(
            "admin-product-image-status"
        );

    const removeButton =
        getProductElement(
            "admin-product-remove-image"
        );


    if (box) {
        box.hidden =
            true;
    }

    if (preview) {
        preview.src =
            "";
    }

    if (imageInput) {
        imageInput.value =
            "";
    }

    if (imageStatus) {
        imageStatus.textContent =
            "Imagen actual";
    }

    if (removeButton) {
        removeButton.hidden =
            true;
    }
}


function showImagePreview(
    source,
    label,
    canRemove
) {
    const box =
        getProductElement(
            "admin-product-image-box"
        );

    const preview =
        getProductElement(
            "admin-product-image-preview"
        );

    const imageStatus =
        getProductElement(
            "admin-product-image-status"
        );

    const removeButton =
        getProductElement(
            "admin-product-remove-image"
        );


    if (
        !box ||
        !preview
    ) {
        return;
    }


    preview.src =
        source;


    if (imageStatus) {
        imageStatus.textContent =
            label;
    }


    if (removeButton) {
        removeButton.hidden =
            !canRemove;
    }


    box.hidden =
        false;
}


function openProductCreate() {
    productState.editingProductId =
        null;


    resetProductForm();


    const eyebrow =
        getProductElement(
            "admin-product-modal-eyebrow"
        );

    const title =
        getProductElement(
            "admin-product-modal-title"
        );

    const submitLabel =
        getProductElement(
            "admin-product-submit-label"
        );


    if (eyebrow) {
        eyebrow.textContent =
            "NUEVO PRODUCTO";
    }


    if (title) {
        title.textContent =
            "Crear producto";
    }


    if (submitLabel) {
        submitLabel.textContent =
            "Crear producto";
    }


    const modal =
        getProductElement(
            "admin-products-modal"
        );

    if (!modal) {
        return;
    }


    modal.hidden =
        false;

    modal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.style.overflow =
        "hidden";


    getProductElement(
        "admin-product-code"
    )?.focus();
}


async function openProductEdit(
    productId
) {
    const message =
        getProductElement(
            "admin-product-form-message"
        );


    setProductMessage(
        message,
        ""
    );


    try {

        const response =
            await adminFetch(
                `/api/admin/products/${productId}`
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


        const product =
            data?.data;


        if (!product) {
            throw new Error(
                "El producto no fue encontrado."
            );
        }


        productState.editingProductId =
            product.id;


        fillProductForm(
            product
        );


        const eyebrow =
            getProductElement(
                "admin-product-modal-eyebrow"
            );

        const title =
            getProductElement(
                "admin-product-modal-title"
            );

        const submitLabel =
            getProductElement(
                "admin-product-submit-label"
            );


        if (eyebrow) {
            eyebrow.textContent =
                "EDITAR PRODUCTO";
        }


        if (title) {
            title.textContent =
                "Editar producto";
        }


        if (submitLabel) {
            submitLabel.textContent =
                "Guardar cambios";
        }


        openProductModal();

    } catch (error) {

        if (
            error instanceof Error &&
            error.message ===
            "La sesión ha expirado."
        ) {
            return;
        }


        setProductMessage(
            getProductElement(
                "admin-product-list-message"
            ),
            error instanceof Error
                ? error.message
                : "No fue posible cargar el producto."
        );
    }
}


function fillProductForm(
    product
) {
    getProductElement(
        "admin-product-id"
    ).value =
        String(
            product.id
        );


    getProductElement(
        "admin-product-code"
    ).value =
        product.code || "";


    getProductElement(
        "admin-product-name"
    ).value =
        product.name || "";


    getProductElement(
        "admin-product-description"
    ).value =
        product.description || "";


    getProductElement(
        "admin-product-price"
    ).value =
        product.price || "";


    getProductElement(
        "admin-product-category"
    ).value =
        product.category_id
            ? String(
                product.category_id
            )
            : "";


    getProductElement(
        "admin-product-status"
    ).value =
        product.is_active === true
            ? "true"
            : "false";


    const imageInput =
        getProductElement(
            "admin-product-image"
        );

    if (imageInput) {
        imageInput.value =
            "";
    }


    if (product.image_url) {

        showImagePreview(
            product.image_url,
            "Imagen actual",
            true
        );

    } else {

        resetProductImagePreview();

    }
}


function openProductModal() {
    const modal =
        getProductElement(
            "admin-products-modal"
        );

    if (!modal) {
        return;
    }


    modal.hidden =
        false;

    modal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.style.overflow =
        "hidden";
}


function closeProductModal() {
    const modal =
        getProductElement(
            "admin-products-modal"
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


    productState.editingProductId =
        null;


    resetProductForm();
}


function getProductFormData() {
    const code =
        getProductElement(
            "admin-product-code"
        ).value.trim();

    const name =
        getProductElement(
            "admin-product-name"
        ).value.trim();

    const description =
        getProductElement(
            "admin-product-description"
        ).value.trim();

    const price =
        getProductElement(
            "admin-product-price"
        ).value.trim();

    const categoryId =
        getProductElement(
            "admin-product-category"
        ).value;

    const isActive =
        getProductElement(
            "admin-product-status"
        ).value ===
        "true";

    const image =
        getProductElement(
            "admin-product-image"
        ).files?.[0] || null;


    const formData =
        new FormData();


    formData.append(
        "code",
        code
    );

    formData.append(
        "name",
        name
    );

    formData.append(
        "description",
        description
    );

    formData.append(
        "price",
        price
    );

    formData.append(
        "category_id",
        categoryId
    );

    formData.append(
        "is_active",
        String(
            isActive
        )
    );


    if (image) {
        formData.append(
            "image",
            image
        );
    }


    return formData;
}


function validateProductForm() {
    const code =
        getProductElement(
            "admin-product-code"
        );

    const name =
        getProductElement(
            "admin-product-name"
        );

    const price =
        getProductElement(
            "admin-product-price"
        );

    const category =
        getProductElement(
            "admin-product-category"
        );


    if (!code.value.trim()) {
        return {
            valid: false,
            element: code,
            message:
                "Ingresa el código del producto.",
        };
    }


    if (!name.value.trim()) {
        return {
            valid: false,
            element: name,
            message:
                "Ingresa el nombre del producto.",
        };
    }


    if (!price.value.trim()) {
        return {
            valid: false,
            element: price,
            message:
                "Ingresa el precio del producto.",
        };
    }


    const numericPrice =
        Number(
            price.value
        );


    if (
        !Number.isFinite(
            numericPrice
        ) ||
        numericPrice < 0
    ) {
        return {
            valid: false,
            element: price,
            message:
                "Ingresa un precio válido.",
        };
    }


    if (!category.value) {
        return {
            valid: false,
            element: category,
            message:
                "Selecciona una categoría activa.",
        };
    }


    const selectedCategory =
        productState.categories.find(
            (item) =>
                String(
                    item.id
                ) ===
                category.value
        );


    if (
        !selectedCategory ||
        selectedCategory.is_active !== true
    ) {
        return {
            valid: false,
            element: category,
            message:
                "La categoría seleccionada está inactiva.",
        };
    }


    return {
        valid: true,
    };
}


async function submitProduct(
    event
) {
    event.preventDefault();


    const validation =
        validateProductForm();


    const message =
        getProductElement(
            "admin-product-form-message"
        );


    setProductMessage(
        message,
        ""
    );


    if (!validation.valid) {

        setProductMessage(
            message,
            validation.message
        );

        validation.element?.focus();

        return;
    }


    const button =
        getProductElement(
            "admin-product-submit"
        );

    const label =
        getProductElement(
            "admin-product-submit-label"
        );


    const isEditing =
        Boolean(
            productState.editingProductId
        );


    setProductButtonLoading(
        button,
        label,
        true,
        isEditing
            ? "Guardando..."
            : "Creando...",
        isEditing
            ? "Guardar cambios"
            : "Crear producto"
    );


    try {

        const formData =
            getProductFormData();


        const endpoint =
            isEditing
                ? `/api/admin/products/${productState.editingProductId}`
                : "/api/admin/products";


        const response =
            await adminFetch(
                endpoint,
                {
                    method:
                        isEditing
                            ? "PUT"
                            : "POST",

                    body:
                        formData,
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


        closeProductModal();


        await loadProducts();

    } catch (error) {

        if (
            error instanceof Error &&
            error.message ===
            "La sesión ha expirado."
        ) {
            return;
        }


        setProductMessage(
            message,
            error instanceof Error
                ? error.message
                : "No fue posible guardar el producto."
        );

    } finally {

        setProductButtonLoading(
            button,
            label,
            false,
            isEditing
                ? "Guardando..."
                : "Creando...",
            isEditing
                ? "Guardar cambios"
                : "Crear producto"
        );
    }
}


function setupProductImagePreview() {
    const input =
        getProductElement(
            "admin-product-image"
        );


    if (!input) {
        return;
    }


    input.addEventListener(
        "change",
        () => {

            const file =
                input.files?.[0];


            if (!file) {
                return;
            }


            const allowedTypes =
                [
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                ];


            if (
                !allowedTypes.includes(
                    file.type
                )
            ) {

                setProductMessage(
                    getProductElement(
                        "admin-product-form-message"
                    ),
                    "La imagen debe ser JPG, PNG o WebP."
                );

                input.value =
                    "";

                return;
            }


            if (
                file.size >
                5 * 1024 * 1024
            ) {

                setProductMessage(
                    getProductElement(
                        "admin-product-form-message"
                    ),
                    "La imagen no puede superar 5 MB."
                );

                input.value =
                    "";

                return;
            }


            const objectUrl =
                URL.createObjectURL(
                    file
                );


            showImagePreview(
                objectUrl,
                "Nueva imagen seleccionada",
                false
            );


            setProductMessage(
                getProductElement(
                    "admin-product-form-message"
                ),
                ""
            );
        }
    );
}


async function removeCurrentProductImage() {
    const productId =
        productState.editingProductId;


    if (!productId) {
        return;
    }


    const confirmed =
        window.confirm(
            "¿Deseas eliminar la imagen actual de este producto?"
        );


    if (!confirmed) {
        return;
    }


    const message =
        getProductElement(
            "admin-product-form-message"
        );


    try {

        const response =
            await adminFetch(
                `/api/admin/products/${productId}/image`,
                {
                    method:
                        "DELETE",

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


        resetProductImagePreview();


        const input =
            getProductElement(
                "admin-product-image"
            );

        if (input) {
            input.value =
                "";
        }

    } catch (error) {

        setProductMessage(
            message,
            error instanceof Error
                ? error.message
                : "No fue posible eliminar la imagen."
        );
    }
}


function openDeleteConfirmation(
    product
) {
    if (
        !product ||
        !product.id
    ) {
        return;
    }


    productState.deletingProductId =
        product.id;


    const modal =
        getProductElement(
            "admin-product-delete-confirm"
        );

    const message =
        getProductElement(
            "admin-product-delete-message"
        );


    if (message) {
        message.textContent =
            `Se eliminará "${product.name}" (${product.code}). Esta acción no se puede deshacer.`;
    }


    if (!modal) {
        return;
    }


    modal.hidden =
        false;

    modal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.style.overflow =
        "hidden";
}


function closeDeleteConfirmation() {
    const modal =
        getProductElement(
            "admin-product-delete-confirm"
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


    productState.deletingProductId =
        null;
}


async function confirmProductDeletion() {
    const productId =
        productState.deletingProductId;


    if (!productId) {
        return;
    }


    const button =
        getProductElement(
            "admin-product-delete-confirm-button"
        );


    if (button) {
        button.disabled =
            true;

        button.textContent =
            "Eliminando...";
    }


    try {

        const response =
            await adminFetch(
                `/api/admin/products/${productId}`,
                {
                    method:
                        "DELETE",

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


        closeDeleteConfirmation();

        await loadProducts();

    } catch (error) {

        closeDeleteConfirmation();

        setProductMessage(
            getProductElement(
                "admin-product-list-message"
            ),
            error instanceof Error
                ? error.message
                : "No fue posible eliminar el producto."
        );

    } finally {

        if (button) {
            button.disabled =
                false;

            button.textContent =
                "Eliminar producto";
        }
    }
}


function clearProductFilters() {
    const form =
        getProductElement(
            "admin-product-filter-form"
        );

    if (form) {
        form.reset();
    }


    resetProductPagination();

    void loadProducts();
}


function setupProductFilters() {
    const form =
        getProductElement(
            "admin-product-filter-form"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        (event) => {

            event.preventDefault();

            resetProductPagination();

            void loadProducts();
        }
    );


    getProductElement(
        "admin-product-clear-filters"
    )?.addEventListener(
        "click",
        clearProductFilters
    );
}


function setupProductPagination() {
    getProductElement(
        "admin-product-previous"
    )?.addEventListener(
        "click",
        () => {

            if (
                productState.pagination.hasPrevious
            ) {

                productState.pagination.page -=
                    1;

                void loadProducts();
            }
        }
    );


    getProductElement(
        "admin-product-next"
    )?.addEventListener(
        "click",
        () => {

            if (
                productState.pagination.hasNext
            ) {

                productState.pagination.page +=
                    1;

                void loadProducts();
            }
        }
    );
}


function setupProductModal() {
    const modal =
        getProductElement(
            "admin-products-modal"
        );


    if (!modal) {
        return;
    }


    getProductElement(
        "admin-product-new-button"
    )?.addEventListener(
        "click",
        openProductCreate
    );


    getProductElement(
        "admin-product-modal-close"
    )?.addEventListener(
        "click",
        closeProductModal
    );


    getProductElement(
        "admin-product-cancel"
    )?.addEventListener(
        "click",
        closeProductModal
    );


    modal.querySelectorAll(
        "[data-product-modal-close]"
    ).forEach(
        (element) => {

            element.addEventListener(
                "click",
                closeProductModal
            );

        }
    );


    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Escape"
            ) {

                if (
                    !modal.hidden
                ) {
                    closeProductModal();

                    return;
                }


                const deleteModal =
                    getProductElement(
                        "admin-product-delete-confirm"
                    );


                if (
                    deleteModal &&
                    !deleteModal.hidden
                ) {
                    closeDeleteConfirmation();
                }
            }

        }
    );


    getProductElement(
        "admin-product-form"
    )?.addEventListener(
        "submit",
        submitProduct
    );


    getProductElement(
        "admin-product-remove-image"
    )?.addEventListener(
        "click",
        () => {
            void removeCurrentProductImage();
        }
    );
}


function setupProductDeleteConfirmation() {
    const modal =
        getProductElement(
            "admin-product-delete-confirm"
        );


    if (!modal) {
        return;
    }


    getProductElement(
        "admin-product-delete-cancel"
    )?.addEventListener(
        "click",
        closeDeleteConfirmation
    );


    getProductElement(
        "admin-product-delete-confirm-button"
    )?.addEventListener(
        "click",
        () => {
            void confirmProductDeletion();
        }
    );


    modal.querySelectorAll(
        "[data-product-delete-close]"
    ).forEach(
        (element) => {

            element.addEventListener(
                "click",
                closeDeleteConfirmation
            );

        }
    );
}


async function setupProductsPage() {
    if (
        !getProductElement(
            "admin-products-table-body"
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


    setupProductFilters();

    setupProductPagination();

    setupProductModal();

    setupProductDeleteConfirmation();

    setupProductImagePreview();

    await loadCategories();

    await loadProducts();
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        void setupProductsPage();
    }
);