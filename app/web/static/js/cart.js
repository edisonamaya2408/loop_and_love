"use strict";


const CART_STORAGE_KEY =
    "loop_and_love.b2b_cart";

const CART_MAX_QUANTITY =
    99;


const cartState = {
    items: [],
};


function getCartElement(
    id
) {
    return document.getElementById(
        id
    );
}


/* ==================================================
   FORMAT
================================================== */

function formatCartPrice(
    value
) {
    const numericValue =
        Number(value);


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


/* ==================================================
   STORAGE
================================================== */

function saveCart() {
    try {

        window.localStorage.setItem(
            CART_STORAGE_KEY,
            JSON.stringify(
                cartState.items
            )
        );

    } catch (
    error
    ) {

        /*
         * El carrito continúa funcionando en memoria aunque
         * el navegador no permita utilizar localStorage.
         */

    }
}


function loadCart() {
    cartState.items = [];


    try {

        const raw =
            window.localStorage.getItem(
                CART_STORAGE_KEY
            );


        if (!raw) {
            return;
        }


        const parsed =
            JSON.parse(
                raw
            );


        if (!Array.isArray(parsed)) {
            return;
        }


        cartState.items =
            parsed
                .filter(
                    (
                        item
                    ) =>
                        item &&
                        Number.isInteger(
                            Number(
                                item.product_id
                            )
                        ) &&
                        Number(
                            item.product_id
                        ) > 0 &&
                        Number.isInteger(
                            Number(
                                item.quantity
                            )
                        ) &&
                        Number(
                            item.quantity
                        ) > 0
                )
                .map(
                    (
                        item
                    ) => {

                        const quantity =
                            Math.min(
                                Math.floor(
                                    Number(
                                        item.quantity
                                    )
                                ),
                                CART_MAX_QUANTITY
                            );


                        return {
                            product_id:
                                Number(
                                    item.product_id
                                ),

                            code:
                                typeof item.code ===
                                    "string"
                                    ? item.code
                                    : "",

                            name:
                                typeof item.name ===
                                    "string"
                                    ? item.name
                                    : "Producto",

                            price:
                                String(
                                    item.price ??
                                    "0"
                                ),

                            image_url:
                                typeof item.image_url ===
                                    "string"
                                    ? item.image_url
                                    : "",

                            quantity,
                        };
                    }
                )
                .filter(
                    (
                        item
                    ) =>
                        item.quantity > 0
                );

    } catch (
    error
    ) {

        cartState.items = [];

    }
}


/* ==================================================
   CART STATE
================================================== */

function getCartItem(
    productId
) {
    return cartState.items.find(
        (
            item
        ) =>
            item.product_id ===
            Number(
                productId
            )
    );
}


function getCartQuantity() {
    return cartState.items.reduce(
        (
            total,
            item
        ) =>
            total +
            item.quantity,
        0
    );
}


function getCartTotal() {
    return cartState.items.reduce(
        (
            total,
            item
        ) => {

            const price =
                Number(
                    item.price
                );


            if (
                !Number.isFinite(
                    price
                )
            ) {
                return total;
            }


            return (
                total +
                (
                    price *
                    item.quantity
                )
            );

        },
        0
    );
}


/* ==================================================
   HEADER COUNT
================================================== */

function updateCartCount() {
    const headerCount =
        getCartElement(
            "cart-count"
        );


    const sectionCount =
        getCartElement(
            "cart-section-count"
        );


    const quantity =
        getCartQuantity();


    if (headerCount) {

        headerCount.textContent =
            String(
                quantity
            );

    }


    if (sectionCount) {

        sectionCount.textContent =
            quantity === 1
                ? "1 producto"
                : `${quantity} productos`;

    }
}


/* ==================================================
   PRODUCT BUTTONS
================================================== */

function getCatalogProducts() {
    if (
        typeof catalogState ===
        "undefined" ||
        !catalogState ||
        !Array.isArray(
            catalogState.products
        )
    ) {
        return [];
    }


    return catalogState.products;
}


function findProductFromCard(
    card
) {
    const codeElement =
        card.querySelector(
            ".catalog-product-card__code"
        );


    const code =
        codeElement?.textContent.trim() ||
        "";


    if (!code) {
        return null;
    }


    return (
        getCatalogProducts().find(
            (
                product
            ) =>
                product &&
                String(
                    product.code ||
                    ""
                ) === code
        ) ||
        null
    );
}


function refreshProductButtons() {
    const cards =
        document.querySelectorAll(
            ".catalog-product-card"
        );


    cards.forEach(
        (
            card
        ) => {

            const product =
                findProductFromCard(
                    card
                );


            if (!product) {
                return;
            }


            const button =
                card.querySelector(
                    ".catalog-product-card__add"
                );


            if (!button) {
                return;
            }


            const existing =
                getCartItem(
                    product.id
                );


            button.textContent =
                existing
                    ? "Agregar otra unidad"
                    : "Agregar al pedido";

        }
    );
}


function decorateProductCards() {
    const cards =
        document.querySelectorAll(
            ".catalog-product-card"
        );


    cards.forEach(
        (
            card
        ) => {

            if (
                card.querySelector(
                    ".catalog-product-card__add"
                )
            ) {
                return;
            }


            const product =
                findProductFromCard(
                    card
                );


            if (!product) {
                return;
            }


            const body =
                card.querySelector(
                    ".catalog-product-card__body"
                );


            if (!body) {
                return;
            }


            const button =
                document.createElement(
                    "button"
                );


            button.type =
                "button";


            button.className =
                "catalog-product-card__add";


            button.textContent =
                getCartItem(
                    product.id
                )
                    ? "Agregar otra unidad"
                    : "Agregar al pedido";


            button.setAttribute(
                "aria-label",
                `Agregar ${product.name ||
                "producto"
                } al pedido`
            );


            button.addEventListener(
                "click",
                () => {

                    addProductToCart(
                        product
                    );

                }
            );


            body.append(
                button
            );

        }
    );
}


/* ==================================================
   ADD
================================================== */

function addProductToCart(
    product
) {
    if (
        !product ||
        !Number.isInteger(
            Number(
                product.id
            )
        ) ||
        Number(
            product.id
        ) <= 0
    ) {
        return;
    }


    const productId =
        Number(
            product.id
        );


    const existing =
        getCartItem(
            productId
        );


    if (existing) {

        existing.quantity =
            Math.min(
                existing.quantity +
                1,

                CART_MAX_QUANTITY
            );

    } else {

        cartState.items.push(
            {
                product_id:
                    productId,

                code:
                    product.code ||
                    "",

                name:
                    product.name ||
                    "Producto",

                price:
                    String(
                        product.price ??
                        "0"
                    ),

                image_url:
                    product.image_url ||
                    "",

                quantity:
                    1,
            }
        );

    }


    saveCart();

    renderCart();

    scrollToCart();
}


/* ==================================================
   UPDATE QUANTITY
================================================== */

function updateCartQuantity(
    productId,
    quantity
) {
    const item =
        getCartItem(
            productId
        );


    if (!item) {
        return;
    }


    const normalized =
        Math.floor(
            Number(
                quantity
            )
        );


    if (
        !Number.isFinite(
            normalized
        )
    ) {
        return;
    }


    if (
        normalized <= 0
    ) {

        removeCartItem(
            productId
        );

        return;
    }


    item.quantity =
        Math.min(
            normalized,
            CART_MAX_QUANTITY
        );


    saveCart();

    renderCart();
}


/* ==================================================
   REMOVE / CLEAR
================================================== */

function removeCartItem(
    productId
) {
    cartState.items =
        cartState.items.filter(
            (
                item
            ) =>
                item.product_id !==
                Number(
                    productId
                )
        );


    saveCart();

    renderCart();
}


function clearCart() {
    cartState.items = [];

    saveCart();

    renderCart();
}


/* ==================================================
   RENDER CART
================================================== */

function renderCart() {
    updateCartCount();


    const itemsContainer =
        getCartElement(
            "cart-items"
        );


    const empty =
        getCartElement(
            "cart-empty"
        );


    const list =
        getCartElement(
            "cart-list"
        );


    const total =
        getCartElement(
            "cart-total"
        );


    const clearButton =
        getCartElement(
            "cart-clear"
        );


    if (
        !itemsContainer ||
        !empty ||
        !list
    ) {

        refreshProductButtons();

        return;
    }


    itemsContainer.replaceChildren();


    const hasItems =
        cartState.items.length >
        0;


    empty.hidden =
        hasItems;


    list.hidden =
        !hasItems;


    if (clearButton) {

        clearButton.hidden =
            !hasItems;

    }


    if (total) {

        total.textContent =
            formatCartPrice(
                getCartTotal()
            );

    }


    if (!hasItems) {

        refreshProductButtons();

        return;
    }


    cartState.items.forEach(
        (
            item
        ) => {

            const row =
                document.createElement(
                    "article"
                );


            row.className =
                "catalog-cart-item";


            row.dataset.productId =
                String(
                    item.product_id
                );


            const image =
                document.createElement(
                    "div"
                );


            image.className =
                "catalog-cart-item__image";


            if (
                item.image_url
            ) {

                const imageElement =
                    document.createElement(
                        "img"
                    );


                imageElement.src =
                    item.image_url;


                imageElement.alt =
                    item.name;


                imageElement.loading =
                    "lazy";


                image.append(
                    imageElement
                );

            } else {

                const placeholder =
                    document.createElement(
                        "span"
                    );


                placeholder.textContent =
                    "♡";


                placeholder.setAttribute(
                    "aria-hidden",
                    "true"
                );


                image.append(
                    placeholder
                );

            }


            const content =
                document.createElement(
                    "div"
                );


            content.className =
                "catalog-cart-item__content";


            const name =
                document.createElement(
                    "strong"
                );


            name.className =
                "catalog-cart-item__name";


            name.textContent =
                item.name;


            const code =
                document.createElement(
                    "small"
                );


            code.className =
                "catalog-cart-item__code";


            code.textContent =
                item.code;


            const price =
                document.createElement(
                    "span"
                );


            price.className =
                "catalog-cart-item__price";


            price.textContent =
                formatCartPrice(
                    item.price
                );


            content.append(
                name,
                code,
                price
            );


            const controls =
                document.createElement(
                    "div"
                );


            controls.className =
                "catalog-cart-item__controls";


            const decrease =
                createQuantityButton(
                    "decrease",
                    item.product_id,
                    `Disminuir cantidad de ${item.name}`,
                    "−"
                );


            const quantity =
                document.createElement(
                    "span"
                );


            quantity.className =
                "catalog-cart-item__quantity";


            quantity.textContent =
                String(
                    item.quantity
                );


            const increase =
                createQuantityButton(
                    "increase",
                    item.product_id,
                    `Aumentar cantidad de ${item.name}`,
                    "+"
                );


            const remove =
                document.createElement(
                    "button"
                );


            remove.type =
                "button";


            remove.className =
                "catalog-cart-item__remove";


            remove.dataset.cartAction =
                "remove";


            remove.dataset.productId =
                String(
                    item.product_id
                );


            remove.setAttribute(
                "aria-label",
                `Eliminar ${item.name} del pedido`
            );


            remove.textContent =
                "Eliminar";


            controls.append(
                decrease,
                quantity,
                increase,
                remove
            );


            row.append(
                image,
                content,
                controls
            );


            itemsContainer.append(
                row
            );

        }
    );


    refreshProductButtons();
}


function createQuantityButton(
    action,
    productId,
    ariaLabel,
    text
) {
    const button =
        document.createElement(
            "button"
        );


    button.type =
        "button";


    button.className =
        "catalog-cart-item__quantity-button";


    button.dataset.cartAction =
        action;


    button.dataset.productId =
        String(
            productId
        );


    button.setAttribute(
        "aria-label",
        ariaLabel
    );


    button.textContent =
        text;


    return button;
}


/* ==================================================
   EVENTS
================================================== */

function setupCartControls() {
    const items =
        getCartElement(
            "cart-items"
        );


    items?.addEventListener(
        "click",
        (
            event
        ) => {

            if (
                !(event.target instanceof Element)
            ) {
                return;
            }


            const button =
                event.target.closest(
                    "[data-cart-action]"
                );


            if (!button) {
                return;
            }


            const productId =
                Number(
                    button.dataset.productId
                );


            const action =
                button.dataset.cartAction;


            const item =
                getCartItem(
                    productId
                );


            if (!item) {
                return;
            }


            if (
                action ===
                "increase"
            ) {

                updateCartQuantity(
                    productId,
                    item.quantity + 1
                );

                return;
            }


            if (
                action ===
                "decrease"
            ) {

                updateCartQuantity(
                    productId,
                    item.quantity - 1
                );

                return;
            }


            if (
                action ===
                "remove"
            ) {

                removeCartItem(
                    productId
                );

            }

        }
    );


    getCartElement(
        "cart-clear"
    )?.addEventListener(
        "click",
        () => {
            clearCart();
        }
    );
}


/* ==================================================
   PRODUCT GRID OBSERVER
================================================== */

function setupProductCardObserver() {
    const results =
        getCartElement(
            "catalog-results"
        );


    if (!results) {
        return;
    }


    const observer =
        new MutationObserver(
            () => {

                window.requestAnimationFrame(
                    () => {
                        decorateProductCards();
                    }
                );

            }
        );


    observer.observe(
        results,
        {
            childList:
                true,
        }
    );


    decorateProductCards();
}


/* ==================================================
   SCROLL
================================================== */

function scrollToCart() {
    const cartSection =
        getCartElement(
            "pedido"
        );


    if (!cartSection) {
        return;
    }


    window.setTimeout(
        () => {

            cartSection.scrollIntoView(
                {
                    behavior:
                        "smooth",

                    block:
                        "start",
                }
            );

        },
        80
    );
}


/* ==================================================
   INITIALIZE
================================================== */

function setupCart() {
    loadCart();

    renderCart();

    setupCartControls();

    setupProductCardObserver();
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        setupCart();
    }
);