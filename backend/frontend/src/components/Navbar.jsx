import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FiMenu, FiX, FiLogOut } from 'react-icons/fi';
import './Navbar.css';

function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const toggleMenu = () => setIsOpen(!isOpen);

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          AAIS
        </Link>
        
        <button className="menu-toggle" onClick={toggleMenu}>
          {isOpen ? <FiX /> : <FiMenu />}
        </button>

        <ul className={`nav-menu ${isOpen ? 'active' : ''}`}>
          <li className="nav-item">
            <Link to="/" className="nav-link">Dashboard</Link>
          </li>
          <li className="nav-item">
            <Link to="/text-generator" className="nav-link">Text Generator</Link>
          </li>
          <li className="nav-item">
            <Link to="/image-analyzer" className="nav-link">Image Analyzer</Link>
          </li>
          <li className="nav-item">
            <Link to="/image-generator" className="nav-link">Image Generator</Link>
          </li>
          <li className="nav-item">
            <Link to="/audio-processor" className="nav-link">Audio Processor</Link>
          </li>
          <li className="nav-item">
            <Link to="/batch-processor" className="nav-link">Batch Processor</Link>
          </li>
          <li className="nav-item">
            <Link to="/history" className="nav-link">History</Link>
          </li>
          <li className="nav-item">
            <Link to="/settings" className="nav-link">Settings</Link>
          </li>
          {isLoggedIn && (
            <li className="nav-item">
              <button className="logout-btn" onClick={() => setIsLoggedIn(false)}>
                <FiLogOut /> Logout
              </button>
            </li>
          )}
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
