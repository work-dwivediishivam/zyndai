import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Rocket, ChevronLeft, ChevronRight, ChevronUp, ChevronDown, User, LogOut, Pin, Trash2, MoreVertical, Edit, FileText, FileCheck, Briefcase } from 'lucide-react';
import { proposalsApi, activeTendersApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';

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
}

interface SidebarProps {
    activeProposalId?: string;
    onProposalSelect?: (proposal: Proposal) => void;
    onNewProposal?: () => void;
    refreshKey?: number;
    onActiveTenderSelect?: () => void;
}

export function Sidebar({ activeProposalId, onProposalSelect, onNewProposal, refreshKey, onActiveTenderSelect }: SidebarProps) {
    const [proposals, setProposals] = useState<Proposal[]>([]);
    const [myRevisions, setMyRevisions] = useState<Proposal[]>([]);
    const [activeTenders, setActiveTenders] = useState<any[]>([]);
    const [openMenuId, setOpenMenuId] = useState<string | null>(null);
    const [renamingId, setRenamingId] = useState<string | null>(null);
    const [renameValue, setRenameValue] = useState('');
    const [sidebarWidth, setSidebarWidth] = useState(() => {
        const saved = localStorage.getItem('sidebarWidth');
        return saved ? parseInt(saved, 10) : 280;
    });
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
        const saved = localStorage.getItem('sidebarCollapsed');
        return saved === 'true';
    });
    const [isResizing, setIsResizing] = useState(false);
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [isDraftDrawerOpen, setIsDraftDrawerOpen] = useState(true);
    const [isRevisionDrawerOpen, setIsRevisionDrawerOpen] = useState(false);
    const [isTenderDrawerOpen, setIsTenderDrawerOpen] = useState(false);
    const { logout, userEmail } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        loadProposals();
        loadMyRevisions();
        loadActiveTenders();
    }, [refreshKey]);

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                setOpenMenuId(null);
                setShowProfileMenu(false);
            }
        };
        if (openMenuId || showProfileMenu) {
            document.addEventListener('keydown', handleEscape);
            return () => document.removeEventListener('keydown', handleEscape);
        }
    }, [openMenuId, showProfileMenu]);

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            const target = e.target as HTMLElement;
            if (showProfileMenu && !target.closest('.user-profile')) {
                setShowProfileMenu(false);
            }
        };
        if (showProfileMenu) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [showProfileMenu]);

    useEffect(() => {
        localStorage.setItem('sidebarWidth', sidebarWidth.toString());
    }, [sidebarWidth]);

    useEffect(() => {
        localStorage.setItem('sidebarCollapsed', isSidebarCollapsed.toString());
    }, [isSidebarCollapsed]);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return;
            const newWidth = Math.max(200, Math.min(600, e.clientX));
            setSidebarWidth(newWidth);
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [isResizing]);

    const sortProposals = (proposalsList: Proposal[]): Proposal[] => {
        return [...proposalsList].sort((a, b) => {
            if (a.pinned && !b.pinned) return -1;
            if (!a.pinned && b.pinned) return 1;
            return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        });
    };

    const categorizeProposals = (proposalsList: Proposal[]) => {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        const categorized = {
            today: [] as Proposal[],
            yesterday: [] as Proposal[],
            past: [] as Proposal[],
        };

        proposalsList.forEach(proposal => {
            const proposalDate = new Date(proposal.created_at);
            proposalDate.setHours(0, 0, 0, 0);

            if (proposalDate.getTime() === today.getTime()) {
                categorized.today.push(proposal);
            } else if (proposalDate.getTime() === yesterday.getTime()) {
                categorized.yesterday.push(proposal);
            } else {
                categorized.past.push(proposal);
            }
        });

        return categorized;
    };

    const loadProposals = async () => {
        try {
            const data = await proposalsApi.list();
            setProposals(sortProposals(data));
        } catch (err) {
            console.error('Failed to load proposals');
        }
    };

    const loadMyRevisions = async () => {
        try {
            const data = await proposalsApi.getMyRevisions();
            setMyRevisions(data);
        } catch (err) {
            console.error('Failed to load revisions');
        }
    };

    const loadActiveTenders = async () => {
        try {
            const data = await activeTendersApi.list();
            setActiveTenders(data);
        } catch (err) {
            console.error('Failed to load active tenders');
        }
    };

    const handleDelete = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm('Are you sure you want to delete this proposal?')) return;
        try {
            await proposalsApi.delete(id);
            loadProposals();
            setOpenMenuId(null);
        } catch (err) {
            console.error('Failed to delete proposal');
        }
    };

    const handlePin = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            const updated = await proposalsApi.pin(id);
            const updatedProposals = proposals.map(p => p.id === id ? updated : p);
            setProposals(sortProposals(updatedProposals));
            setOpenMenuId(null);
        } catch (err) {
            console.error('Failed to pin/unpin proposal');
        }
    };

    const handleRename = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const proposal = proposals.find(p => p.id === id);
        if (proposal) {
            setRenamingId(id);
            setRenameValue(proposal.title);
            setOpenMenuId(null);
        }
    };

    const handleRenameSubmit = async (id: string) => {
        if (!renameValue.trim()) {
            setRenamingId(null);
            return;
        }
        try {
            const updated = await proposalsApi.rename(id, renameValue.trim());
            setProposals(proposals.map(p => p.id === id ? updated : p));
            setRenamingId(null);
            setRenameValue('');
        } catch (err) {
            console.error('Failed to rename proposal');
        }
    };

    const handleRenameCancel = () => {
        setRenamingId(null);
        setRenameValue('');
    };

    const toggleMenu = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setOpenMenuId(openMenuId === id ? null : id);
    };

    const toggleSidebar = () => {
        setIsSidebarCollapsed(!isSidebarCollapsed);
    };

    const handleResizeStart = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
    };

    const getUserInitials = (email: string | null) => {
        if (!email) return 'U';
        const name = email.split('@')[0];
        return name.charAt(0).toUpperCase();
    };

    const getUserName = (email: string | null) => {
        if (!email) return 'User';
        const name = email.split('@')[0];
        return name.split('.').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' ');
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleProposalClick = (p: Proposal) => {
        if (renamingId !== p.id) {
            setOpenMenuId(null);
            if (onProposalSelect) {
                onProposalSelect(p);
            } else {
                navigate('/');
            }
        }
    };

    const renderProposalItem = (p: Proposal) => (
        <div
            key={p.id}
            className={`proposal-item ${activeProposalId === p.id ? 'active' : ''}`}
            onClick={() => handleProposalClick(p)}
        >
            {renamingId === p.id ? (
                <div className="proposal-rename-input" onClick={(e) => e.stopPropagation()}>
                    <input
                        type="text"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onBlur={() => handleRenameSubmit(p.id)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                handleRenameSubmit(p.id);
                            } else if (e.key === 'Escape') {
                                handleRenameCancel();
                            }
                        }}
                        autoFocus
                        className="rename-input"
                    />
                </div>
            ) : (
                <>
                    <div className="proposal-content">
                        <span className="proposal-title">
                            {p.pinned && <Pin size={14} className="pin-icon" />}
                            {p.title}
                        </span>
                    </div>
                    <div className="proposal-menu-container">
                        <button
                            className="proposal-menu-btn"
                            onClick={(e) => toggleMenu(p.id, e)}
                            aria-label="More options"
                        >
                            <MoreVertical size={18} className="menu-dots-icon" />
                        </button>
                        {openMenuId === p.id && (
                            <div className="proposal-menu-dropdown">
                                <button
                                    className="menu-item"
                                    onClick={(e) => handleRename(p.id, e)}
                                >
                                    <Edit size={16} className="menu-item-icon" />
                                    <span>Rename</span>
                                </button>
                                <button
                                    className="menu-item"
                                    onClick={(e) => handlePin(p.id, e)}
                                >
                                    <Pin size={16} className="menu-item-icon" />
                                    <span>{p.pinned ? 'Unpin' : 'Pin'}</span>
                                </button>
                                <button
                                    className="menu-item delete"
                                    onClick={(e) => handleDelete(p.id, e)}
                                >
                                    <Trash2 size={16} className="menu-item-icon" />
                                    <span>Delete</span>
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );

    // Export the sidebar width for parent components
    const currentWidth = isSidebarCollapsed ? 60 : sidebarWidth;

    return (
        <>
            <aside
                className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}
                style={{ width: isSidebarCollapsed ? '60px' : `${sidebarWidth}px` }}
            >
                <div className="sidebar-header">
                    {!isSidebarCollapsed && (
                        <h2
                            className="sidebar-title clickable-logo"
                            onClick={() => navigate('/')}
                            title="Go to home"
                        >
                            <Rocket size={28} className="rocket-icon" />
                            Uniflow
                        </h2>
                    )}
                    <div className="sidebar-header-actions">
                        <button
                            onClick={toggleSidebar}
                            className="collapse-btn"
                            aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                        >
                            {isSidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                        </button>
                    </div>
                </div>
                {!isSidebarCollapsed && (
                    <>
                        <button onClick={onNewProposal} className="new-proposal-btn">
                            + New Proposal
                        </button>

                        {/* Proposal Draft Section - Contains all proposals */}
                        <div className="expandable-section">
                            <div
                                className="section-header"
                                onClick={() => setIsDraftDrawerOpen(!isDraftDrawerOpen)}
                            >
                                <span className={`section-arrow ${isDraftDrawerOpen ? 'open' : ''}`}>
                                    <ChevronRight size={16} />
                                </span>
                                <FileText size={18} className="section-icon" />
                                <span className="section-title">Proposal Draft</span>
                            </div>
                            {isDraftDrawerOpen && (
                                <div className="section-content">
                                    {(() => {
                                        const categorized = categorizeProposals(proposals);
                                        return (
                                            <>
                                                {categorized.today.length > 0 && (
                                                    <div className="proposal-section">
                                                        <div className="proposal-section-header">Today</div>
                                                        {categorized.today.map(renderProposalItem)}
                                                    </div>
                                                )}
                                                {categorized.yesterday.length > 0 && (
                                                    <div className="proposal-section">
                                                        <div className="proposal-section-header">Yesterday</div>
                                                        {categorized.yesterday.map(renderProposalItem)}
                                                    </div>
                                                )}
                                                {categorized.past.length > 0 && (
                                                    <div className="proposal-section">
                                                        <div className="proposal-section-header">Past</div>
                                                        {categorized.past.map(renderProposalItem)}
                                                    </div>
                                                )}
                                                {proposals.length === 0 && (
                                                    <div className="empty-section">No drafts yet</div>
                                                )}
                                            </>
                                        );
                                    })()}
                                </div>
                            )}
                        </div>

                        {/* Proposal Revision Section */}
                        <div className="expandable-section">
                            <div
                                className="section-header"
                                onClick={() => setIsRevisionDrawerOpen(!isRevisionDrawerOpen)}
                            >
                                <span className={`section-arrow ${isRevisionDrawerOpen ? 'open' : ''}`}>
                                    <ChevronRight size={16} />
                                </span>
                                <FileCheck size={18} className="section-icon" />
                                <span className="section-title">Proposal Revision</span>
                            </div>
                            {isRevisionDrawerOpen && (
                                <div className="section-content">
                                    {myRevisions.length === 0 ? (
                                        <div className="empty-section">No revisions assigned to you</div>
                                    ) : (
                                        myRevisions.map(renderProposalItem)
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Active Tender Section */}
                        <div className="expandable-section">
                            <div
                                className="section-header"
                                onClick={() => {
                                    setIsTenderDrawerOpen(!isTenderDrawerOpen);
                                    if (!isTenderDrawerOpen && onActiveTenderSelect) {
                                        onActiveTenderSelect();
                                    }
                                }}
                            >
                                <span className={`section-arrow ${isTenderDrawerOpen ? 'open' : ''}`}>
                                    <ChevronRight size={16} />
                                </span>
                                <Briefcase size={18} className="section-icon" />
                                <span className="section-title">Active Tender</span>
                            </div>
                            {isTenderDrawerOpen && (
                                <div className="section-content">
                                    {activeTenders.length === 0 ? (
                                        <div className="empty-section">No active tenders</div>
                                    ) : (
                                        activeTenders.map(tender => (
                                            <div
                                                key={tender.id}
                                                className="proposal-item"
                                                onClick={() => {
                                                    if (onActiveTenderSelect) {
                                                        onActiveTenderSelect();
                                                    }
                                                }}
                                            >
                                                <div className="proposal-content">
                                                    <span className="proposal-title">
                                                        {tender.title}
                                                    </span>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}
                        </div>
                    </>
                )}
                {!isSidebarCollapsed && (
                    <div
                        className="sidebar-resize-handle"
                        onMouseDown={handleResizeStart}
                    />
                )}
                <div className="sidebar-footer">
                    <div className="user-profile">
                        <div
                            className="user-profile-header"
                            onClick={() => setShowProfileMenu(!showProfileMenu)}
                        >
                            <div className="user-avatar">
                                {getUserInitials(userEmail)}
                            </div>
                            {!isSidebarCollapsed && (
                                <div className="user-info">
                                    <div className="user-name">{getUserName(userEmail)}</div>
                                    <div className="user-email">{userEmail}</div>
                                </div>
                            )}
                            {!isSidebarCollapsed && (
                                <div className="profile-chevron">
                                    {showProfileMenu ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                </div>
                            )}
                        </div>
                        {showProfileMenu && !isSidebarCollapsed && (
                            <div className="profile-menu">
                                <div className="profile-menu-section">
                                    <Link to="/team" className="profile-menu-item" onClick={() => setShowProfileMenu(false)}>
                                        <User size={18} className="menu-icon" />
                                        <span>Profile</span>
                                    </Link>
                                </div>
                                <div className="profile-menu-divider"></div>
                                <div className="profile-menu-section">
                                    <button className="profile-menu-item logout-item" onClick={handleLogout}>
                                        <LogOut size={18} className="menu-icon" />
                                        <span>Logout</span>
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </aside>
            {/* Hidden element to pass sidebar width to parent via CSS variable */}
            <style>{`:root { --sidebar-width: ${currentWidth}px; }`}</style>
        </>
    );
}

// Hook to get the current sidebar width
export function useSidebarWidth() {
    const [width, setWidth] = useState(() => {
        const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (collapsed) return 60;
        const saved = localStorage.getItem('sidebarWidth');
        return saved ? parseInt(saved, 10) : 280;
    });

    useEffect(() => {
        const handleStorage = () => {
            const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            if (collapsed) {
                setWidth(60);
            } else {
                const saved = localStorage.getItem('sidebarWidth');
                setWidth(saved ? parseInt(saved, 10) : 280);
            }
        };

        window.addEventListener('storage', handleStorage);

        // Also listen for custom events for same-tab updates
        const interval = setInterval(handleStorage, 100);

        return () => {
            window.removeEventListener('storage', handleStorage);
            clearInterval(interval);
        };
    }, []);

    return width;
}
