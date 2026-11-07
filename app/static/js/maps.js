// Mapas de la Suite con Leaflet: selector de ubicación (formulario de paquetes) y mapa de paquetes.
const CARTAGENA = [10.3997, -75.5144];

// El mapa se limita a Cartagena: no se puede mover ni alejar fuera de sus límites (data-bounds)
const createMap = (element, center, zoom) => {
    const bounds = JSON.parse(element.dataset.bounds);
    const map = L.map(element, { maxBounds: bounds, maxBoundsViscosity: 1, minZoom: 11 }).setView(center, zoom);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
    return map;
};

// ---- Selector de ubicación: al tocar el mapa se marca el punto y se guardan lat y lng ----
const value = (id) => document.getElementById(id).value;

// Con las dos ubicaciones elegidas se calcula la distancia en línea recta (se puede corregir a mano)
const updateDistance = () => {
    const ids = ['origin_lat', 'origin_lng', 'destination_lat', 'destination_lng'];
    if (!ids.every((id) => value(id))) return;
    const meters = L.latLng(value('origin_lat'), value('origin_lng')).distanceTo([value('destination_lat'), value('destination_lng')]);
    document.getElementById('distance_km').value = (meters / 1000).toFixed(1);
};

// Dirección del punto (geocodificación inversa de OpenStreetMap): calle, número y barrio
const addressOf = async ({ lat, lng }) => {
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&accept-language=es&lat=${lat}&lon=${lng}`);
        const { address = {}, display_name: name = '' } = await response.json();
        const street = [address.road, address.house_number].filter(Boolean).join(' ');
        return [street, address.suburb || address.neighbourhood].filter(Boolean).join(', ') || name;
    } catch {
        return ''; // sin conexión: se escribe la dirección a mano
    }
};

document.querySelectorAll('[data-map-picker]').forEach((element) => {
    const lat = document.getElementById(element.dataset.lat);
    const lng = document.getElementById(element.dataset.lng);
    const address = document.getElementById(element.dataset.address);
    const saved = lat.value && lng.value;
    const map = createMap(element, saved ? [lat.value, lng.value] : CARTAGENA, saved ? 15 : 12);
    let marker = saved ? L.marker([lat.value, lng.value]).addTo(map) : null;

    map.on('click', ({ latlng }) => {
        if (!map.options.maxBounds.contains(latlng)) return; // fuera de Cartagena
        marker = marker ? marker.setLatLng(latlng) : L.marker(latlng).addTo(map);
        lat.value = latlng.lat.toFixed(6);
        lng.value = latlng.lng.toFixed(6);
        updateDistance();
        addressOf(latlng).then((text) => { if (text) address.value = text.slice(0, 255); });
    });
});

// ---- Paquetes en el mapa: círculo vacío = origen, círculo lleno = destino (color según el estado) ----
const css = getComputedStyle(document.documentElement);
const tones = { pending: 'amber', picked_up: 'sky', delivered: 'mint', issue: 'rose' };
const colorOf = (status) => css.getPropertyValue(`--color-${tones[status]}-ink`).trim();

// Ventana que se abre al tocar un punto
const popupOf = (p, place) => `
    <div class="min-w-44">
        <a href="${p.url}" class="text-sm font-extrabold">${p.number}</a>
        <span class="ml-1 rounded-full px-2 py-0.5 text-[11px] font-bold" style="background:${colorOf(p.status)}1f;color:${colorOf(p.status)}">${p.label}</span>
        <div class="mt-2 text-xs text-muted">${place === 'Origen' ? 'Origen' : 'Destino'}</div>
        <div class="text-xs font-semibold">${place === 'Origen' ? p.origin : p.destination}</div>
    </div>`;

// Dibuja la línea y los dos puntos de un paquete dentro de una capa
const drawPackage = (layer, p) => {
    const color = colorOf(p.status);
    L.polyline([p.from, p.to], { color, weight: 3, opacity: 0.5, dashArray: '2 8', lineCap: 'round' }).addTo(layer);
    L.circleMarker(p.from, { radius: 7, color, weight: 3, fillColor: '#fff', fillOpacity: 1 }).bindPopup(popupOf(p, 'Origen')).bindTooltip('Origen').addTo(layer);
    L.circleMarker(p.to, { radius: 8, color, weight: 3, fillColor: color, fillOpacity: 0.95 }).bindPopup(popupOf(p, 'Destino')).bindTooltip('Destino').addTo(layer);
};

// Mapa general de la Suite (con filtro y conteo por estado)
const mapElement = document.getElementById('packagesMap');
if (mapElement) {
    const packages = JSON.parse(document.getElementById('map-data').textContent);
    const map = createMap(mapElement, CARTAGENA, 12);
    L.control.scale({ imperial: false }).addTo(map);
    const layer = L.featureGroup().addTo(map); // featureGroup permite calcular el área que ocupan los puntos
    const filter = document.getElementById('mapFilter');

    const draw = () => {
        layer.clearLayers();
        const shown = packages.filter((p) => filter.value === 'all' || (filter.value === 'active' ? p.status !== 'delivered' : p.status === filter.value));
        shown.forEach((p) => drawPackage(layer, p));
        document.getElementById('mapCount').textContent = shown.length;
        document.querySelectorAll('[data-count]').forEach((el) => { el.textContent = shown.filter((p) => p.status === el.dataset.count).length; });
        if (shown.length) map.fitBounds(layer.getBounds().pad(0.15), { maxZoom: 15 }); // acerca el mapa a los puntos
    };

    filter.addEventListener('change', draw);
    draw();
}

// Mapa del detalle de un paquete: solo su origen y su destino
const detailElement = document.getElementById('packageMap');
if (detailElement) {
    const map = createMap(detailElement, CARTAGENA, 12);
    const layer = L.featureGroup().addTo(map);
    drawPackage(layer, JSON.parse(detailElement.dataset.package));
    map.fitBounds(layer.getBounds().pad(0.3), { maxZoom: 16 });
}
