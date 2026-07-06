import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import Scanner from './pages/Scanner';
import Search from './pages/Search';
import ProductDetails from './pages/ProductDetails';
import Dashboard from './pages/Dashboard';
import AdminDashboard from './pages/AdminDashboard';
import Bill from './pages/Bill';
import ProtectedRoute from './components/ProtectedRoute';
import AIChatModal from './components/AIChatModal';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />

        <Route
          path="/scanner"
          element={
            <ProtectedRoute>
              <Scanner />
            </ProtectedRoute>
          }
        />

        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <Search />
            </ProtectedRoute>
          }
        />

        <Route
          path="/product/:id"
          element={
            <ProtectedRoute>
              <ProductDetails />
            </ProtectedRoute>
          }
        />

        {/* This dashboard is for basic stock management */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* This is the comprehensive admin panel */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/bill"
          element={
            // Not strictly protected as it might be popped out, but good to keep it secure.
            <ProtectedRoute>
              <Bill />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Simple 404 */}
        <Route path="*" element={<div style={{ color: 'white', textAlign: 'center', marginTop: '50px' }}><h1>404 - Page Not Found</h1></div>} />
      </Routes>
      <AIChatModal />
    </Router>
  );
}

export default App;
