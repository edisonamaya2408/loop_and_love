"use strict";


const catalogState = {
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
};


function getCatalogElement(
    id
) {
    return document.getElementById(
        id
    );
}


/* ==================================================
   IMAGE VIEWER
================================================== */

function openCatalogImageModal(
    imageUrl,
    productName
) {
    const modal =
        getCatalogElement(
            "catalog-image-modal"
        );

    const image =
        getCatalogElement(
            "catalog-image-modal-image"
        );

    const title =
        getCatalogElement(
            "catalog-image-modal-title"
        );

    if (
        !modal ||
        !image
    ) {
        return;
    }

    image.src =
        imageUrl;

    image.alt =
        productName ||
        "Producto Loop & Love";

    if (title) {
        title.textContent =
            productName ||
            "Producto";
    }

    modal.hidden =
        false;

    modal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.style.overflow =
        "hidden";

    getCatalogElement(
        "catalog-image-modal-close"
    )?.focus();
}


function closeCatalogImageModal() {
    const modal =
        getCatalogElement(
            "catalog-image-modal"
        );

    const image =
        getCatalogElement(
            "catalog-image-modal-image"
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

    if (image) {
        image.removeAttribute(
            "src"
        );
    }

    document.body.style.overflow =
        "";
}


function setupCatalogImageModal() {
    const modal =
        getCatalogElement(
            "catalog-image-modal"
        );

    if (!modal) {
        return;
    }


    const closeButton =
        getCatalogElement(
            "catalog-image-modal-close"
        );


    closeButton?.addEventListener(
        "click",
        closeCatalogImageModal
    );


    modal.querySelectorAll(
        "[data-catalog-image-modal-close]"
    ).forEach(
        (
            element
        ) => {

            element.addEventListener(
                "click",
                closeCatalogImageModal
            );

        }
    );


    document.addEventListener(
        "keydown",
        (
            event
        ) => {

            if (
                event.key === "Escape" &&
                !modal.hidden
            ) {
                closeCatalogImageModal();
            }

        }
    );
}


/* ==================================================
   FILTER TOGGLE
================================================== */

function setupCatalogFiltersToggle() {
    const toggle =
        getCatalogElement(
            "catalog-filter-toggle"
        );

    const filters =
        getCatalogElement(
            "catalog-filters"
        );

    if (
        !toggle ||
        !filters
    ) {
        return;
    }


    toggle.addEventListener(
        "click",
        () => {

            const collapsed =
                filters.classList.toggle(
                    "catalog-filters--collapsed"
                );

            toggle.setAttribute(
                "aria-expanded",
                String(
                    !collapsed
                )
            );

        }
    );
}


/* ==================================================
   MESSAGES
================================================== */

function setCatalogMessage(
    element,
    message
) {
    if (!element) {
        return;
    }

    if (!message) {
        element.hidden =
            true;

        element.textContent =
            "";

        return;
    }

    element.hidden =
        false;

    element.textContent =
        message;
}


/* ==================================================
   FORMATTERS
================================================== */

function formatCatalogPrice(
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


function formatCatalogCount(
    total
) {
    if (
        total === 1
    ) {
        return "1 producto";
    }

    return `${total} productos`;
}


function formatCatalogDate(
    value
) {
    if (!value) {
        return "";
    }

    const date =
        new Date(
            value
        );

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return "";
    }

    return date.toLocaleDateString(
        "es-CO",
        {
            year:
                "numeric",

            month:
                "long",

            day:
                "numeric",
        }
    );
}


/* ==================================================
   FILTERS
================================================== */

function getCatalogFilters() {
    return {
        search:
            getCatalogElement(
                "catalog-search"
            )?.value.trim() || "",

        category_id:
            getCatalogElement(
                "catalog-category"
            )?.value || "",

        min_price:
            getCatalogElement(
                "catalog-min-price"
            )?.value || "",

        max_price:
            getCatalogElement(
                "catalog-max-price"
            )?.value || "",
    };
}


function validateCatalogPriceRange(
    filters
) {
    if (
        filters.min_price === "" ||
        filters.max_price === ""
    ) {
        return {
            valid:
                true,
        };
    }


    const minimum =
        Number(
            filters.min_price
        );

    const maximum =
        Number(
            filters.max_price
        );


    if (
        !Number.isFinite(
            minimum
        ) ||
        !Number.isFinite(
            maximum
        )
    ) {
        return {
            valid:
                false,

            message:
                "Ingresa un rango de precios válido.",
        };
    }


    if (
        minimum < 0 ||
        maximum < 0
    ) {
        return {
            valid:
                false,

            message:
                "Los precios no pueden ser negativos.",
        };
    }


    if (
        minimum > maximum
    ) {
        return {
            valid:
                false,

            message:
                "El precio mínimo no puede ser mayor que el máximo.",
        };
    }


    return {
        valid:
            true,
    };
}


function buildCatalogProductsUrl() {
    const filters =
        getCatalogFilters();


    const params =
        new URLSearchParams();


    params.set(
        "page",
        String(
            catalogState.pagination.page
        )
    );


    params.set(
        "per_page",
        String(
            catalogState.pagination.perPage
        )
    );


    Object.entries(
        filters
    ).forEach(
        (
            [key, value]
        ) => {

            if (
                value !== ""
            ) {
                params.set(
                    key,
                    value
                );
            }

        }
    );


    return (
        "/api/products?" +
        params.toString()
    );
}


/* ==================================================
   LOADING
================================================== */

function showCatalogLoading(
    loading
) {
    const loadingElement =
        getCatalogElement(
            "catalog-loading"
        );


    if (loadingElement) {
        loadingElement.hidden =
            !loading;
    }


    if (loading) {

        const results =
            getCatalogElement(
                "catalog-results"
            );

        const empty =
            getCatalogElement(
                "catalog-empty"
            );

        const error =
            getCatalogElement(
                "catalog-error"
            );

        const pagination =
            getCatalogElement(
                "catalog-pagination"
            );


        if (results) {
            results.hidden =
                true;
        }

        if (empty) {
            empty.hidden =
                true;
        }

        if (error) {
            error.hidden =
                true;
        }

        if (pagination) {
            pagination.hidden =
                true;
        }
    }
}


/* ==================================================
   CATEGORIES
================================================== */

function renderCatalogCategories() {
    const select =
        getCatalogElement(
            "catalog-category"
        );


    if (!select) {
        return;
    }


    const currentValue =
        select.value;


    select.replaceChildren();


    const allOption =
        document.createElement(
            "option"
        );


    allOption.value =
        "";

    allOption.textContent =
        "Todas las categorías";


    select.append(
        allOption
    );


    catalogState.categories.forEach(
        (
            category
        ) => {

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


            select.append(
                option
            );

        }
    );


    select.value =
        currentValue;
}


async function loadCatalogCategories() {
    const response =
        await fetch(
            "/api/categories",
            {
                method:
                    "GET",

                headers: {
                    Accept:
                        "application/json",
                },
            }
        );


    const data =
        await parseCatalogJson(
            response
        );


    if (!response.ok) {
        throw new Error(
            getCatalogApiError(
                data,
                "No fue posible cargar las categorías."
            )
        );
    }


    catalogState.categories =
        Array.isArray(
            data?.data
        )
            ? data.data
            : [];


    renderCatalogCategories();
}


/* ==================================================
   PRODUCTS
================================================== */

async function loadCatalogProducts() {
    const response =
        await fetch(
            buildCatalogProductsUrl(),
            {
                method:
                    "GET",

                headers: {
                    Accept:
                        "application/json",
                },
            }
        );


    const data =
        await parseCatalogJson(
            response
        );


    if (!response.ok) {
        throw new Error(
            getCatalogApiError(
                data,
                "No fue posible cargar los productos."
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
        data?.pagination ||
        {};


    catalogState.products =
        products;


    catalogState.pagination = {
        page:
            Number(
                pagination.page
            ) || 1,

        perPage:
            Number(
                pagination.per_page
            ) ||
            catalogState.pagination.perPage,

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
}


async function parseCatalogJson(
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


function getCatalogApiError(
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


function clearCatalogResults() {
    const results =
        getCatalogElement(
            "catalog-results"
        );


    if (results) {
        results.replaceChildren();
    }
}


/* ==================================================
   PRODUCT CARD
================================================== */

function renderCatalogProduct(
    product
) {
    const article =
        document.createElement(
            "article"
        );


    article.className =
        "catalog-product-card";


    const media =
        document.createElement(
            "button"
        );


    media.type =
        "button";


    media.className =
        "catalog-product-card__media";


    const imageUrl =
        typeof product.image_url ===
            "string"
            ? product.image_url.trim()
            : "";


    if (
        imageUrl
    ) {

        media.setAttribute(
            "aria-label",
            `Ver imagen completa de ${
                product.name ||
                "Producto"
            }`
        );


        media.addEventListener(
            "click",
            () => {

                openCatalogImageModal(
                    imageUrl,
                    product.name
                );

            }
        );


        const image =
            document.createElement(
                "img"
            );


        image.src =
            imageUrl;


        image.alt =
            product.name ||
            "Producto Loop & Love";


        image.loading =
            "lazy";


        image.decoding =
            "async";


        image.addEventListener(
            "error",
            () => {

                media.replaceChildren();


                media.disabled =
                    true;


                media.removeAttribute(
                    "aria-label"
                );


                media.setAttribute(
                    "aria-hidden",
                    "true"
                );


                const placeholder =
                    document.createElement(
                        "span"
                    );


                placeholder.className =
                    "catalog-product-card__placeholder";


                placeholder.setAttribute(
                    "aria-hidden",
                    "true"
                );


                placeholder.textContent =
                    "♡";


                media.append(
                    placeholder
                );

            },
            {
                once:
                    true,
            }
        );


        media.append(
            image
        );


    } else {

        media.disabled =
            true;


        media.setAttribute(
            "aria-hidden",
            "true"
        );


        const placeholder =
            document.createElement(
                "span"
            );


        placeholder.className =
            "catalog-product-card__placeholder";


        placeholder.setAttribute(
            "aria-hidden",
            "true"
        );


        placeholder.textContent =
            "♡";


        media.append(
            placeholder
        );
    }


    const body =
        document.createElement(
            "div"
        );


    body.className =
        "catalog-product-card__body";


    const category =
        document.createElement(
            "span"
        );


    category.className =
        "catalog-product-card__category";


    category.textContent =
        product.category?.name ||
        "Sin categoría";


    const name =
        document.createElement(
            "h3"
        );


    name.className =
        "catalog-product-card__name";


    name.textContent =
        product.name ||
        "Producto";


    const code =
        document.createElement(
            "span"
        );


    code.className =
        "catalog-product-card__code";


    code.textContent =
        product.code ||
        "";


    body.append(
        category,
        name,
        code
    );


    if (
        product.description
    ) {

        const description =
            document.createElement(
                "p"
            );


        description.className =
            "catalog-product-card__description";


        description.textContent =
            product.description;


        body.append(
            description
        );
    }


    const footer =
        document.createElement(
            "div"
        );


    footer.className =
        "catalog-product-card__footer";


    const price =
        document.createElement(
            "strong"
        );


    price.className =
        "catalog-product-card__price";


    price.textContent =
        formatCatalogPrice(
            product.price
        );


    const available =
        document.createElement(
            "span"
        );


    available.className =
        "catalog-product-card__available";


    const availableDot =
        document.createElement(
            "span"
        );


    availableDot.className =
        "catalog-product-card__available-dot";


    availableDot.setAttribute(
        "aria-hidden",
        "true"
    );


    available.append(
        availableDot,
        document.createTextNode(
            "Disponible"
        )
    );


    footer.append(
        price,
        available
    );


    article.append(
        media,
        body,
        footer
    );


    return article;
}


/* ==================================================
   RENDER PRODUCTS
================================================== */

function renderCatalogProducts() {
    const results =
        getCatalogElement(
            "catalog-results"
        );


    const empty =
        getCatalogElement(
            "catalog-empty"
        );


    const error =
        getCatalogElement(
            "catalog-error"
        );


    if (!results) {
        return;
    }


    clearCatalogResults();


    if (error) {
        error.hidden =
            true;
    }


    if (
        !catalogState.products.length
    ) {

        results.hidden =
            true;


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


    results.hidden =
        false;


    catalogState.products.forEach(
        (
            product
        ) => {

            results.append(
                renderCatalogProduct(
                    product
                )
            );

        }
    );
}


/* ==================================================
   PAGINATION
================================================== */

function renderCatalogPagination() {
    const pagination =
        getCatalogElement(
            "catalog-pagination"
        );


    const previous =
        getCatalogElement(
            "catalog-previous"
        );


    const next =
        getCatalogElement(
            "catalog-next"
        );


    const indicator =
        getCatalogElement(
            "catalog-page-indicator"
        );


    const hasMultiplePages =
        catalogState.pagination.pages >
        1;


    if (pagination) {
        pagination.hidden =
            !hasMultiplePages;
    }


    if (previous) {
        previous.disabled =
            !catalogState.pagination.hasPrevious;
    }


    if (next) {
        next.disabled =
            !catalogState.pagination.hasNext;
    }


    if (indicator) {
        indicator.textContent =
            `Página ${catalogState.pagination.page} de ${catalogState.pagination.pages}`;
    }
}


/* ==================================================
   RESULT HEADER
================================================== */

function updateCatalogResultHeader() {
    const count =
        getCatalogElement(
            "catalog-results-count"
        );


    const status =
        getCatalogElement(
            "catalog-results-status"
        );


    const total =
        catalogState.pagination.total;


    if (count) {
        count.textContent =
            formatCatalogCount(
                total
            );
    }


    if (status) {

        if (
            total === 0
        ) {

            status.textContent =
                "Sin resultados";

            return;
        }


        const start =
            (
                (
                    catalogState.pagination.page
                    - 1
                )
                *
                catalogState.pagination.perPage
            )
            + 1;


        const end =
            Math.min(
                start
                +
                catalogState.products.length
                -
                1,
                total
            );


        status.textContent =
            `Mostrando ${start}-${end} de ${total}`;
    }
}


/* ==================================================
   ERROR
================================================== */

function showCatalogError(
    message
) {
    const results =
        getCatalogElement(
            "catalog-results"
        );


    const loading =
        getCatalogElement(
            "catalog-loading"
        );


    const empty =
        getCatalogElement(
            "catalog-empty"
        );


    const pagination =
        getCatalogElement(
            "catalog-pagination"
        );


    const error =
        getCatalogElement(
            "catalog-error"
        );


    const errorMessage =
        getCatalogElement(
            "catalog-error-message"
        );


    if (results) {
        results.hidden =
            true;
    }


    if (loading) {
        loading.hidden =
            true;
    }


    if (empty) {
        empty.hidden =
            true;
    }


    if (pagination) {
        pagination.hidden =
            true;
    }


    if (errorMessage) {
        errorMessage.textContent =
            message;
    }


    if (error) {
        error.hidden =
            false;
    }


    const status =
        getCatalogElement(
            "catalog-results-status"
        );


    if (status) {
        status.textContent =
            "No disponible";
    }
}


/* ==================================================
   REFRESH
================================================== */

async function refreshCatalog() {
    const filters =
        getCatalogFilters();


    const validation =
        validateCatalogPriceRange(
            filters
        );


    const filterMessage =
        getCatalogElement(
            "catalog-filter-message"
        );


    setCatalogMessage(
        filterMessage,
        ""
    );


    if (
        !validation.valid
    ) {

        setCatalogMessage(
            filterMessage,
            validation.message
        );

        return;
    }


    catalogState.pagination.page =
        1;


    showCatalogLoading(
        true
    );


    const status =
        getCatalogElement(
            "catalog-results-status"
        );


    const count =
        getCatalogElement(
            "catalog-results-count"
        );


    if (status) {
        status.textContent =
            "Cargando productos...";
    }


    if (count) {
        count.textContent =
            "Cargando catálogo...";
    }


    try {

        await loadCatalogProducts();


        renderCatalogProducts();

        renderCatalogPagination();

        updateCatalogResultHeader();


        showCatalogLoading(
            false
        );

    } catch (
        error
    ) {

        showCatalogError(
            error instanceof Error
                ? error.message
                : "No fue posible cargar los productos."
        );
    }
}


/* ==================================================
   INITIALIZE
================================================== */

async function initializeCatalog() {
    const results =
        getCatalogElement(
            "catalog-results"
        );


    if (!results) {
        return;
    }


    showCatalogLoading(
        true
    );


    try {

        await Promise.all(
            [
                loadCatalogCategories(),
                loadCatalogProducts(),
            ]
        );


        renderCatalogProducts();

        renderCatalogPagination();

        updateCatalogResultHeader();


        showCatalogLoading(
            false
        );

    } catch (
        error
    ) {

        showCatalogError(
            error instanceof Error
                ? error.message
                : "No fue posible cargar el catálogo."
        );
    }
}


/* ==================================================
   FILTER FORM
================================================== */

function setupCatalogFilterForm() {
    const form =
        getCatalogElement(
            "catalog-filter-form"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        async (
            event
        ) => {

            event.preventDefault();


            await refreshCatalog();


            const results =
                getCatalogElement(
                    "catalog-results"
                );


            if (
                results &&
                !results.hidden
            ) {

                results.scrollIntoView(
                    {
                        behavior:
                            "smooth",

                        block:
                            "start",
                    }
                );
            }

        }
    );


    form.addEventListener(
        "reset",
        () => {

            window.setTimeout(
                () => {

                    const message =
                        getCatalogElement(
                            "catalog-filter-message"
                        );


                    setCatalogMessage(
                        message,
                        ""
                    );


                    catalogState.pagination.page =
                        1;


                    void refreshCatalog();

                },
                0
            );

        }
    );
}


/* ==================================================
   PAGINATION CONTROLS
================================================== */

function setupCatalogPagination() {
    const previous =
        getCatalogElement(
            "catalog-previous"
        );


    const next =
        getCatalogElement(
            "catalog-next"
        );


    previous?.addEventListener(
        "click",
        () => {

            if (
                !catalogState.pagination.hasPrevious
            ) {
                return;
            }


            catalogState.pagination.page -=
                1;


            void refreshCatalogPage();

        }
    );


    next?.addEventListener(
        "click",
        () => {

            if (
                !catalogState.pagination.hasNext
            ) {
                return;
            }


            catalogState.pagination.page +=
                1;


            void refreshCatalogPage();

        }
    );
}


async function refreshCatalogPage() {
    showCatalogLoading(
        true
    );


    const status =
        getCatalogElement(
            "catalog-results-status"
        );


    if (status) {
        status.textContent =
            "Cargando productos...";
    }


    try {

        await loadCatalogProducts();


        renderCatalogProducts();

        renderCatalogPagination();

        updateCatalogResultHeader();


        showCatalogLoading(
            false
        );


        const results =
            getCatalogElement(
                "catalog-results"
            );


        if (
            results &&
            !results.hidden
        ) {

            results.scrollIntoView(
                {
                    behavior:
                        "smooth",

                    block:
                        "start",
                }
            );
        }

    } catch (
        error
    ) {

        showCatalogError(
            error instanceof Error
                ? error.message
                : "No fue posible cargar los productos."
        );
    }
}


/* ==================================================
   RETRY
================================================== */

function setupCatalogRetry() {
    const retry =
        getCatalogElement(
            "catalog-retry"
        );


    if (!retry) {
        return;
    }


    retry.addEventListener(
        "click",
        () => {

            void initializeCatalog();

        }
    );
}


/* ==================================================
   INITIAL PAGE
================================================== */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupCatalogFiltersToggle();

        setupCatalogFilterForm();

        setupCatalogPagination();

        setupCatalogRetry();

        setupCatalogImageModal();

        void initializeCatalog();

    }
);