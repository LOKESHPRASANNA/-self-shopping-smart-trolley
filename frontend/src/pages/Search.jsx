import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../index.css';

const Search = () => {
    const [query, setQuery] = useState('');
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchProducts = async (searchQuery = '') => {
        setLoading(true);
        try {
            const res = await axios.get(`/api/search?query=${searchQuery}`);
            setProducts(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProducts();
    }, []);

    const handleSearch = (e) => {
        e.preventDefault();
        fetchProducts(query);
    };

    return (
        <div className="container fade-in" style={{ paddingTop: '20px', minHeight: '100vh' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
                <Link to="/home" className="btn btn-primary" style={{ backgroundColor: '#7f8c8d' }}>&larr; Back to Home</Link>
                <h1 style={{ color: 'white', margin: 0 }}>Product Gallery</h1>
                <div style={{ width: '100px' }}></div> {/* Spacer */}
            </div>

            <div className="card" style={{ backgroundColor: 'white', marginBottom: '30px', textAlign: 'center' }}>
                <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                    <input
                        type="text"
                        placeholder="Search for products..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        style={{ padding: '12px', width: '300px', borderRadius: '25px', border: '1px solid #ccc' }}
                    />
                    <button type="submit" className="btn btn-primary" style={{ borderRadius: '25px' }}>Search</button>
                </form>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', color: 'white' }}>Loading...</div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '20px' }}>
                    {products.map((product) => (
                        <div key={product.id} className="card fade-in" style={{ backgroundColor: 'white', padding: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', transition: 'transform 0.3s' }}>
                            <img
                                src={product.image}
                                alt={product.name}
                                style={{ width: '150px', height: '150px', objectFit: 'contain', marginBottom: '15px' }}
                                onError={(e) => { e.target.src = '/static/images/placeholder.svg'; }}
                            />
                            <h3 style={{ fontSize: '1.2rem', margin: '10px 0', textAlign: 'center', color: '#333' }}>{product.name}</h3>
                            <p style={{ color: '#e74c3c', fontWeight: 'bold', fontSize: '1.1rem' }}>₹{product.price}</p>
                            <Link to={`/product/${product.id}`} className="btn btn-primary" style={{ marginTop: 'auto', width: '100%' }}>
                                View Shelf
                            </Link>
                        </div>
                    ))}
                    {products.length === 0 && (
                        <div style={{ gridColumn: '1/-1', textAlign: 'center', color: 'white', fontSize: '1.2rem' }}>No products found.</div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Search;
