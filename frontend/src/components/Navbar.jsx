import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { FiMenu, FiX } from 'react-icons/fi';
import './Navbar.css';

function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const isHomeRoute = location.pathname === '/' || location.pathname.startsWith('/nova');
  const isJarvisRoute =
    location.pathname.startsWith('/jarvis')
    || location.pathname.startsWith('/operator')
    || location.pathname.startsWith('/platform');
  const surface = isJarvisRoute ? 'jarvis' : 'nova';

  const toggleMenu = () => setIsOpen(!isOpen);
  const closeMenu = () => setIsOpen(false);
  const linkClassName = ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`;
  const navItems = isJarvisRoute
    ? [
        { type: 'route', to: '/jarvis', label: 'Console' },
        { type: 'route', to: '/operator', label: 'UGR / Forge' },
        { type: 'route', to: '/platform', label: 'Platform Ops' },
        { type: 'route', to: '/jarvis/repo-manager', label: 'Repo Manager' },
        { type: 'route', to: '/memory', label: 'Memory Bank' },
  { type: 'route', to: '/', label: 'Small Nova' },
      ]
    : isHomeRoute
    ? [
        { type: 'anchor', href: '#chat', label: 'Chat' },
        { type: 'anchor', href: '#intake', label: 'Intake' },
        { type: 'anchor', href: '#categories', label: 'Categories' },
        { type: 'route', to: '/jarvis', label: 'Console' },
        { type: 'route', to: '/memory', label: 'Memory Bank' },
      ]
    : [
        { type: 'route', to: '/', label: 'Home' },
        { type: 'route', to: '/jarvis', label: 'Console' },
        { type: 'route', to: '/memory', label: 'Memory Bank' },
      ];
  const brand = isJarvisRoute
    ? { mark: 'JARVIS', subtitle: 'Operator Console', to: '/jarvis' }
  : { mark: 'SMALL NOVA', subtitle: 'Companion Surface', to: '/' };

  return (
    <nav className={`navbar navbar--${surface}`}>
      <div className="navbar-container">
        <NavLink to={brand.to} className="navbar-logo" onClick={closeMenu}>
          <span className="navbar-mark">{brand.mark}</span>
          <span className="navbar-subtitle">{brand.subtitle}</span>
        </NavLink>
        
        <button className="menu-toggle" onClick={toggleMenu} aria-label="Toggle navigation">
          {isOpen ? <FiX /> : <FiMenu />}
        </button>

        <ul className={`nav-menu ${isOpen ? 'active' : ''}`}>
          {navItems.map((item) => (
            <li className="nav-item" key={item.label}>
              {item.type === 'anchor' ? (
                <a href={item.href} className="nav-link" onClick={closeMenu}>
                  {item.label}
                </a>
              ) : (
                <NavLink to={item.to} className={linkClassName} onClick={closeMenu}>
                  {item.label}
                </NavLink>
              )}
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
