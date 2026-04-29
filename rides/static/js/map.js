/* ============================================================================
   LEAFLET MAP FUNCTIONS
   ============================================================================ */

// Create Leaflet map with OSM
function createMap(elementId, center = [51.505, -0.09], zoom = 13) {
    const map = L.map(elementId).setView(center, zoom);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 2,
        crossOrigin: true
    }).addTo(map);
    
    return map;
}

// Create marker with custom color
function createMarker(map, lat, lng, title, color = 'blue', popupContent = null) {
    const colors = {
        'red': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        'green': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        'blue': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
        'orange': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
        'yellow': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png',
        'violet': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
        'grey': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png',
        'black': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-black.png'
    };
    
    const icon = L.icon({
        iconUrl: colors[color] || colors['blue'],
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41],
        shadowAnchor: [12, 41]
    });
    
    const marker = L.marker([lat, lng], {
        icon: icon,
        title: title
    }).addTo(map);
    
    if (popupContent) {
        marker.bindPopup(popupContent);
    }
    
    return marker;
}

// Draw route line between two points
function drawRoute(map, fromLat, fromLng, toLat, toLng, color = '#007bff', weight = 3) {
    const latlngs = [
        [fromLat, fromLng],
        [toLat, toLng]
    ];
    
    const polyline = L.polyline(latlngs, {
        color: color,
        weight: weight,
        opacity: 0.8,
        dashArray: '5, 10'
    }).addTo(map);
    
    // Fit map to bounds
    map.fitBounds(polyline.getBounds());
    
    return polyline;
}

// Load GeoJSON and add to map
function loadGeoJSONData(map, url) {
    return fetch(url)
        .then(response => response.json())
        .then(data => {
            const markers = [];
            
            data.features.forEach(feature => {
                const props = feature.properties;
                const lat = feature.geometry.coordinates[1];
                const lng = feature.geometry.coordinates[0];
                
                const color = props.marker_type === 'from' ? 'green' : 'red';
                
                const popupContent = `
                    <div class="map-popup">
                        <strong>${props.title}</strong><br>
                        <small><strong>From:</strong> ${props.from_location}</small><br>
                        <small><strong>To:</strong> ${props.to_location}</small><br>
                        <small><strong>Driver:</strong> ${props.driver}</small><br>
                        <small><strong>Time:</strong> ${new Date(props.datetime).toLocaleString()}</small><br>
                        <small><strong>Seats:</strong> ${props.seats}</small><br>
                        <a href="/rides/${props.ride_id}/">View Ride</a>
                    </div>
                `;
                
                const marker = createMarker(map, lat, lng, props.title, color, popupContent);
                markers.push(marker);
            });
            
            return markers;
        });
}

// Fit all markers in view
function fitMarkersInView(map, markers) {
    if (markers.length === 0) return;
    
    const latlngs = markers.map(marker => marker.getLatLng());
    const bounds = L.latLngBounds(latlngs);
    map.fitBounds(bounds, { padding: [50, 50] });
}

// Clear all markers from map (except tile layer)
function clearMapMarkers(map) {
    map.eachLayer(layer => {
        if (layer instanceof L.Marker || layer instanceof L.Polyline) {
            map.removeLayer(layer);
        }
    });
}
