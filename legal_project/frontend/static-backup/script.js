// Mobile menu toggle
function toggleMobileMenu() {
    const navMenu = document.getElementById('navMenu');
    navMenu.classList.toggle('active');
}

// Close mobile menu when clicking a link
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
        const navMenu = document.getElementById('navMenu');
        navMenu.classList.remove('active');
    });
});

// Smooth scrolling for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 80,
                behavior: 'smooth'
            });
        }
    });
});

// Similar Cases Analyzer
function analyzeSimilarCases() {
    const fileInput = document.getElementById('caseFile');
    if (fileInput.files.length === 0) {
        alert("Please select a case file first.");
        return;
    }
    
    const fileName = fileInput.files[0].name;
    alert(`Analyzing ${fileName} for similar cases...`);
    
    // In a real app, this would call your MERN backend
    // For demo, we'll just show the existing results
    document.getElementById('similarCasesList').innerHTML = `
        <li>Case #2023-045: Similarity Score: 92%</li>
        <li>Case #2022-187: Similarity Score: 87%</li>
        <li>Case #2023-012: Similarity Score: 79%</li>
        <li>Case #2021-256: Similarity Score: 76%</li>
        <li>Case #2023-033: Similarity Score: 71%</li>
    `;
}

// Civil Compliance Auditor
function runComplianceAudit() {
    alert("Running compliance audit...");
    
    // In a real app, this would call your MERN backend
    // For demo, we'll update the score randomly
    const score = Math.floor(Math.random() * 20) + 75; // 75-95%
    document.querySelector('.compliance-score span').textContent = `${score}%`;
}

// Argument Strength Score Calculator
function calculateArgumentScore() {
    alert("Calculating argument strength...");
    
    // In a real app, this would call your MERN backend
    // For demo, we'll update with random scores
    const totalScore = (Math.random() * 2 + 7).toFixed(1); // 7.0-9.0
    document.querySelector('.score-value').textContent = totalScore;
    
    const precedentScore = Math.floor(Math.random() * 15) + 80; // 80-95%
    const statutoryScore = Math.floor(Math.random() * 25) + 65; // 65-90%
    const logicScore = Math.floor(Math.random() * 15) + 80; // 80-95%
    
    document.querySelectorAll('.score-fill')[0].style.width = `${precedentScore}%`;
    document.querySelectorAll('.score-fill')[1].style.width = `${statutoryScore}%`;
    document.querySelectorAll('.score-fill')[2].style.width = `${logicScore}%`;
    
    document.querySelectorAll('.score-bar-container span')[0].textContent = `${precedentScore}%`;
    document.querySelectorAll('.score-bar-container span')[1].textContent = `${statutoryScore}%`;
    document.querySelectorAll('.score-bar-container span')[2].textContent = `${logicScore}%`;
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Highlight active navigation link based on scroll position
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section');
        const navLinks = document.querySelectorAll('.nav-link');
        
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (scrollY >= (sectionTop - 100)) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
});