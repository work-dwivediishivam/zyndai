import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Download, Eye } from 'lucide-react';
import { proposalsApi, activeTendersApi } from '../api/client';
import { Sidebar, useSidebarWidth } from '../components/Sidebar';
import { SearchInput } from '../components/SearchInput';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import './HomePage.css';

interface Proposal {
    id: string;
    title: string;
    content: string;
    created_at: string;
    updated_at: string;
    pinned?: boolean;
    final_draft?: boolean;
    status?: string;
    proposal_revision?: string;
    assigned_to_email?: string;  // If set, this is a revision assigned to a specific user
}

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
}

export function HomePage() {
    const [activeProposal, setActiveProposal] = useState<Proposal | null>(null);
    const [input, setInput] = useState('');
    const [newTitle, setNewTitle] = useState('');
    const [loading, setLoading] = useState(false);
    const [showNewForm, setShowNewForm] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
    const [showTenderTable, setShowTenderTable] = useState(false);
    const [activeTenders, setActiveTenders] = useState<ActiveTender[]>([]);
    const [isPublishing, setIsPublishing] = useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);
    const sidebarWidth = useSidebarWidth();

    useEffect(() => {
        loadActiveTenders();
    }, [sidebarRefreshKey]);

    const loadActiveTenders = async () => {
        try {
            const data = await activeTendersApi.list();
            setActiveTenders(data);
        } catch (err) {
            console.error('Failed to load active tenders');
        }
    };

    const handleCreateProposal = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newTitle.trim()) return;
        setLoading(true);
        try {
            const proposal = await proposalsApi.create(newTitle);
            setActiveProposal(proposal);
            setNewTitle('');
            setShowNewForm(false);
            setSidebarRefreshKey(prev => prev + 1);
        } catch (err) {
            console.error('Failed to create proposal');
        } finally {
            setLoading(false);
        }
    };

    const handleIterate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!activeProposal || !input.trim()) return;

        setLoading(true);
        try {
            let updated;
            if (selectedFiles.length > 0) {
                const response = await proposalsApi.chat(activeProposal.id, input, selectedFiles);
                updated = response.proposal;
            } else {
                updated = await proposalsApi.iterate(activeProposal.id, input);
            }

            setActiveProposal(updated);
            setInput('');
            setSelectedFiles([]);

            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }

            const textarea = document.querySelector('.chat-textarea') as HTMLTextAreaElement;
            if (textarea) {
                textarea.style.height = 'auto';
            }
        } catch (err) {
            console.error('Failed to iterate:', err);
            alert('Failed to send message. Please check that the backend is running and GOOGLE_API_KEY is set.');
        } finally {
            setLoading(false);
        }
    };

    const showNotification = (message: string, type: 'success' | 'error') => {
        setNotification({ message, type });
        setTimeout(() => setNotification(null), 4000);
    };

    const handleSubmitDraft = async () => {
        if (!activeProposal || activeProposal.final_draft) return;
        setIsSubmitting(true);
        try {
            const result = await proposalsApi.submit(activeProposal.id);
            setActiveProposal(result.proposal);
            setSidebarRefreshKey(prev => prev + 1);
            showNotification('Draft submitted successfully! Notifications sent to relevant departments.', 'success');
        } catch (err) {
            showNotification('Failed to submit draft. Please try again.', 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handlePublishTender = async () => {
        if (!activeProposal) return;
        setIsPublishing(true);
        try {
            const result = await activeTendersApi.publishTender(activeProposal.id);
            // Update the active proposal with the new status
            if (result.proposal) {
                setActiveProposal(result.proposal);
            }
            setSidebarRefreshKey(prev => prev + 1);
            showNotification('Tender published successfully!', 'success');
            // Refresh the active tenders list
            loadActiveTenders();
        } catch (err: any) {
            const errorMsg = err?.response?.data?.detail || 'Failed to publish tender. Please try again.';
            showNotification(errorMsg, 'error');
        } finally {
            setIsPublishing(false);
        }
    };

    const handleActiveTenderSelect = () => {
        setShowTenderTable(true);
        setActiveProposal(null);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    };

    const openTenderInNewTab = (tenderId: string) => {
        window.open(`/active-tenders/${tenderId}`, '_blank');
    };

    const exportToPDF = async () => {
        if (!activeProposal || !activeProposal.content) {
            alert('No content to export');
            return;
        }

        try {
            const element = document.querySelector('.markdown-preview') as HTMLElement;
            if (!element) {
                alert('Could not find content to export');
                return;
            }

            const canvas = await html2canvas(element, {
                scale: 2,
                useCORS: true,
                logging: false,
                backgroundColor: '#ffffff'
            });

            const imgWidth = 210;
            const pageHeight = 297;
            const imgHeight = (canvas.height * imgWidth) / canvas.width;
            let heightLeft = imgHeight;
            let position = 0;

            const pdf = new jsPDF('p', 'mm', 'a4');
            const imgData = canvas.toDataURL('image/png');

            pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;

            while (heightLeft > 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;
            }

            const fileName = `${activeProposal.title.replace(/[\/\\:*?"<>|]/g, '-').trim()}.pdf`;
            pdf.save(fileName);
        } catch (err) {
            console.error('Failed to export PDF:', err);
            alert('Failed to export PDF');
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setSelectedFiles(Array.from(e.target.files));
        }
    };

    const handleRemoveFile = (index: number) => {
        setSelectedFiles(files => files.filter((_, i) => i !== index));
    };

    const handleProposalSelect = (proposal: Proposal) => {
        setActiveProposal(proposal);
    };

    const handleNewProposal = () => {
        setShowNewForm(true);
    };

    const handleHomeSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;
        setLoading(true);
        try {
            const proposal = await proposalsApi.create('New Proposal');
            setActiveProposal(proposal);
            setSidebarRefreshKey(prev => prev + 1);
            setTimeout(async () => {
                try {
                    let updated;
                    if (selectedFiles.length > 0) {
                        const response = await proposalsApi.chat(proposal.id, input, selectedFiles);
                        updated = response.proposal;
                    } else {
                        updated = await proposalsApi.iterate(proposal.id, input);
                    }
                    setActiveProposal(updated);
                    setInput('');
                    setSelectedFiles([]);
                    if (fileInputRef.current) {
                        fileInputRef.current.value = '';
                    }
                } catch (err) {
                    console.error('Failed to iterate:', err);
                } finally {
                    setLoading(false);
                }
            }, 100);
        } catch (err) {
            console.error('Failed to create proposal');
            setLoading(false);
        }
    };



    return (
        <div className="home-container">
            <Sidebar
                activeProposalId={activeProposal?.id}
                onProposalSelect={(proposal) => {
                    setShowTenderTable(false);
                    handleProposalSelect(proposal);
                }}
                onNewProposal={() => {
                    setShowTenderTable(false);
                    handleNewProposal();
                }}
                refreshKey={sidebarRefreshKey}
                onActiveTenderSelect={handleActiveTenderSelect}
            />

            <main
                className="main-content"
                style={{ marginLeft: `${sidebarWidth}px` }}
            >
                {showNewForm && (
                    <div className="modal-overlay" onClick={() => setShowNewForm(false)}>
                        <div className="modal" onClick={(e) => e.stopPropagation()}>
                            <h3>Create New Proposal</h3>
                            <form onSubmit={handleCreateProposal}>
                                <input
                                    type="text"
                                    value={newTitle}
                                    onChange={(e) => setNewTitle(e.target.value)}
                                    placeholder="Proposal title..."
                                    autoFocus
                                />
                                <div className="modal-actions">
                                    <button type="button" onClick={() => setShowNewForm(false)}>Cancel</button>
                                    <button type="submit" disabled={loading}>Create</button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {showTenderTable ? (
                    /* Active Tenders Table View */
                    <div className="tender-table-container">
                        <div className="editor-header">
                            <h1>Active Tenders</h1>
                        </div>
                        <div className="tender-table-wrapper">
                            {activeTenders.length === 0 ? (
                                <div className="empty-tenders">
                                    <p>No active tenders yet.</p>
                                    <p>Publish a tender from a proposal revision to see it here.</p>
                                </div>
                            ) : (
                                <table className="tender-table">
                                    <thead>
                                        <tr>
                                            <th>S.No</th>
                                            <th>Title</th>
                                            <th>Organisation NIF</th>
                                            <th>Price</th>
                                            <th>Submission Date</th>
                                            <th>Deadline</th>
                                            <th>Expiry</th>
                                            <th>View</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {activeTenders.map((tender, index) => (
                                            <tr key={tender.id}>
                                                <td>{index + 1}</td>
                                                <td className="tender-title-cell">{tender.title}</td>
                                                <td>{tender.organization_nif}</td>
                                                <td>{tender.price > 0 ? `₹${tender.price.toLocaleString()}` : '0'}</td>
                                                <td>{formatDate(tender.submission_date)}</td>
                                                <td>{formatDate(tender.submission_deadline)}</td>
                                                <td>{formatDate(tender.contract_expiry_date)}</td>
                                                <td>
                                                    <button
                                                        className="view-tender-btn"
                                                        onClick={() => openTenderInNewTab(tender.id)}
                                                        title="View Tender"
                                                    >
                                                        <Eye size={18} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                ) : activeProposal ? (
                    <>
                        <div className="editor-header">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <h1>{activeProposal.title}</h1>
                                {(() => {
                                    const isPublished = activeProposal.status === 'published' ||
                                        activeTenders.some(t => t.proposal_id === activeProposal.id);
                                    if (isPublished) {
                                        return <span className="status-badge published">Published</span>;
                                    } else if (activeProposal.assigned_to_email) {
                                        return <span className="status-badge revision">Revision Required</span>;
                                    } else if (activeProposal.final_draft) {
                                        return <span className="status-badge submitted">Submitted</span>;
                                    }
                                    return null;
                                })()}
                            </div>
                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                                <button onClick={exportToPDF} className="export-pdf-btn">
                                    <Download size={18} />
                                    Export
                                </button>
                                {activeProposal.assigned_to_email ? (
                                    // Publish Tender button for assigned revisions
                                    (() => {
                                        const isAlreadyPublished = activeProposal.status === 'published' ||
                                            activeTenders.some(t => t.proposal_id === activeProposal.id);
                                        return (
                                            <button
                                                onClick={handlePublishTender}
                                                className={`submit-btn publish ${isAlreadyPublished ? 'submitted' : ''}`}
                                                disabled={isPublishing || isAlreadyPublished}
                                            >
                                                {isPublishing ? 'Publishing...' : isAlreadyPublished ? '✓ Published' : 'Publish Tender'}
                                            </button>
                                        );
                                    })()
                                ) : (
                                    // Submit Draft button for owner's proposals
                                    <button
                                        onClick={handleSubmitDraft}
                                        className={`submit-btn ${activeProposal.final_draft ? 'submitted' : ''}`}
                                        disabled={activeProposal.final_draft || isSubmitting}
                                    >
                                        {isSubmitting ? 'Submitting...' : activeProposal.final_draft ? '✓ Submitted' : 'Submit Draft'}
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="editor-content">
                            {loading && !activeProposal.content ? (
                                <div className="loading-container">
                                    <div className="spinner"></div>
                                    <p className="generating-text">generating</p>
                                </div>
                            ) : (
                                <div className="markdown-preview">
                                    {activeProposal.final_draft && activeProposal.proposal_revision ? (
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{activeProposal.proposal_revision}</ReactMarkdown>
                                    ) : (
                                        activeProposal.content && <ReactMarkdown remarkPlugins={[remarkGfm]}>{activeProposal.content}</ReactMarkdown>
                                    )}
                                </div>
                            )}
                        </div>


                        <SearchInput
                            input={input}
                            setInput={setInput}
                            loading={loading}
                            selectedFiles={selectedFiles}
                            fileInputRef={fileInputRef}
                            onFileSelect={handleFileSelect}
                            onRemoveFile={handleRemoveFile}
                            onSubmit={handleIterate}
                            placeholder="Describe what you want to add or change..."
                            className="chat-input-form"
                            sidebarWidth={sidebarWidth}
                        />
                    </>
                ) : (
                    <div className="empty-workspace">
                        <h2>Welcome to Uniflow</h2>
                        <p>Select a proposal from the sidebar or create a new one to get started.</p>
                        <SearchInput
                            input={input}
                            setInput={setInput}
                            loading={loading}
                            selectedFiles={selectedFiles}
                            fileInputRef={fileInputRef}
                            onFileSelect={handleFileSelect}
                            onRemoveFile={handleRemoveFile}
                            onSubmit={handleHomeSearch}
                            placeholder="Start writing your proposal..."
                            className="home-search-form"
                            sidebarWidth={sidebarWidth}
                        />
                    </div>
                )}

                {/* Notification Toast */}
                {notification && (
                    <div className={`notification-toast ${notification.type}`}>
                        {notification.message}
                    </div>
                )}
            </main>
        </div>
    );
}
