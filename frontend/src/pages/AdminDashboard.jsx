import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../index.css';

// Admin Dashboard based on car.html
const AdminDashboard = () => {
    const [activeSection, setActiveSection] = useState('dashboard');
    const [stats, setStats] = useState({ products: 0, orders: 156, revenue: 45280, users: 1248 });
    const [sidebarOpen, setSidebarOpen] = useState(false);

    // Mock Product Data from HTML (Ideally fetch from API)
    const [products, setProducts] = useState([]);
    const [filteredProducts, setFilteredProducts] = useState([]);
    const [category, setCategory] = useState('all');

    useEffect(() => {
        // Fetch products from backend
        const fetchProducts = async () => {
            try {
                // If backend supports /api/stock, we use it. But car.html had hardcoded data.
                // We'll try to fetch from /search (shows all products)
                const res = await axios.get('/api/search?query=');
                setProducts(res.data);
                setFilteredProducts(res.data);
                setStats(prev => ({ ...prev, products: res.data.length }));
            } catch (err) {
                console.error("Failed to fetch products", err);
            }
        };
        fetchProducts();
    }, []);

    useEffect(() => {
        if (category === 'all') {
            setFilteredProducts(products);
        } else {
            // This assumes the backend returns a 'category' or we can infer it
            // The python dictionary had categories, but /search returns a flat list.
            // We might not be able to filter by category easily unless we update the backend.
            // For now, let's just show all or filter if we can. 
            // The products in python are distinct.
            // Simple keyword filter for demo:
            if (category === 'snacks') {
                setFilteredProducts(products.filter(p => ["Lays", "Slice", "Biscuit", "Chocolate", "Noodles"].some(k => p.name.includes(k))));
            } else if (category === 'daily') {
                setFilteredProducts(products.filter(p => !["Lays", "Slice", "Biscuit", "Chocolate", "Noodles"].some(k => p.name.includes(k))));
            }
        }
    }, [category, products]);

    const handleEdit = (id) => alert(`Edit product ${id}`);
    const handleView = (id) => alert(`View product ${id}`);

    return (
        <div style={{ display: 'flex', minHeight: '100vh', flexDirection: 'row', fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif" }}>
            {/* Sidebar */}
            <nav style={{
                width: '280px',
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                boxShadow: '4px 0 20px rgba(0, 0, 0, 0.1)',
                padding: '20px 0',
                position: 'fixed',
                height: '100vh',
                zIndex: 100,
                transform: sidebarOpen ? 'translateX(0)' : 'translateX(0)', // Handle mobile later
                display: 'flex',
                flexDirection: 'column'
            }} className="admin-sidebar">
                <div style={{ textAlign: 'center', padding: '20px', borderBottom: '2px solid #f0f0f0', marginBottom: '30px' }}>
                    <h1 style={{ color: '#2c3e50', fontSize: '28px', fontWeight: 'bold', margin: 0 }}>DMart Admin</h1>
                    <p style={{ color: '#7f8c8d', fontSize: '14px', marginTop: '5px' }}>Store Management</p>
                </div>
                <ul style={{ listStyle: 'none', padding: '0 20px' }}>
                    {['dashboard', 'products', 'inventory', 'orders', 'analytics', 'users', 'settings'].map(section => (
                        <li key={section} style={{ marginBottom: '8px' }}>
                            <button
                                onClick={() => setActiveSection(section)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    width: '100%',
                                    padding: '15px 20px',
                                    textDecoration: 'none',
                                    color: activeSection === section ? 'white' : '#34495e',
                                    borderRadius: '12px',
                                    transition: 'all 0.3s ease',
                                    fontWeight: '500',
                                    background: activeSection === section ? 'linear-gradient(135deg, #667eea, #764ba2)' : 'transparent',
                                    border: 'none',
                                    cursor: 'pointer'
                                }}
                            >
                                <span style={{ textTransform: 'capitalize' }}>{section}</span>
                            </button>
                        </li>
                    ))}
                    <li style={{ marginTop: '20px', borderTop: '1px solid #eee', paddingTop: '10px' }}>
                        <Link to="/home" style={{
                            display: 'flex', width: '100%', padding: '15px 20px',
                            color: '#e74c3c', textDecoration: 'none', fontWeight: '500'
                        }}>
                            Exit Dashboard
                        </Link>
                    </li>
                </ul>
            </nav>

            {/* Main Content */}
            <main style={{
                flex: 1,
                marginLeft: '280px',
                padding: '30px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                minHeight: '100vh',
                overflowY: 'auto'
            }}>
                <header style={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    padding: '25px 30px',
                    borderRadius: '20px',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                    marginBottom: '30px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    <h2 style={{ color: '#2c3e50', fontSize: '32px', fontWeight: '600', margin: 0, textTransform: 'capitalize' }}>{activeSection}</h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                        <span>Welcome, Admin</span>
                        <div style={{
                            width: '45px', height: '45px', borderRadius: '50%',
                            background: 'linear-gradient(135deg, #667eea, #764ba2)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: 'white', fontWeight: 'bold'
                        }}>A</div>
                    </div>
                </header>

                {activeSection === 'dashboard' && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '25px', marginBottom: '30px' }}>
                        {[
                            { label: 'Total Products', val: stats.products, color: '#3498db' },
                            { label: 'Orders Today', val: stats.orders, color: '#e74c3c' },
                            { label: "Today's Revenue", val: `₹${stats.revenue}`, color: '#2ecc71' },
                            { label: 'Active Users', val: stats.users, color: '#f1c40f' }
                        ].map((item, i) => (
                            <div key={i} className="card fade-in" style={{ padding: '30px', textAlign: 'center', backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
                                <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#2c3e50', marginBottom: '8px' }}>{item.val}</div>
                                <div style={{ color: '#7f8c8d', fontWeight: '500' }}>{item.label}</div>
                            </div>
                        ))}
                    </div>
                )}

                {activeSection === 'products' && (
                    <div className="section" style={{ background: 'rgba(255, 255, 255, 0.95)', borderRadius: '20px', padding: '0 0 20px', boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}>
                        <div style={{ padding: '25px 30px', borderBottom: '2px solid #f8f9fa', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 style={{ fontSize: '24px', fontWeight: '600', color: '#2c3e50', margin: 0 }}>Product Management</h3>
                            <button className="btn btn-primary" onClick={() => alert('Feature coming soon')}>Add New Product</button>
                        </div>
                        <div style={{ display: 'flex', padding: '20px 30px 0', gap: '10px', borderBottom: '2px solid #f8f9fa' }}>
                            {['all', 'snacks', 'daily'].map(cat => (
                                <button
                                    key={cat}
                                    onClick={() => setCategory(cat)}
                                    style={{
                                        padding: '12px 24px', border: 'none', background: 'none',
                                        color: category === cat ? '#667eea' : '#7f8c8d',
                                        fontWeight: '600', cursor: 'pointer',
                                        borderBottom: category === cat ? '3px solid #667eea' : '3px solid transparent'
                                    }}
                                >
                                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                                </button>
                            ))}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px', padding: '30px' }}>
                            {filteredProducts.map(p => (
                                <div key={p.id} className="card" style={{ padding: '20px', background: 'white', borderRadius: '16px', boxShadow: '0 4px 15px rgba(0,0,0,0.08)' }}>
                                    <div style={{ width: '100%', height: '150px', background: '#f8f9fa', borderRadius: '12px', marginBottom: '15px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <img
                                            src={p.image.startsWith('http') ? p.image : `http://localhost:5003${p.image}`}
                                            alt={p.name}
                                            style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                                            onError={(e) => { e.target.src = 'https://placehold.co/150x150?text=No+Image'; }}
                                        />
                                    </div>
                                    <div style={{ fontSize: '16px', fontWeight: '600', color: '#2c3e50', marginBottom: '8px' }}>{p.name}</div>
                                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#e74c3c', marginBottom: '8px' }}>₹{p.price}</div>
                                    <div style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '15px' }}>📍 {p.location}</div>
                                    <div style={{ display: 'flex', gap: '10px' }}>
                                        <button className="btn" style={{ flex: 1, backgroundColor: '#ecf0f1', color: '#34495e', padding: '8px' }} onClick={() => handleEdit(p.id)}>Edit</button>
                                        <button className="btn btn-primary" style={{ flex: 1, padding: '8px' }} onClick={() => handleView(p.id)}>View</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {['inventory', 'orders', 'analytics', 'users', 'settings'].includes(activeSection) && (
                    <div style={{ background: 'rgba(255, 255, 255, 0.95)', borderRadius: '20px', padding: '40px', textAlign: 'center' }}>
                        <h3 style={{ color: '#7f8c8d' }}>{activeSection.charAt(0).toUpperCase() + activeSection.slice(1)} features coming soon...</h3>
                    </div>
                )}
            </main>
        </div>
    );
};

export default AdminDashboard;
