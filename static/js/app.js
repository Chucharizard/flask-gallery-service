// Funcionalidad JavaScript para la interfaz web de Flask

// Función que se ejecuta cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Mejorar la experiencia de usuario para los mensajes flash
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            setTimeout(function() {
                bsAlert.close();
            }, 5000);
        });
    }, 2000);
    
    // Configurar la vista previa de imágenes al cargar
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', previewImage);
    }
    
    // Añadir confirmación para eliminaciones
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    if (deleteButtons) {
        deleteButtons.forEach(button => {
            button.addEventListener('click', confirmAction);
        });
    }
    
    // Inicializar efecto de lazycarga para imágenes
    lazyLoadImages();
});

// Función para previsualizar la imagen antes de subirla
function previewImage(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Verificar que sea una imagen
    if (!file.type.match('image.*')) {
        alert('Por favor selecciona una imagen válida (JPEG, PNG, GIF)');
        e.target.value = '';
        return;
    }
    
    // Verificar tamaño (máximo 10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('La imagen es demasiado grande. El tamaño máximo es 10MB.');
        e.target.value = '';
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('preview');
        if (preview) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            
            // Ocultar el mensaje de "sin vista previa"
            const noPreview = document.getElementById('no-preview');
            if (noPreview) {
                noPreview.style.display = 'none';
            }
        }
    }
    
    reader.readAsDataURL(file);
}

// Función para confirmar acciones destructivas
function confirmAction(e) {
    if (!confirm(e.target.getAttribute('data-confirm') || '¿Estás seguro?')) {
        e.preventDefault();
        return false;
    }
    return true;
}

// Función para implementar carga diferida de imágenes
function lazyLoadImages() {
    // Comprobar si el navegador soporta IntersectionObserver
    if ('IntersectionObserver' in window) {
        let lazyImageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    let lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImage.classList.remove('lazy');
                    lazyImageObserver.unobserve(lazyImage);
                }
            });
        });

        let lazyImages = document.querySelectorAll('img.lazy');
        lazyImages.forEach(function(lazyImage) {
            lazyImageObserver.observe(lazyImage);
        });
    } else {
        // Fallback para navegadores que no soportan IntersectionObserver
        let lazyImages = document.querySelectorAll('img.lazy');
        lazyImages.forEach(function(img) {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
        });
    }
}

// Función para actualizar la interfaz en tiempo real (para futura implementación con WebSockets)
function updateGalleryInRealtime() {
    // Esta función se puede implementar en el futuro para actualizar 
    // la galería en tiempo real cuando nuevas imágenes sean añadidas
    console.log('Actualización en tiempo real preparada para implementación futura');
}






// Fix for iOS Safari 100vh issue
function setVhVariable() {
  let vh = window.innerHeight * 0.01;
  document.documentElement.style.setProperty('--vh', `${vh}px`);
}

// Set initially and on resize
setVhVariable();
window.addEventListener('resize', setVhVariable);

// Add auto-dark-mode class if user prefers dark mode
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
  document.body.classList.add('auto-dark-mode');
}

// Optional: Track dark mode changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
  document.body.classList.toggle('auto-dark-mode', event.matches);
});

// Improve touch performance on mobile - prevent 300ms delay
document.addEventListener('touchstart', function() {}, {passive: true});
