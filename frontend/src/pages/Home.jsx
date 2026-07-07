import React from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import BackgroundAnimation from '../components/BackgroundAnimation';
import '../index.css';

const Home = () => {
    const navigate = useNavigate();
    const username = localStorage.getItem('username') || 'User';

    const handleLogout = async () => {
        try {
            await axios.post('/api/logout');
            localStorage.removeItem('loggedin');
            localStorage.removeItem('username');
            navigate('/login');
        } catch (error) {
            console.error('Logout failed', error);
            // Force logout anyway on client side
            localStorage.removeItem('loggedin');
            navigate('/login');
        }
    };

    return (
        <div style={{ position: 'relative', height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
            <BackgroundAnimation />

            <div className="fade-in" style={{ textAlign: 'center', zIndex: 1 }}>
                <h1 style={{ color: 'white', fontSize: '3rem', marginBottom: '10px' }}>Welcome to Smart Shopping</h1>
                <h2 style={{ color: '#f2f6f7', fontSize: '2rem', marginBottom: '40px' }}>Welcome, {username}!</h2>

                <p style={{ color: '#ecf0f1', fontSize: '1.2rem', marginBottom: '40px' }}>We're glad to have you back!</p>

                <div className="button-container">
                    <button className="home-btn" onClick={() => navigate('/scanner')}>
                        <span>Scan Product</span>
                    </button>

                    <button className="home-btn" onClick={() => navigate('/search')}>
                        <span>Search Product</span>
                    </button>

                    <button className="home-btn" onClick={() => navigate('/dashboard')}>
                        <span>Manage Stock</span>
                    </button>

                    <button className="home-btn" onClick={() => navigate('/admin')}>
                        <span>Admin Panel</span>
                    </button>

                    <button className="btn-logout" onClick={handleLogout}>
                        Logout
                    </button>
                </div>
            </div>

            <footer style={{ position: 'absolute', bottom: '20px', color: 'white', textAlign: 'center', width: '100%' }}>
                <p>© 2024 Smart Shopping. All rights reserved.</p>
            </footer>
        </div>
    );
};

export default Home;
