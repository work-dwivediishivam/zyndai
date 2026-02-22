import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowLeft } from 'lucide-react';
import { activeTendersApi } from '../api/client';
import './ActiveTenderPage.css';

interface ActiveTender {
    id: string;
    proposal_id: string;
    title: string;
    organization_nif: string;
    price: number;
    submission_date: string;
    submission_deadline: string;
    contract_expiry_date: string;
    tender_content: string;
    created_by: string;
    created_at: string;
    updated_at: string;
}

export function ActiveTenderPage() {
    const { tenderId } = useParams<{ tenderId: string }>();
    const navigate = useNavigate();
    const [tender, setTender] = useState<ActiveTender | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadTender = async () => {
            if (!tenderId) return;

            setLoading(true);
            try {
                const data = await activeTendersApi.get(tenderId);
                setTender(data);
            } catch (err) {
                console.error('Failed to load tender:', err);
                setError('Failed to load tender. It may not exist or you may not have access.');
            } finally {
                setLoading(false);
            }
        };

        loadTender();
    }, [tenderId]);

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (loading) {
        return (
            <div className="tender-page">
                <div className="tender-loading">
                    <div className="spinner"></div>
                    <p>Loading tender...</p>
                </div>
            </div>
        );
    }

    if (error || !tender) {
        return (
            <div className="tender-page">
                <div className="tender-error">
                    <h2>Error</h2>
                    <p>{error || 'Tender not found'}</p>
                    <button onClick={() => navigate('/')} className="back-btn">
                        <ArrowLeft size={18} />
                        Back to Home
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="tender-page">
            <div className="tender-header">
                <button onClick={() => navigate('/')} className="back-btn">
                    <ArrowLeft size={18} />
                    Back
                </button>
                <div className="tender-meta">
                    <h1>{tender.title}</h1>
                    <div className="tender-info-grid">
                        <div className="info-item">
                            <span className="info-label">Organization NIF</span>
                            <span className="info-value">{tender.organization_nif}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Price</span>
                            <span className="info-value">
                                {tender.price > 0 ? `₹${tender.price.toLocaleString()}` : 'Not specified'}
                            </span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Submission Date</span>
                            <span className="info-value">{formatDate(tender.submission_date)}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Deadline</span>
                            <span className="info-value">{formatDate(tender.submission_deadline)}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Contract Expiry</span>
                            <span className="info-value">{formatDate(tender.contract_expiry_date)}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="tender-content-wrapper">
                <div className="markdown-preview">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {tender.tender_content}
                    </ReactMarkdown>
                </div>
            </div>
        </div>
    );
}
