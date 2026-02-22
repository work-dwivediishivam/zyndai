import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { authApi } from '../api/client';

interface AuthContextType {
    isAuthenticated: boolean;
    userEmail: string | null;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, name: string, organizationName: string, organizationNif: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [userEmail, setUserEmail] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        const email = localStorage.getItem('userEmail');
        setIsAuthenticated(!!token);
        setUserEmail(email);
        setIsLoading(false);
    }, []);

    const login = async (email: string, password: string) => {
        const data = await authApi.login(email, password);
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('userEmail', email);
        setIsAuthenticated(true);
        setUserEmail(email);
    };

    const register = async (email: string, password: string, name: string, organizationName: string, organizationNif: string) => {
        const data = await authApi.register(email, password, name, organizationName, organizationNif);
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('userEmail', email);
        setIsAuthenticated(true);
        setUserEmail(email);
    };

    const logout = () => {
        authApi.logout();
        localStorage.removeItem('userEmail');
        setIsAuthenticated(false);
        setUserEmail(null);
    };

    return (
        <AuthContext.Provider value={{ isAuthenticated, userEmail, isLoading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
}
