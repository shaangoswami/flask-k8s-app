// Page Navigation
const navBtns = document.querySelectorAll('.nav-btn');
const pages = document.querySelectorAll('.page');

navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetPage = btn.dataset.page;
        
        // Update active button
        navBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Show target page
        pages.forEach(page => {
            page.classList.remove('active');
            if (page.id === targetPage) {
                page.classList.add('active');
            }
        });
    });
});

// Visitor Counter Animation
function animateCounter() {
    const counter = document.getElementById('visitor-count');
    const target = Math.floor(Math.random() * 1000) + 500;
    let current = 0;
    const increment = target / 100;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            counter.textContent = target;
            clearInterval(timer);
        } else {
            counter.textContent = Math.floor(current);
        }
    }, 20);
}

// Notification System
function showNotification(message = "Welcome! 🎉 Your Flask app is running perfectly!") {
    const notification = document.getElementById('notification');
    const notificationText = document.getElementById('notification-text');
    
    notificationText.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Form Submission
function handleSubmit(event) {
    event.preventDefault();
    showNotification("Message sent successfully! ✉️");
    event.target.reset();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    animateCounter();
});
