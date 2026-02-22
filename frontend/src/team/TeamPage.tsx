import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, FileText, Plus, ChevronUp, ChevronDown, MoreVertical, Edit, Trash2 } from 'lucide-react';
import { organizationsApi, proposalsApi } from '../api/client';
import { Sidebar, useSidebarWidth } from '../components/Sidebar';
import '../proposals/HomePage.css';
import './TeamPage.css';

interface Organization {
    id: string;
    name: string;
    nif: string;
    members_count: number;
}

interface Member {
    id: string;
    email: string;
    name: string;
    role: string;
    department?: string;
}

interface AvailableUser {
    id: string;
    name: string;
    email: string;
}

export function TeamPage() {
    const [organization, setOrganization] = useState<Organization | null>(null);
    const [members, setMembers] = useState<Member[]>([]);
    const [selectedRole, setSelectedRole] = useState<string>('All');
    const [showAddMember, setShowAddMember] = useState(false);
    const [availableUsers, setAvailableUsers] = useState<AvailableUser[]>([]);
    const [selectedUserId, setSelectedUserId] = useState('');
    const [newMemberRole, setNewMemberRole] = useState('viewer');
    const [openMenuId, setOpenMenuId] = useState<string | null>(null);
    const [editingMemberId, setEditingMemberId] = useState<string | null>(null);
    const [editingRole, setEditingRole] = useState<string>('');
    const [sortColumn, setSortColumn] = useState<string | null>(null);
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
    const [showNewForm, setShowNewForm] = useState(false);
    const [newTitle, setNewTitle] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const sidebarWidth = useSidebarWidth();

    useEffect(() => {
        loadOrganization();
        loadMembers();
    }, [selectedRole]);

    useEffect(() => {
        if (showAddMember) {
            loadAvailableUsers();
        }
    }, [showAddMember]);

    const loadOrganization = async () => {
        try {
            const data = await organizationsApi.get();
            setOrganization(data);
        } catch (err) {
            console.error('Failed to load organization');
        }
    };

    const loadMembers = async () => {
        try {
            const data = await organizationsApi.listMembers('default', selectedRole === 'All' ? undefined : selectedRole);
            setMembers(data);
        } catch (err) {
            console.error('Failed to load members');
        }
    };

    const loadAvailableUsers = async () => {
        try {
            const data = await organizationsApi.getAvailableUsers();
            setAvailableUsers(data);
        } catch (err) {
            console.error('Failed to load available users');
        }
    };

    const handleAddMember = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedUserId) return;
        try {
            await organizationsApi.addMember('default', selectedUserId, newMemberRole);
            setSelectedUserId('');
            setNewMemberRole('viewer');
            setShowAddMember(false);
            await loadMembers();
            await loadOrganization();
        } catch (err: any) {
            console.error('Failed to add member');
            alert(err?.response?.data?.detail || 'Failed to add member');
        }
    };

    const handleRemoveMember = async (memberId: string) => {
        if (!confirm('Are you sure you want to remove this member?')) return;
        try {
            await organizationsApi.removeMember('default', memberId);
            loadMembers();
            loadOrganization();
            setOpenMenuId(null);
        } catch (err) {
            console.error('Failed to remove member');
        }
    };

    const handleEditRole = (member: Member) => {
        setEditingMemberId(member.id);
        setEditingRole(member.role);
        setOpenMenuId(null);
    };

    const handleSaveRole = async (memberId: string) => {
        try {
            await organizationsApi.updateMemberRole('default', memberId, editingRole);
            setEditingMemberId(null);
            setEditingRole('');
            await loadMembers();
        } catch (err: any) {
            console.error('Failed to update role');
            alert(err?.response?.data?.detail || 'Failed to update role');
        }
    };

    const handleCancelEdit = () => {
        setEditingMemberId(null);
        setEditingRole('');
    };

    const handleSort = (column: string) => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortColumn(column);
            setSortDirection('asc');
        }
    };

    const sortedMembers = [...members].sort((a, b) => {
        if (!sortColumn) return 0;
        let aVal: string = (a[sortColumn as keyof Member] ?? '') as string;
        let bVal: string = (b[sortColumn as keyof Member] ?? '') as string;
        if (sortColumn === 'name') {
            aVal = a.name;
            bVal = b.name;
        }
        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
        return 0;
    });

    const getUserInitials = (name: string) => {
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    };

    const handleNewProposal = () => {
        setShowNewForm(true);
    };

    const roles = ['All', 'Owner', 'Administrator', 'Editor', 'Viewer'];

    return (
        <div className="home-container">
            <Sidebar onNewProposal={handleNewProposal} />

            <main
                className="main-content"
                style={{ marginLeft: `${sidebarWidth}px` }}
            >
                {showNewForm && (
                    <div className="modal-overlay" onClick={() => setShowNewForm(false)}>
                        <div className="modal" onClick={(e) => e.stopPropagation()}>
                            <h3>Create New Proposal</h3>
                            <form onSubmit={async (e) => {
                                e.preventDefault();
                                if (!newTitle.trim()) return;
                                setLoading(true);
                                try {
                                    await proposalsApi.create(newTitle);
                                    setNewTitle('');
                                    setShowNewForm(false);
                                    navigate('/');
                                } catch (err) {
                                    console.error('Failed to create proposal');
                                } finally {
                                    setLoading(false);
                                }
                            }}>
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
                <div className="team-page">
                    <div className="team-header">
                        <h1>Team Management</h1>
                    </div>

                    <div className="org-info-cards">
                        <div className="org-info-card">
                            <FileText size={24} className="org-card-icon" />
                            <div className="org-card-content">
                                <div className="org-card-label">Name</div>
                                <div className="org-card-value">{organization?.name || 'Loading...'}</div>
                            </div>
                        </div>
                        <div className="org-info-card">
                            <FileText size={24} className="org-card-icon" />
                            <div className="org-card-content">
                                <div className="org-card-label">NIF</div>
                                <div className="org-card-value">{organization?.nif || '-'}</div>
                            </div>
                        </div>
                        <div className="org-info-card">
                            <Users size={24} className="org-card-icon" />
                            <div className="org-card-content">
                                <div className="org-card-label">Members</div>
                                <div className="org-card-value">{organization?.members_count || 0}</div>
                            </div>
                        </div>
                    </div>

                    <div className="members-section">
                        <div className="members-header">
                            <h2 className="members-title">Members of the organization</h2>
                            <div className="members-controls">
                                <div className="role-filters">
                                    {roles.map(role => (
                                        <button
                                            key={role}
                                            className={`role-filter ${selectedRole === role ? 'active' : ''}`}
                                            onClick={() => setSelectedRole(role)}
                                        >
                                            {role}
                                        </button>
                                    ))}
                                </div>
                                <button
                                    className="add-member-btn"
                                    onClick={() => setShowAddMember(true)}
                                >
                                    <Plus size={20} />
                                </button>
                            </div>
                        </div>

                        {showAddMember && (
                            <div className="add-member-modal">
                                <div className="add-member-form">
                                    <h3>Add Member</h3>
                                    <form onSubmit={handleAddMember}>
                                        <div className="form-group">
                                            <label>Select User</label>
                                            <select
                                                value={selectedUserId}
                                                onChange={(e) => setSelectedUserId(e.target.value)}
                                                required
                                                autoFocus
                                            >
                                                <option value="">Choose a user...</option>
                                                {availableUsers.map(user => (
                                                    <option key={user.id} value={user.id}>
                                                        {user.name} ({user.email})
                                                    </option>
                                                ))}
                                            </select>
                                            {availableUsers.length === 0 && (
                                                <p className="no-users-hint">No users available. Users must register first without an organization.</p>
                                            )}
                                        </div>
                                        <div className="form-group">
                                            <label>Role</label>
                                            <select
                                                value={newMemberRole}
                                                onChange={(e) => setNewMemberRole(e.target.value)}
                                            >
                                                <option value="viewer">Viewer</option>
                                                <option value="editor">Editor</option>
                                                <option value="admin">Administrator</option>
                                            </select>
                                        </div>
                                        <div className="form-actions">
                                            <button type="button" onClick={() => setShowAddMember(false)}>Cancel</button>
                                            <button type="submit" disabled={!selectedUserId}>Add Member</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        )}

                        <div className="members-table-container">
                            <table className="members-table">
                                <thead>
                                    <tr>
                                        <th onClick={() => handleSort('name')} className="sortable">
                                            Name
                                            {sortColumn === 'name' && (
                                                sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />
                                            )}
                                        </th>
                                        <th>Department</th>
                                        <th>Position</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sortedMembers.map(member => (
                                        <tr key={member.id}>
                                            <td>
                                                <div className="member-info">
                                                    <div className="member-avatar">
                                                        {getUserInitials(member.name)}
                                                    </div>
                                                    <div className="member-details">
                                                        <div className="member-name">{member.name}</div>
                                                        <div className="member-email">{member.email}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="department-cell">
                                                <span className="member-department">{member.department || '-'}</span>
                                            </td>
                                            <td className="position-cell">
                                                {editingMemberId === member.id ? (
                                                    <div className="inline-edit">
                                                        <select
                                                            value={editingRole}
                                                            onChange={(e) => setEditingRole(e.target.value)}
                                                            className="role-select"
                                                        >
                                                            <option value="viewer">Viewer</option>
                                                            <option value="editor">Editor</option>
                                                            <option value="admin">Administrator</option>
                                                            <option value="owner">Owner</option>
                                                        </select>
                                                        <button
                                                            className="save-btn"
                                                            onClick={() => handleSaveRole(member.id)}
                                                        >
                                                            Save
                                                        </button>
                                                        <button
                                                            className="cancel-btn"
                                                            onClick={handleCancelEdit}
                                                        >
                                                            Cancel
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <span className="member-role">{member.role}</span>
                                                )}
                                            </td>
                                            <td className="actions-cell">
                                                <div className="member-actions">
                                                    <button
                                                        className="action-menu-btn"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setOpenMenuId(openMenuId === member.id ? null : member.id);
                                                        }}
                                                    >
                                                        <MoreVertical size={18} />
                                                    </button>
                                                    {openMenuId === member.id && (
                                                        <div className="action-menu-dropdown">
                                                            <button
                                                                className="action-menu-item"
                                                                onClick={() => handleEditRole(member)}
                                                            >
                                                                <Edit size={16} />
                                                                <span>Edit</span>
                                                            </button>
                                                            <button
                                                                className="action-menu-item delete"
                                                                onClick={() => handleRemoveMember(member.id)}
                                                            >
                                                                <Trash2 size={16} />
                                                                <span>Remove</span>
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <div className="pagination">
                            <span>Page 1 of 1</span>
                            <div className="pagination-buttons">
                                <button disabled>&lt;</button>
                                <button disabled>&gt;</button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
