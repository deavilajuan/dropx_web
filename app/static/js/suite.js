// Comportamiento básico de la Suite: menú lateral, ventanas emergentes y contraseña visible.

// Menú lateral en móvil: está oculto a la izquierda (-translate-x-full); el botón lo muestra y tocar fuera lo oculta
const side = document.getElementById('side');
const menuBtn = document.getElementById('menuBtn');
if (side && menuBtn) {
    menuBtn.addEventListener('click', () => side.classList.toggle('-translate-x-full'));
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#side, #menuBtn')) side.classList.add('-translate-x-full');
    });
}

// Mensajes de éxito o información ([data-autoclose]): se ocultan solos a los 4 segundos
document.querySelectorAll('[data-autoclose]').forEach((alert) => {
    setTimeout(() => {
        alert.style.transition = 'opacity 0.5s';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
    }, 4000);
});

// Ventanas emergentes ([data-overlay]): se abren con data-open y se cierran con data-close, Escape o tocando el fondo
function openOverlay(overlay) {
    overlay.classList.remove('hidden');
    overlay.classList.add('flex');
    const first = overlay.querySelector('input, button');
    if (first) first.focus();
}

function closeOverlays() {
    document.querySelectorAll('[data-overlay]').forEach((o) => {
        o.classList.add('hidden');
        o.classList.remove('flex');
    });
}

document.addEventListener('click', (e) => {
    const opener = e.target.closest('[data-open]');
    if (opener) openOverlay(document.querySelector(opener.dataset.open));

    // Botón de editar: copia los datos del botón al formulario de la ventana
    const editor = e.target.closest('[data-edit]');
    if (editor) {
        const overlay = document.querySelector(editor.dataset.edit);
        overlay.querySelector('form').action = editor.dataset.action;
        overlay.querySelector('[name=name]').value = editor.dataset.name;
        overlay.querySelector('[name=email]').value = editor.dataset.email;
        overlay.querySelector('[name=phone]').value = editor.dataset.phone;
        overlay.querySelector('[name=password]').value = '';
        openOverlay(overlay);
    }

    if (e.target.closest('[data-close]') || e.target.matches('[data-overlay]')) closeOverlays();

    // Mostrar u ocultar la contraseña
    const toggle = e.target.closest('[data-toggle-password]');
    if (toggle) {
        const input = document.querySelector(toggle.dataset.togglePassword);
        input.type = input.type === 'password' ? 'text' : 'password';
        toggle.textContent = input.type === 'password' ? 'Mostrar' : 'Ocultar';
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeOverlays();
});

// Vista rápida de paquetes: los datos vienen en un JSON dentro de la página
const quickData = document.getElementById('quick-data');
if (quickData) {
    const packages = JSON.parse(quickData.textContent);
    // Texto y colores de cada estado (las clases se escriben completas para que Tailwind las encuentre)
    const labels = {
        pending: ['Pendiente', 'bg-amber text-amber-ink'],
        picked_up: ['Recogido', 'bg-sky text-sky-ink'],
        delivered: ['Entregado', 'bg-mint text-mint-ink'],
        issue: ['Con novedad', 'bg-rose text-rose-ink'],
    };

    // Texto seguro: se asigna con textContent para no interpretar HTML
    function rows(items) {
        return items.map(([label, value]) => {
            const row = document.createElement('div');
            row.className = 'mb-3 last:mb-0';
            const span = document.createElement('span');
            span.className = 'block text-xs text-muted';
            span.textContent = label;
            const b = document.createElement('b');
            b.className = 'block break-words font-bold';
            b.textContent = value || '—';
            row.append(span, b);
            return row;
        });
    }

    function pill(text, css) {
        const span = document.createElement('span');
        span.className = 'inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-bold before:size-1.5 before:rounded-full before:bg-current ' + css;
        span.textContent = text;
        return span;
    }

    document.addEventListener('click', (e) => {
        const button = e.target.closest('[data-quick]');
        if (!button) return;
        const p = packages[button.dataset.quick];
        document.getElementById('quick-title').textContent = p.number;
        document.getElementById('q-pills').replaceChildren(pill(...labels[p.status]), ...(p.isUrgent ? [pill('Urgente', 'bg-rose text-rose-ink')] : []));
        document.getElementById('q-from').replaceChildren(...rows([['Nombre', p.sender.name], ['Documento', p.sender.document], ['Teléfono', p.sender.phone], ['Dirección de origen', p.originAddress]]));
        document.getElementById('q-to').replaceChildren(...rows([['Nombre', p.receiver.name], ['Documento', p.receiver.document], ['Teléfono', p.receiver.phone], ['Dirección de destino', p.destinationAddress]]));
        document.getElementById('q-w').textContent = p.weightKg.toFixed(1) + ' kg';
        document.getElementById('q-km').textContent = p.distanceKm.toFixed(1) + ' km';
        document.getElementById('q-c').textContent = p.courier || 'Sin asignar';
        document.getElementById('q-edit').href = p.editUrl;
        document.getElementById('q-detail').href = p.detailUrl;
        openOverlay(document.getElementById('quick'));
    });
}
