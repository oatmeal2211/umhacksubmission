import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './navbar.css';

const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 100); // adjust scroll trigger as needed
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={isScrolled ? 'scrolled' : 'transparent'}>
      <div className="navbar-container">
        <div className="navbar-left">
          <h3>Easy2Wakaf</h3>
          <Link to="/">Home</Link>
          <Link to="/profile">Profile</Link>
          <Link to="/about">About</Link>
          <Link to="/addproject">Add Project</Link>
          <Link to="/rewards">Rewards</Link>
          
        </div>
        <div className="navbar-right">
        <button className="btnLogin" onClick={() => navigate('/login')}>
          Login
        </button>
          <button className="btnRegister"  onClick={() => navigate('/register')}>Register</button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;