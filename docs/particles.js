/**
 * Animated Dot Mesh Network Background
 * Creates floating particles with connecting lines (similar to OceanBase effect)
 */

class ParticleNetwork {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.numberOfParticles = 80;
        this.maxDistance = 150;
        this.mouse = { x: null, y: null, radius: 150 };

        this.init();
        this.animate();
        this.setupEventListeners();
    }

    init() {
        this.resize();
        this.createParticles();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = document.documentElement.scrollHeight;
    }

    createParticles() {
        this.particles = [];
        for (let i = 0; i < this.numberOfParticles; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                radius: Math.random() * 2 + 1
            });
        }
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.resize();
            this.createParticles();
        });

        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.x;
            this.mouse.y = e.y + window.scrollY;
        });

        window.addEventListener('mouseout', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });

        // Update canvas height on scroll
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                const newHeight = document.documentElement.scrollHeight;
                if (Math.abs(this.canvas.height - newHeight) > 100) {
                    this.canvas.height = newHeight;
                }
            }, 100);
        });
    }

    drawParticle(particle) {
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = 'rgba(99, 102, 241, 0.5)';
        this.ctx.fill();
        this.ctx.closePath();
    }

    drawLine(p1, p2, distance) {
        const opacity = 1 - (distance / this.maxDistance);
        this.ctx.beginPath();
        this.ctx.strokeStyle = `rgba(99, 102, 241, ${opacity * 0.3})`;
        this.ctx.lineWidth = 0.5;
        this.ctx.moveTo(p1.x, p1.y);
        this.ctx.lineTo(p2.x, p2.y);
        this.ctx.stroke();
        this.ctx.closePath();
    }

    updateParticle(particle) {
        // Mouse interaction
        if (this.mouse.x !== null && this.mouse.y !== null) {
            const dx = particle.x - this.mouse.x;
            const dy = particle.y - this.mouse.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < this.mouse.radius) {
                const angle = Math.atan2(dy, dx);
                const force = (this.mouse.radius - distance) / this.mouse.radius;
                particle.vx += Math.cos(angle) * force * 0.5;
                particle.vy += Math.sin(angle) * force * 0.5;
            }
        }

        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Boundary check
        if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
        if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;

        // Keep particles within bounds
        particle.x = Math.max(0, Math.min(this.canvas.width, particle.x));
        particle.y = Math.max(0, Math.min(this.canvas.height, particle.y));

        // Apply friction
        particle.vx *= 0.99;
        particle.vy *= 0.99;
    }

    animate() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Update and draw particles
        this.particles.forEach(particle => {
            this.updateParticle(particle);
            this.drawParticle(particle);
        });

        // Draw connections
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < this.maxDistance) {
                    this.drawLine(this.particles[i], this.particles[j], distance);
                }
            }
        }

        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('particle-canvas');
    if (canvas) {
        new ParticleNetwork(canvas);
    }
});
