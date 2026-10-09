"use strict";

const adminAuditState = {
    page: 1,
    perPage: 25,
    total: 0,
    pages: 0,
    filters: {
        actor: "",
        action: "",
        entity_type: "",
        entity_id: "",
        date_from: "",
        date_to: "",
    },
    requestInFlight: false,
};

function getAuditElement(id) {
    return document.getElementById(id);
}

function setAuditMessage(message) {
    const element = getAuditElement(
        "admin-audit-message"
    );

    if (!element) return;

    element.hidden = !message;
    element.textContent = message || "";
}

function formatAuditDate(value) {
    if (!value) return "—";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "—";
    }

    return date.toLocaleString("es-CO", {
        dateStyle: "medium",
        timeStyle: "short",
    });
}

function auditActionLabel(action) {
    const labels = {
        "product.created": "Producto creado",
        "product.updated": "Producto actualizado",
        "product.activated": "Producto activado",
        "product.deactivated": "Producto desactivado",
        "product.status_changed": "Estado de producto cambiado",
        "product.image_deleted": "Imagen de producto eliminada",
        "product.deleted": "Producto eliminado",
        "category.created": "Categoría creada",
        "category.updated": "Categoría actualizada",
        "category.deleted": "Categoría eliminada",
        "admin_user.created": "Administrador creado",
        "admin_user.updated": "Administrador actualizado",
        "admin_user.activated": "Administrador activado",
        "admin_user.deactivated": "Administrador desactivado",
        "order.confirmed": "Pedido confirmado",
        "order.cancelled": "Pedido cancelado",
        "order.status_changed": "Estado de pedido cambiado",
    };

    return labels[action] || action || "Operación desconocida";
}

function auditEntityLabel(entityType) {
    const labels = {
        product: "Producto",
        category: "Categoría",
        order: "Pedido",
        admin_user: "Administrador",
    };

    return labels[entityType] || entityType || "—";
}

function appendTextCell(row, value, className) {
    const cell = document.createElement("td");

    if (className) {
        const strong = document.createElement("strong");
        strong.className = className;
        strong.textContent = value || "—";
        cell.append(strong);
    } else {
        cell.textContent = value || "—";
    }

    row.append(cell);
    return cell;
}

function renderAuditDetails(details, requestId) {
    const detailsElement = document.createElement("details");
    detailsElement.className = "admin-audit-details";

    const summary = document.createElement("summary");
    summary.textContent = "Ver detalles";

    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(
        {
            cambios: details || {},
            request_id: requestId || null,
        },
        null,
        2
    );

    detailsElement.append(summary, pre);

    const cell = document.createElement("td");
    cell.append(detailsElement);
    return cell;
}

function renderAuditEvents(events) {
    const body = getAuditElement(
        "admin-audit-table-body"
    );

    const empty = getAuditElement(
        "admin-audit-empty"
    );

    if (!body) return;

    body.replaceChildren();

    const normalizedEvents = Array.isArray(events)
        ? events
        : [];

    if (empty) {
        empty.hidden = normalizedEvents.length > 0;
    }

    normalizedEvents.forEach((event) => {
        const row = document.createElement("tr");

        appendTextCell(
            row,
            formatAuditDate(event.created_at)
        );

        const actorCell = document.createElement("td");
        const actorName = document.createElement("strong");
        actorName.textContent =
            event.actor_name || "Administrador desconocido";

        const actorEmail = document.createElement("small");
        actorEmail.textContent = event.actor_email || "Sin correo";

        actorCell.append(actorName, actorEmail);
        row.append(actorCell);

        const actionCell = document.createElement("td");
        const actionBadge = document.createElement("span");
        actionBadge.className = "admin-audit-action";
        actionBadge.textContent = auditActionLabel(event.action);
        actionCell.append(actionBadge);
        row.append(actionCell);

        appendTextCell(
            row,
            auditEntityLabel(event.entity_type)
        );

        appendTextCell(
            row,
            event.entity_id !== null &&
            event.entity_id !== undefined
                ? `#${event.entity_id}`
                : "—"
        );

        row.append(
            renderAuditDetails(
                event.details,
                event.request_id
            )
        );

        appendTextCell(
            row,
            event.ip_address || "—"
        );

        body.append(row);
    });

    const count = getAuditElement(
        "admin-audit-count"
    );

    if (count) {
        count.textContent =
            `${adminAuditState.total} evento` +
            `${adminAuditState.total === 1 ? "" : "s"}`;
    }
}

function updateAuditPagination(pagination) {
    const previous = getAuditElement(
        "admin-audit-prev"
    );

    const next = getAuditElement(
        "admin-audit-next"
    );

    const info = getAuditElement(
        "admin-audit-pagination-info"
    );

    adminAuditState.page = pagination?.page || 1;
    adminAuditState.perPage = pagination?.per_page || 25;
    adminAuditState.total = pagination?.total || 0;
    adminAuditState.pages = pagination?.pages || 0;

    if (previous) {
        previous.disabled = !pagination?.has_previous;
    }

    if (next) {
        next.disabled = !pagination?.has_next;
    }

    if (info) {
        info.textContent =
            `Página ${adminAuditState.page} de ` +
            `${adminAuditState.pages || 1}`;
    }

    const count = getAuditElement(
        "admin-audit-count"
    );

    if (count) {
        count.textContent =
            `${adminAuditState.total} evento` +
            `${adminAuditState.total === 1 ? "" : "s"}`;
    }
}

function buildAuditQuery() {
    const params = new URLSearchParams();

    params.set("page", String(adminAuditState.page));
    params.set("per_page", String(adminAuditState.perPage));

    Object.entries(adminAuditState.filters).forEach(
        ([key, value]) => {
            if (value) params.set(key, value);
        }
    );

    return params.toString();
}

async function loadAuditEvents() {
    if (adminAuditState.requestInFlight) return;

    adminAuditState.requestInFlight = true;

    const loading = getAuditElement(
        "admin-audit-loading"
    );

    const empty = getAuditElement(
        "admin-audit-empty"
    );

    const body = getAuditElement(
        "admin-audit-table-body"
    );

    if (loading) loading.hidden = false;
    if (empty) empty.hidden = true;
    if (body) body.replaceChildren();

    setAuditMessage("");

    try {
        const response = await adminFetch(
            `/api/admin/audit-logs?${buildAuditQuery()}`,
            {
                headers: {
                    Accept: "application/json",
                },
            }
        );

        const data = await parseJsonSafely(response);

        if (!response.ok) {
            throw new Error(getErrorMessage(data));
        }

        renderAuditEvents(data?.data);
        updateAuditPagination(data?.pagination);
    } catch (error) {
        if (
            error instanceof Error &&
            error.message === "La sesión ha expirado."
        ) {
            return;
        }

        setAuditMessage(
            error instanceof Error
                ? error.message
                : "No fue posible cargar la auditoría."
        );

        if (body) body.replaceChildren();
        if (empty) empty.hidden = true;
    } finally {
        adminAuditState.requestInFlight = false;
        if (loading) loading.hidden = true;
    }
}

function setupAuditFilters() {
    const form = getAuditElement(
        "admin-audit-filter-form"
    );

    const clearButton = getAuditElement(
        "admin-audit-clear-button"
    );

    if (!form) return;

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        adminAuditState.filters = {
            actor:
                getAuditElement("admin-audit-actor")?.value.trim() || "",
            action:
                getAuditElement("admin-audit-action")?.value || "",
            entity_type:
                getAuditElement("admin-audit-entity-type")?.value || "",
            entity_id:
                getAuditElement("admin-audit-entity-id")?.value.trim() || "",
            date_from:
                getAuditElement("admin-audit-date-from")?.value || "",
            date_to:
                getAuditElement("admin-audit-date-to")?.value || "",
        };

        if (
            adminAuditState.filters.date_from &&
            adminAuditState.filters.date_to &&
            adminAuditState.filters.date_from >
                adminAuditState.filters.date_to
        ) {
            setAuditMessage(
                "La fecha desde no puede ser posterior a la fecha hasta."
            );
            return;
        }

        adminAuditState.page = 1;
        void loadAuditEvents();
    });

    clearButton?.addEventListener("click", () => {
        form.reset();

        adminAuditState.filters = {
            actor: "",
            action: "",
            entity_type: "",
            entity_id: "",
            date_from: "",
            date_to: "",
        };

        adminAuditState.page = 1;
        void loadAuditEvents();
    });
}

function setupAuditPagination() {
    getAuditElement("admin-audit-prev")?.addEventListener(
        "click",
        () => {
            if (adminAuditState.page <= 1) return;

            adminAuditState.page -= 1;
            void loadAuditEvents();
        }
    );

    getAuditElement("admin-audit-next")?.addEventListener(
        "click",
        () => {
            if (
                adminAuditState.page >= adminAuditState.pages
            ) {
                return;
            }

            adminAuditState.page += 1;
            void loadAuditEvents();
        }
    );
}

function initializeAdminAudit() {
    if (!getAuditElement("admin-audit-table-body")) {
        return;
    }

    if (
        typeof getAdminToken !== "function" ||
        !getAdminToken()
    ) {
        redirectToLogin();
        return;
    }

    setupAuditFilters();
    setupAuditPagination();
    void loadAuditEvents();
}

document.addEventListener(
    "DOMContentLoaded",
    initializeAdminAudit
);