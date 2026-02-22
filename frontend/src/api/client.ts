import axios from 'axios';

export const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    headers: { 'Content-Type': 'application/json' },
});

// Add token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Auth API
export const authApi = {
    login: async (email: string, password: string) => {
        const res = await api.post('/auth/login', { email, password });
        return res.data;
    },
    register: async (email: string, password: string, name: string, organizationName: string, organizationNif: string) => {
        const res = await api.post('/auth/register', {
            email,
            password,
            name,
            organization_name: organizationName,
            organization_nif: organizationNif
        });
        return res.data;
    },
    logout: () => {
        localStorage.removeItem('token');
    },
};

// Proposals API
export const proposalsApi = {
    list: async () => {
        const res = await api.get('/proposals');
        return res.data;
    },
    create: async (title: string) => {
        const res = await api.post('/proposals', { title, content: '' });
        return res.data;
    },
    get: async (id: string) => {
        const res = await api.get(`/proposals/${id}`);
        return res.data;
    },
    iterate: async (id: string, userInput: string) => {
        const res = await api.post(`/proposals/${id}/iterate`, { user_input: userInput });
        return res.data;
    },
    submit: async (id: string) => {
        const res = await api.post(`/proposals/${id}/submit_draft`);
        return res.data;
    },
    delete: async (id: string) => {
        const res = await api.delete(`/proposals/${id}`);
        return res.data;
    },
    pin: async (id: string) => {
        const res = await api.post(`/proposals/${id}/pin`);
        return res.data;
    },
    rename: async (id: string, title: string) => {
        const res = await api.patch(`/proposals/${id}`, { title });
        return res.data;
    },
    // Chat with file upload support
    chat: async (id: string, message: string, files?: File[]) => {
        const formData = new FormData();
        formData.append('message', message);

        if (files && files.length > 0) {
            files.forEach(file => {
                formData.append('files', file);
            });
        }

        const res = await api.post(`/proposals/${id}/chat`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return res.data;
    },
    getMessages: async (id: string) => {
        const res = await api.get(`/proposals/${id}/messages`);
        return res.data;
    },
    // Get all revisions assigned to current user
    getMyRevisions: async () => {
        const res = await api.get('/my-revisions');
        return res.data;
    },
    // Get the user's personalized revision for a specific proposal
    getMyProposalRevision: async (id: string) => {
        const res = await api.get(`/proposals/${id}/my-revision`);
        return res.data;
    },
};

// Organizations API
export const organizationsApi = {
    get: async (orgId: string = "default") => {
        const res = await api.get(`/organizations/${orgId}`);
        return res.data;
    },
    listMembers: async (orgId: string = "default", role?: string) => {
        const res = await api.get(`/organizations/${orgId}/members`, {
            params: role ? { role } : {}
        });
        return res.data;
    },
    getAvailableUsers: async (orgId: string = "default") => {
        const res = await api.get(`/organizations/${orgId}/available-users`);
        return res.data;
    },
    addMember: async (orgId: string, userId: string, role: string) => {
        const res = await api.post(`/organizations/${orgId}/members`, { user_id: userId, role });
        return res.data;
    },
    updateMemberRole: async (orgId: string, memberId: string, role: string) => {
        const res = await api.patch(`/organizations/${orgId}/members/${memberId}`, { role });
        return res.data;
    },
    removeMember: async (orgId: string, memberId: string) => {
        const res = await api.delete(`/organizations/${orgId}/members/${memberId}`);
        return res.data;
    },
};

// Active Tenders API
export const activeTendersApi = {
    list: async () => {
        const res = await api.get('/active-tenders');
        return res.data;
    },
    get: async (id: string) => {
        const res = await api.get(`/active-tenders/${id}`);
        return res.data;
    },
    publishTender: async (proposalId: string) => {
        const res = await api.post(`/proposals/${proposalId}/publish_tender`);
        return res.data;
    },
};

