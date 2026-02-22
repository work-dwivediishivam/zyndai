import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import './LoginPage.css';

export function LoginPage() {
    const [isRegistering, setIsRegistering] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [organizationName, setOrganizationName] = useState('');
    const [organizationNif, setOrganizationNif] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login, register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            if (isRegistering) {
                await register(email, password, name, organizationName, organizationNif);
            } else {
                await login(email, password);
            }
            navigate('/');
        } catch (err: any) {
            setError(err?.response?.data?.detail || (isRegistering ? 'Registration failed' : 'Invalid credentials'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <h1>🚀 Uniflow</h1>
                    <p>Unified Tender Proposal Platform</p>
                </div>

                <div className="auth-tabs">
                    <button
                        className={`auth-tab ${!isRegistering ? 'active' : ''}`}
                        onClick={() => setIsRegistering(false)}
                        type="button"
                    >
                        Sign In
                    </button>
                    <button
                        className={`auth-tab ${isRegistering ? 'active' : ''}`}
                        onClick={() => setIsRegistering(true)}
                        type="button"
                    >
                        Register
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    {isRegistering && (
                        <div className="form-group">
                            <label htmlFor="name">Full Name</label>
                            <input
                                id="name"
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Enter your full name"
                                required
                            />
                        </div>
                    )}
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your email"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                        />
                    </div>
                    {isRegistering && (
                        <>
                            <div className="form-group">
                                <label htmlFor="orgName">Organization Name</label>
                                <input
                                    id="orgName"
                                    type="text"
                                    value={organizationName}
                                    onChange={(e) => setOrganizationName(e.target.value)}
                                    placeholder="Enter your organization name"
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="orgNif">Organization NIF (Tax ID)</label>
                                <input
                                    id="orgNif"
                                    type="text"
                                    value={organizationNif}
                                    onChange={(e) => setOrganizationNif(e.target.value)}
                                    placeholder="Enter NIF (optional)"
                                />
                            </div>
                        </>
                    )}
                    {error && <div className="error">{error}</div>}
                    <button type="submit" disabled={loading} className="login-btn">
                        {loading ? (isRegistering ? 'Creating account...' : 'Signing in...') : (isRegistering ? 'Create Account' : 'Sign In')}
                    </button>
                </form>
            </div>
        </div>
    );
}
