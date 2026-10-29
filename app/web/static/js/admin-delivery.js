"use strict";

function deliveryElement(id) {
    return document.getElementById(id);
}

function showDeliveryMessage(message, type = "success") {
    const element = deliveryElement("admin-delivery-message");

    if (!element) return;

    element.hidden = !message;
    element.textContent = message || "";
    element.dataset.type = type;
}

function createDeliveryMap(mapId, latitudeId, longitudeId) {
    const mapElement = deliveryElement(mapId);

    if (!mapElement || !window.L) return null;

    const latitudeInput = deliveryElement(latitudeId);
    const longitudeInput = deliveryElement(longitudeId);

    const defaultCenter = [4.5709, -74.2973];

    const existingLatitude = Number(latitudeInput.value);
    const existingLongitude = Number(longitudeInput.value);

    const hasCoordinates =
        latitudeInput.value !== "" &&
        longitudeInput.value !== "" &&
        Number.isFinite(existingLatitude) &&
        Number.isFinite(existingLongitude);

    const map = L.map(mapId).setView(
        hasCoordinates
            ? [existingLatitude, existingLongitude]
            : defaultCenter,
        hasCoordinates ? 15 : 5
    );

    L.tileLayer(
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }
    ).addTo(map);

    let marker = null;

    function setCoordinates(latitude, longitude, recenter = false) {
        latitudeInput.value = Number(latitude).toFixed(7);
        longitudeInput.value = Number(longitude).toFixed(7);

        const point = [Number(latitude), Number(longitude)];

        if (marker) {
            marker.setLatLng(point);
        } else {
            marker = L.marker(point).addTo(map);
        }

        if (recenter) {
            map.setView(point, 15);
        }
    }

    map.on("click", (event) => {
        setCoordinates(
            event.latlng.lat,
            event.latlng.lng
        );
    });

    if (hasCoordinates) {
        setCoordinates(existingLatitude, existingLongitude);
    }

    latitudeInput.addEventListener("change", () => {
        if (latitudeInput.value === "" || longitudeInput.value === "") {
            return;
        }

        const latitude = Number(latitudeInput.value);
        const longitude = Number(longitudeInput.value);

        if (
            Number.isFinite(latitude) &&
            Number.isFinite(longitude) &&
            latitude >= -90 &&
            latitude <= 90 &&
            longitude >= -180 &&
            longitude <= 180
        ) {
            setCoordinates(latitude, longitude, true);
        }
    });

    longitudeInput.addEventListener("change", () => {
        latitudeInput.dispatchEvent(new Event("change"));
    });

    return {
        map,
        setCoordinates,
    };
}

function setDeliveryFormValues(settings) {
    const fields = {
        "delivery-base-fee": settings.base_fee,
        "delivery-price-per-km": settings.price_per_km,
        "delivery-distance-factor": settings.distance_factor,
        "delivery-max-distance": settings.max_distance_km,
        "delivery-origin-latitude": settings.origin_latitude,
        "delivery-origin-longitude": settings.origin_longitude,
        "delivery-public-latitude": settings.public_map_center_latitude,
        "delivery-public-longitude": settings.public_map_center_longitude,
    };

    Object.entries(fields).forEach(([id, value]) => {
        deliveryElement(id).value = value ?? "";
    });
}

async function loadDeliverySettings() {
    const response = await adminFetch(
        "/api/admin/delivery-settings",
        {
            headers: { Accept: "application/json" },
        }
    );

    const data = await parseJsonSafely(response);

    if (!response.ok || data?.success !== true) {
        throw new Error(getErrorMessage(data));
    }

    setDeliveryFormValues(data.data);
}

async function saveDeliverySettings(event) {
    event.preventDefault();

    const form = deliveryElement("admin-delivery-settings-form");

    if (!form.reportValidity()) return;

    showDeliveryMessage("");

    const payload = {
        base_fee: deliveryElement("delivery-base-fee").value,
        price_per_km: deliveryElement("delivery-price-per-km").value,
        distance_factor: deliveryElement("delivery-distance-factor").value,
        max_distance_km: deliveryElement("delivery-max-distance").value,
        origin_latitude: deliveryElement("delivery-origin-latitude").value,
        origin_longitude: deliveryElement("delivery-origin-longitude").value,
        public_map_center_latitude: deliveryElement("delivery-public-latitude").value,
        public_map_center_longitude: deliveryElement("delivery-public-longitude").value,
    };

    const button = deliveryElement("delivery-settings-save");
    button.disabled = true;

    try {
        const response = await adminFetch(
            "/api/admin/delivery-settings",
            {
                method: "PUT",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            }
        );

        const data = await parseJsonSafely(response);

        if (!response.ok || data?.success !== true) {
            throw new Error(getErrorMessage(data));
        }

        setDeliveryFormValues(data.data);

        showDeliveryMessage(
            "Configuración de domicilio guardada correctamente."
        );

    } catch (error) {
        showDeliveryMessage(
            error instanceof Error
                ? error.message
                : "No fue posible guardar la configuración.",
            "error"
        );

    } finally {
        button.disabled = false;
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    if (!deliveryElement("admin-delivery-settings-form")) return;

    if (!getAdminToken()) {
        redirectToLogin();
        return;
    }

    deliveryElement("admin-delivery-settings-form").addEventListener(
        "submit",
        saveDeliverySettings
    );

    let originMap;
    let publicMap;

    try {
        await loadDeliverySettings();

        originMap = createDeliveryMap(
            "delivery-origin-map",
            "delivery-origin-latitude",
            "delivery-origin-longitude"
        );

        publicMap = createDeliveryMap(
            "delivery-public-center-map",
            "delivery-public-latitude",
            "delivery-public-longitude"
        );

        // Leaflet necesita recalcular sus dimensiones después de crear
        // los mapas dentro del layout administrativo.
        window.setTimeout(() => {
            originMap?.map.invalidateSize();
            publicMap?.map.invalidateSize();
        }, 0);

    } catch (error) {
        showDeliveryMessage(
            error instanceof Error
                ? error.message
                : "No fue posible cargar la configuración.",
            "error"
        );
    }
});