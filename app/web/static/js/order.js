"use strict";


const ORDER_API_URL =
    "/api/orders";


const orderState = {
    submitting:
        false,
};


/* ==================================================
   DOM
================================================== */

function getOrderElement(
    id
) {
    return document.getElementById(
        id
    );
}


/* ==================================================
   FORMAT
================================================== */

function formatOrderPrice(
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


/* ==================================================
   CART PAYLOAD
================================================== */

function getOrderCartItems() {
    if (
        typeof cartState ===
        "undefined" ||
        !cartState ||
        !Array.isArray(
            cartState.items
        )
    ) {
        return [];
    }


    return cartState.items
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
            ) => ({
                product_id:
                    Number(
                        item.product_id
                    ),

                quantity:
                    Math.floor(
                        Number(
                            item.quantity
                        )
                    ),
            })
        );
}


/* ==================================================
   WHATSAPP
================================================== */

function getWhatsAppNumber() {
    const orderSection =
        getOrderElement(
            "pedido"
        );


    const rawNumber =
        orderSection?.dataset
            ?.whatsappNumber ||
        "";


    const normalized =
        String(
            rawNumber
        )
            .trim()
            .replace(
                /[^\d]/g,
                ""
            );


    if (
        normalized.startsWith(
            "00"
        )
    ) {
        return normalized.slice(
            2
        );
    }


    return normalized;
}


function isValidWhatsAppNumber(
    number
) {
    return (
        /^\d{8,15}$/.test(
            number
        )
    );
}


/* ==================================================
   RESPONSE
================================================== */

async function parseOrderResponse(
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


function getOrderApiError(
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


/* ==================================================
   FEEDBACK
================================================== */

function clearOrderFeedback() {
    const feedback =
        getOrderElement(
            "order-feedback"
        );


    if (!feedback) {
        return;
    }


    feedback.hidden =
        true;


    feedback.className =
        "catalog-order-feedback";


    feedback.replaceChildren();
}


function showOrderFeedback(
    message,
    type = "error",
    whatsappUrl = ""
) {
    const feedback =
        getOrderElement(
            "order-feedback"
        );


    if (!feedback) {
        return;
    }


    feedback.replaceChildren();


    feedback.hidden =
        false;


    feedback.className =
        `catalog-order-feedback catalog-order-feedback--${type}`;


    const text =
        document.createElement(
            "p"
        );


    text.className =
        "catalog-order-feedback__text";


    text.textContent =
        message;


    feedback.append(
        text
    );


    if (
        whatsappUrl
    ) {
        const link =
            document.createElement(
                "a"
            );


        link.className =
            "catalog-order-feedback__link";


        link.href =
            whatsappUrl;


        link.target =
            "_blank";


        link.rel =
            "noopener noreferrer";


        link.textContent =
            "Abrir WhatsApp";


        feedback.append(
            link
        );
    }
}


/* ==================================================
   SUBMITTING STATE
================================================== */

function setOrderSubmitting(
    submitting
) {
    orderState.submitting =
        submitting;


    const button =
        getOrderElement(
            "order-submit"
        );


    const clearButton =
        getOrderElement(
            "cart-clear"
        );


    if (button) {
        button.disabled =
            submitting;


        button.textContent =
            submitting
                ? "Creando pedido..."
                : "Enviar pedido por WhatsApp";
    }


    if (clearButton) {
        clearButton.disabled =
            submitting;
    }


    const quantityButtons =
        document.querySelectorAll(
            "#cart-items [data-cart-action]"
        );


    quantityButtons.forEach(
        (
            quantityButton
        ) => {
            quantityButton.disabled =
                submitting;
        }
    );
}


/* ==================================================
   WHATSAPP WINDOW
================================================== */

function openWhatsAppWindow() {
    let whatsappWindow =
        null;


    try {
        /*
         * La ventana se abre sin URL en el mismo gesto del usuario.
         * Así el navegador la considera una ventana iniciada por el
         * usuario y no por una tarea asíncrona posterior.
         */
        whatsappWindow =
            window.open(
                "",
                "_blank"
            );

    } catch (
    error
    ) {
        whatsappWindow =
            null;
    }


    if (
        !whatsappWindow
    ) {
        return null;
    }


    /*
     * Mientras esperamos la respuesta del servidor mostramos
     * contenido en lugar de dejar la pestaña completamente vacía.
     */
    try {
        whatsappWindow.document.title =
            "Loop & Love | WhatsApp";

        whatsappWindow.document.body.innerHTML = `
            <div style="
                min-height:100vh;
                display:flex;
                align-items:center;
                justify-content:center;
                padding:24px;
                margin:0;
                background:#FCF7F2;
                color:#614438;
                font-family:Arial,sans-serif;
                text-align:center;
            ">
                <div>
                    <strong>
                        Preparando tu pedido...
                    </strong>
                    <p>
                        Estamos preparando el mensaje para WhatsApp.
                    </p>
                </div>
            </div>
        `;

    } catch (
    error
    ) {
        /*
         * Si el navegador no permite modificar el documento de la
         * ventana temporal, la navegación posterior sigue siendo válida.
         */
    }


    return whatsappWindow;
}


/* ==================================================
   WHATSAPP MESSAGE
================================================== */

function buildWhatsAppMessage(
    order
) {
    const items =
        Array.isArray(
            order?.items
        )
            ? order.items
            : [];


    const lines = [
        "Hola, quiero enviar el siguiente pedido a Loop & Love.",
        "",
        `Pedido #${order.id}`,
        "",
        "*Productos:*",
    ];


    items.forEach(
        (
            item
        ) => {
            lines.push(
                `• ${item.name} x ${item.quantity} — ${formatOrderPrice(item.line_total)}`
            );
        }
    );


    lines.push(
        "",
        `*Total:* ${formatOrderPrice(order.total)}`,
        "",
        "*Datos del cliente:*",
        `Nombre: ${order.name}`,
        `Teléfono: ${order.phone}`,
        `Ciudad: ${order.city}`
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


    return lines.join(
        "\n"
    );
}


function buildWhatsAppUrl(
    number,
    order
) {
    const message =
        buildWhatsAppMessage(
            order
        );


    return (
        `https://wa.me/${number}?text=${encodeURIComponent(message)}`
    );
}


/* ==================================================
   RESET
================================================== */

function resetOrderForm() {
    const form =
        getOrderElement(
            "catalog-order-form"
        );


    if (form) {
        form.reset();
    }
}


/* ==================================================
   SUBMIT
================================================== */

async function submitCatalogOrder(
    event
) {
    event.preventDefault();


    if (
        orderState.submitting
    ) {
        return;
    }


    clearOrderFeedback();


    const form =
        getOrderElement(
            "catalog-order-form"
        );


    if (!form) {
        return;
    }


    const items =
        getOrderCartItems();


    if (!items.length) {
        showOrderFeedback(
            "Agrega al menos un producto antes de enviar el pedido."
        );

        return;
    }


    if (
        !form.reportValidity()
    ) {
        return;
    }


    const whatsappNumber =
        getWhatsAppNumber();


    if (
        !isValidWhatsAppNumber(
            whatsappNumber
        )
    ) {
        showOrderFeedback(
            "El número de WhatsApp no está configurado correctamente. Intenta nuevamente más tarde."
        );

        return;
    }


    /*
     * Abrimos la ventana antes del fetch.
     *
     * Esto es importante porque después de await fetch()
     * el navegador puede considerar la apertura un popup
     * no iniciado por el usuario.
     */
    const whatsappWindow =
        openWhatsAppWindow();


    setOrderSubmitting(
        true
    );


    const payload = {
        name:
            getOrderElement(
                "order-customer-name"
            )?.value ||
            "",

        phone:
            getOrderElement(
                "order-customer-phone"
            )?.value ||
            "",

        city:
            getOrderElement(
                "order-customer-city"
            )?.value ||
            "",

        observations:
            getOrderElement(
                "order-customer-observations"
            )?.value ||
            null,

        items,
    };


    try {
        const response =
            await fetch(
                ORDER_API_URL,
                {
                    method:
                        "POST",

                    headers: {
                        Accept:
                            "application/json",

                        "Content-Type":
                            "application/json",
                    },

                    body:
                        JSON.stringify(
                            payload
                        ),
                }
            );


        const data =
            await parseOrderResponse(
                response
            );


        if (
            !response.ok ||
            data?.success !== true ||
            !data?.data
        ) {
            throw new Error(
                getOrderApiError(
                    data,
                    "No fue posible registrar el pedido."
                )
            );
        }


        const order =
            data.data;


        const whatsappUrl =
            buildWhatsAppUrl(
                whatsappNumber,
                order
            );


        /*
         * El pedido ya está confirmado y almacenado.
         *
         * El carrito se limpia para evitar que el cliente
         * pueda reenviar accidentalmente el mismo pedido.
         */
        if (
            typeof clearCart ===
            "function"
        ) {
            clearCart();

        } else {
            window.localStorage.removeItem(
                "loop_and_love.b2b_cart"
            );
        }


        resetOrderForm();


        /*
         * order-feedback está fuera de #cart-list.
         * Por eso sigue visible aunque clearCart() haya
         * ocultado el carrito.
         */
        if (
            whatsappWindow
        ) {
            showOrderFeedback(
                `Pedido #${order.id} registrado correctamente. WhatsApp está listo para enviar la solicitud.`,
                "success"
            );

            try {
                whatsappWindow.location.replace(
                    whatsappUrl
                );

            } catch (
            error
            ) {
                /*
                 * Si la navegación de la ventana falla,
                 * ofrecemos el enlace manual.
                 */
                showOrderFeedback(
                    `Pedido #${order.id} registrado correctamente. Abre WhatsApp para enviar la solicitud.`,
                    "success",
                    whatsappUrl
                );
            }

        } else {
            /*
             * El navegador bloqueó el popup.
             * El pedido sigue siendo válido y el cliente
             * puede abrir WhatsApp mediante el enlace.
             */
            showOrderFeedback(
                `Pedido #${order.id} registrado correctamente. El navegador bloqueó la ventana de WhatsApp.`,
                "success",
                whatsappUrl
            );
        }

    } catch (
    error
    ) {

        if (
            whatsappWindow &&
            !whatsappWindow.closed
        ) {
            try {
                whatsappWindow.close();

            } catch (
            closeError
            ) {
                /*
                 * No interrumpimos el tratamiento del error
                 * si el navegador no permite cerrar la ventana.
                 */
            }
        }


        showOrderFeedback(
            error instanceof Error
                ? error.message
                : "No fue posible registrar el pedido."
        );

    } finally {
        setOrderSubmitting(
            false
        );
    }
}


/* ==================================================
   INITIALIZE
================================================== */

function setupCatalogOrderForm() {
    const form =
        getOrderElement(
            "catalog-order-form"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        (
            event
        ) => {
            void submitCatalogOrder(
                event
            );
        }
    );
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        setupCatalogOrderForm();
    }
);