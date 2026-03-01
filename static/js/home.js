// =============================================
// LIFELINE CARE — HOME PAGE JAVASCRIPT
// =============================================

document.addEventListener('DOMContentLoaded', function () {

    // ---- Navbar scroll effect ----
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 50);
    });

    // ---- Active nav link on scroll ----
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            if (window.scrollY >= section.offsetTop - 100) {
                current = section.getAttribute('id');
            }
        });
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    });

    // ---- Hamburger / Mobile menu ----
    const hamburger = document.getElementById('hamburger');
    const mobileMenu = document.getElementById('mobileMenu');

    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'mobile-overlay';
    document.body.appendChild(overlay);

    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        mobileMenu.classList.toggle('open');
        overlay.classList.toggle('show');
        document.body.style.overflow = mobileMenu.classList.contains('open') ? 'hidden' : '';
    });

    overlay.addEventListener('click', closeMobileMenu);

    // ---- Stats Counter Animation ----
    const statNumbers = document.querySelectorAll('.stat-number');
    const countObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                countObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(num => countObserver.observe(num));

    function animateCounter(el) {
        const target = parseInt(el.getAttribute('data-target'));
        const duration = 2000;
        const step = target / (duration / 16);
        let current = 0;
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            el.textContent = Math.floor(current).toLocaleString() + '+';
        }, 16);
    }

    // ---- Scroll reveal animations ----
    const revealEls = document.querySelectorAll('.feature-card, .spec-card, .step-card, .testimonial-card, .stat-item');
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, i * 60);
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    revealEls.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(24px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        revealObserver.observe(el);
    });

    // ---- Testimonials Carousel ----
    const track = document.getElementById('testimonialsTrack');
    const cards = track.querySelectorAll('.testimonial-card');
    const dotsContainer = document.getElementById('tDots');
    let currentIndex = 0;
    const cardWidth = cards[0].offsetWidth + 24; // card + gap

    // Build dots
    cards.forEach((_, i) => {
        const dot = document.createElement('div');
        dot.className = 'tdot' + (i === 0 ? ' active' : '');
        dot.addEventListener('click', () => goToSlide(i));
        dotsContainer.appendChild(dot);
    });

    function goToSlide(index) {
        currentIndex = Math.max(0, Math.min(index, cards.length - 1));
        track.scrollLeft = currentIndex * cardWidth;
        document.querySelectorAll('.tdot').forEach((d, i) => {
            d.classList.toggle('active', i === currentIndex);
        });
    }

    document.getElementById('tNext').addEventListener('click', () => {
        goToSlide(currentIndex < cards.length - 1 ? currentIndex + 1 : 0);
    });

    document.getElementById('tPrev').addEventListener('click', () => {
        goToSlide(currentIndex > 0 ? currentIndex - 1 : cards.length - 1);
    });

    // Auto-advance
    setInterval(() => {
        goToSlide(currentIndex < cards.length - 1 ? currentIndex + 1 : 0);
    }, 5000);

    // ---- Slot selection in hero card ----
    document.querySelectorAll('.slot').forEach(slot => {
        slot.addEventListener('click', function () {
            document.querySelectorAll('.slot').forEach(s => s.classList.remove('active'));
            this.classList.add('active');
        });
    });

});

// Global function for mobile menu close (called from HTML onclick)
function closeMobileMenu() {
    const hamburger = document.getElementById('hamburger');
    const mobileMenu = document.getElementById('mobileMenu');
    const overlay = document.querySelector('.mobile-overlay');
    hamburger.classList.remove('active');
    mobileMenu.classList.remove('open');
    if (overlay) overlay.classList.remove('show');
    document.body.style.overflow = '';
}