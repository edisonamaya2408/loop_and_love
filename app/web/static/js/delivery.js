"use strict";

(() => {
    const state = {
        map: null,
        marker: null,
        config: null,
        selected: null,
        quote: null,
        timer: null,
        sequence: 0,
    };

    const element = (id) => (
        document.getElementById(id)
    );

    function refreshMapSize() {
        if (!state.map) {
            return;
        }

        /*
         * Esperar dos ciclos de renderizado para que el navegador
         * aplique las dimensiones del contenedor del carrito.
         */
        window.requestAnimationFrame(() => {
            window.requestAnimationFrame(() => {
                const mapElement = element(
                    "delivery-destination-map"
                );

                if (
                    !state.map ||
                    !mapElement ||
                    mapElement.clientWidth === 0 ||
                    mapElement.clientHeight === 0
                ) {
                    return;
                }

                state.map.invalidateSize({
                    pan: false,
                });
            });
        });
    }

    function formatCOP(value) {
        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "No disponible";
        }

        return new Intl.NumberFormat(
            "es-CO",
            {
                style: "currency",
                currency: "COP",
                maximumFractionDigits: 0,
            }
        ).format(number);
    }

    function showFeedback(message, type = "info") {
        const feedback = element(
            "delivery-quote-feedback"
        );

        if (!feedback) {
            return;
        }

        feedback.textContent = message;
        feedback.dataset.type = type;
    }

    function clearQuote() {
        state.quote = null;

        const summary = element(
            "delivery-quote-summary"
        );

        if (summary) {
            summary.hidden = true;
        }
    }

    function refreshCartSummary() {
        if (
            !state.quote ||
            state.quote.sequence !== state.sequence
        ) {
            clearQuote();
            return;
        }

        const subtotal = (
            typeof getCartTotal === "function"
                ? Number(getCartTotal())
                : NaN
        );

        const deliveryFee = Number(
            state.quote.deliveryFee
        );

        if (
            !Number.isFinite(subtotal) ||
            !Number.isFinite(deliveryFee)
        ) {
            clearQuote();

            showFeedback(
                "No fue posible calcular el total del pedido.",
                "error"
            );

            return;
        }

        const subtotalElement = element(
            "delivery-quote-subtotal"
        );

        const feeElement = element(
            "delivery-quote-fee"
        );

        const totalElement = element(
            "delivery-quote-total"
        );

        if (subtotalElement) {
            subtotalElement.textContent = formatCOP(
                subtotal
            );
        }

        if (feeElement) {
            feeElement.textContent = formatCOP(
                deliveryFee
            );
        }

        if (totalElement) {
            totalElement.textContent = formatCOP(
                subtotal + deliveryFee
            );
        }

        const summary = element(
            "delivery-quote-summary"
        );

        if (summary) {
            summary.hidden = false;
        }
    }

    async function requestQuote(
        latitude,
        longitude,
        sequence
    ) {
        try {
            const response = await fetch(
                "/api/delivery/quote",
                {
                    method: "POST",
                    headers: {
                        Accept: "application/json",
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        latitude,
                        longitude,
                    }),
                }
            );

            const body = await response.json().catch(
                () => null
            );

            // Ignorar respuestas correspondientes a puntos
            // que el usuario ya cambió en el mapa.
            if (sequence !== state.sequence) {
                return;
            }

            if (
                response.status === 422 ||
                body?.error?.code ===
                "DELIVERY_OUT_OF_COVERAGE"
            ) {
                clearQuote();

                showFeedback(
                    "Esta ubicación está fuera de la cobertura de entrega.",
                    "error"
                );

                return;
            }

            if (
                response.status === 503 ||
                body?.error?.code ===
                "DELIVERY_NOT_CONFIGURED"
            ) {
                clearQuote();

                showFeedback(
                    "El servicio de domicilio no está disponible en este momento.",
                    "error"
                );

                return;
            }

            if (
                !response.ok ||
                body?.success !== true ||
                !body?.data
            ) {
                throw new Error(
                    body?.error?.message ||
                    "No fue posible calcular el domicilio."
                );
            }

            const fee = Number(
                body.data.delivery_fee
            );

            if (
                !Number.isFinite(fee) ||
                fee < 0
            ) {
                throw new Error(
                    "El servidor devolvió una tarifa de domicilio inválida."
                );
            }

            state.quote = {
                sequence,
                deliveryFee: body.data.delivery_fee,
            };

            refreshCartSummary();

            showFeedback(
                "Domicilio calculado. El servidor lo validará nuevamente al registrar el pedido."
            );

        } catch (error) {
            if (sequence !== state.sequence) {
                return;
            }

            clearQuote();

            showFeedback(
                error instanceof Error
                    ? error.message
                    : "No fue posible calcular el domicilio.",
                "error"
            );
        }
    }

    function selectDestination(
        latitude,
        longitude
    ) {
        if (
            !Number.isFinite(latitude) ||
            !Number.isFinite(longitude) ||
            latitude < -90 ||
            latitude > 90 ||
            longitude < -180 ||
            longitude > 180
        ) {
            clearQuote();

            showFeedback(
                "La ubicación seleccionada no es válida.",
                "error"
            );

            return;
        }

        state.selected = {
            latitude: Number(latitude.toFixed(7)),
            longitude: Number(longitude.toFixed(7)),
        };

        element(
            "delivery-destination-latitude"
        ).value = String(
            state.selected.latitude
        );

        element(
            "delivery-destination-longitude"
        ).value = String(
            state.selected.longitude
        );

        state.sequence += 1;

        const sequence = state.sequence;
        const selected = { ...state.selected };

        clearQuote();

        showFeedback("Calculando domicilio…");

        if (state.timer !== null) {
            window.clearTimeout(state.timer);
        }

        state.timer = window.setTimeout(
            () => {
                void requestQuote(
                    selected.latitude,
                    selected.longitude,
                    sequence
                );
            },
            350
        );
    }

    function initializeMap(config) {
        if (!window.L) {
            throw new Error(
                "No fue posible cargar el mapa. Recarga la página e inténtalo nuevamente."
            );
        }

        const latitude = Number(
            config.map_center_latitude
        );

        const longitude = Number(
            config.map_center_longitude
        );

        if (
            !Number.isFinite(latitude) ||
            !Number.isFinite(longitude)
        ) {
            throw new Error(
                "La configuración pública del mapa no es válida."
            );
        }

        state.config = config;

        state.map = L.map(
            "delivery-destination-map"
        ).setView(
            [latitude, longitude],
            13
        );

        L.tileLayer(
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
                attribution:
                    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            }
        ).addTo(state.map);

        state.map.on(
            "click",
            (event) => {
                const point = event.latlng;

                if (state.marker) {
                    state.marker.setLatLng(point);
                } else {
                    state.marker = L.marker(
                        point
                    ).addTo(state.map);
                }

                selectDestination(
                    point.lat,
                    point.lng
                );
            }
        );

        refreshMapSize();

    }

    async function initialize() {
        if (!element("delivery-destination-map")) {
            return;
        }

        try {
            const response = await fetch(
                "/api/delivery/config",
                {
                    headers: {
                        Accept: "application/json",
                    },
                }
            );

            const body = await response.json().catch(
                () => null
            );

            if (
                !response.ok ||
                body?.success !== true ||
                !body?.data
            ) {
                throw new Error(
                    body?.error?.message ||
                    "El servicio de domicilio no está disponible."
                );
            }

            initializeMap(body.data);

        } catch (error) {
            showFeedback(
                error instanceof Error
                    ? error.message
                    : "No fue posible cargar el mapa.",
                "error"
            );
        }
    }

    function getCheckoutData() {
        if (
            !state.selected ||
            !state.quote ||
            state.quote.sequence !== state.sequence
        ) {
            return null;
        }

        return {
            delivery_latitude: state.selected.latitude,
            delivery_longitude: state.selected.longitude,
        };
    }

    function reset() {
        state.sequence += 1;

        if (state.timer !== null) {
            window.clearTimeout(state.timer);
            state.timer = null;
        }

        state.selected = null;
        clearQuote();

        if (state.marker && state.map) {
            state.map.removeLayer(state.marker);
            state.marker = null;
        }

        const latitudeInput = element(
            "delivery-destination-latitude"
        );

        const longitudeInput = element(
            "delivery-destination-longitude"
        );

        if (latitudeInput) {
            latitudeInput.value = "";
        }

        if (longitudeInput) {
            longitudeInput.value = "";
        }

        showFeedback("Selecciona un punto en el mapa.");
    }

    window.LoopAndLoveDelivery = Object.freeze({
        getCheckoutData,
        refreshCartSummary,
        reset,
    });

    window.addEventListener(
        "loopandlove:cart-updated",
        () => {
            refreshCartSummary();
            refreshMapSize();
        }
    );

    window.addEventListener(
        "resize",
        refreshMapSize
    );

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            void initialize();
        }
    );
})();