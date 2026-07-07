import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../index.css';

const Login = () => {
    const canvasRef = useRef(null);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();
    const [error, setError] = useState('');

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        let particles = [];

        class Particle {
            constructor(x, y) {
                this.x = x;
                this.y = y;
                this.size = Math.random() * 5 + 1;
                this.speedX = Math.random() * 3 - 1.5;
                this.speedY = Math.random() * 3 - 1.5;
                this.color = 'rgba(255, 255, 255, 0.5)';
            }
            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                if (this.size > 0.2) this.size -= 0.1;
            }
            draw() {
                ctx.fillStyle = this.color;
                ctx.strokeStyle = this.color;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
            }
        }

        const createParticles = (e) => {
            const xPos = e.clientX;
            const yPos = e.clientY;
            for (let i = 0; i < 5; i++) {
                particles.push(new Particle(xPos, yPos));
            }
        };

        const animateParticles = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            for (let i = 0; i < particles.length; i++) {
                particles[i].update();
                particles[i].draw();
                if (particles[i].size <= 0.3) {
                    particles.splice(i, 1);
                    i--;
                }
            }
            requestAnimationFrame(animateParticles);
        };

        window.addEventListener('mousemove', createParticles);
        animateParticles();

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('mousemove', createParticles);
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('/api/login', { username, password });

            if (response.data.status === 'success') {
                localStorage.setItem('loggedin', 'true');
                localStorage.setItem('username', username);
                navigate('/home');
            } else {
                setError(response.data.message || 'Invalid credentials or Login failed');
            }
        } catch (err) {
            console.error(err);
            setError('An error occurred during login');
        }
    };

    return (
        <div style={{ position: 'relative', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' }}>
            <canvas ref={canvasRef} style={{ position: 'absolute', top: 0, left: 0, zIndex: -1 }} />

            <div style={{ position: 'absolute', top: '10%', textAlign: 'center', width: '100%' }}>
                <h1 style={{ color: 'white', fontSize: '3rem', textShadow: '2px 2px 4px rgba(0,0,0,0.4)' }}>SMART SHOPPING</h1>
            </div>

            <div className="card fade-in" style={{ width: '100%', maxWidth: '400px', backgroundColor: 'white' }}>
                <h2 style={{ textAlign: 'center', color: '#e7492d', marginBottom: '30px' }}>Login</h2>
                {error && <div style={{ color: 'red', textAlign: 'center', marginBottom: '10px' }}>{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label>Username</label>
                        <input
                            type="text"
                            required
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>
                    <div className="input-group">
                        <label>Password</label>
                        <input
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Login</button>
                </form>

                <div style={{ textAlign: 'center', marginTop: '20px' }}>
                    Don't have an account? <Link to="/register">Register here</Link>
                </div>
            </div>
        </div>
    );
};

export default Login;
