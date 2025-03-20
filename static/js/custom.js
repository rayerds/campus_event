document.addEventListener('DOMContentLoaded', () => {
    const createEventBtn = document.querySelector('a[href*="create_event"]');
    if (createEventBtn) {
        createEventBtn.addEventListener('mouseover', () => {
            createEventBtn.style.boxShadow = '0 0 8px rgba(0, 123, 255, 0.6)';
        });
        createEventBtn.addEventListener('mouseout', () => {
            createEventBtn.style.boxShadow = 'none';
        });
    }
});
