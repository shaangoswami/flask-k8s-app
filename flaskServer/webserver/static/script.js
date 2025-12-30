// Page Navigation
const navBtns = document.querySelectorAll('.nav-btn');
const pages = document.querySelectorAll('.page');

navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetPage = btn.dataset.page;
        
        navBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        pages.forEach(page => {
            page.classList.remove('active');
            if (page.id === targetPage) {
                page.classList.add('active');
            }
        });
    });
});

// Fetch real visitor count from API
async function loadVisitorCount() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        animateCounterTo(data.visitors);
    } catch (error) {
        console.error('Error loading stats:', error);
        animateCounterTo(0);
    }
}

// Animate counter to target value
function animateCounterTo(target) {
    const counter = document.getElementById('visitor-count');
    let current = 0;
    const increment = Math.max(1, target / 50);
    
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
function showNotification(message = "Welcome! 🎉 Your Flask app is running!") {
    const notification = document.getElementById('notification');
    const notificationText = document.getElementById('notification-text');
    
    notificationText.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Form Submission with API
async function handleSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = {
        name: form.querySelector('input[type="text"]').value,
        email: form.querySelector('input[type="email"]').value,
        message: form.querySelector('textarea').value
    };
    
    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification("Message sent successfully! ✉️");
            form.reset();
        } else {
            showNotification("Error sending message. Please try again.");
        }
    } catch (error) {
        console.error('Error submitting form:', error);
        showNotification("Error sending message. Please try again.");
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadVisitorCount();
});
