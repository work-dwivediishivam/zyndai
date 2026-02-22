import React from 'react';
import { Send, Paperclip, X } from 'lucide-react';

interface SearchInputProps {
    input: string;
    setInput: (value: string) => void;
    loading: boolean;
    selectedFiles: File[];
    fileInputRef: React.RefObject<HTMLInputElement | null>;
    onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onRemoveFile: (index: number) => void;
    onSubmit: (e: React.FormEvent) => void;
    placeholder?: string;
    className?: string;
    sidebarWidth: number;
}

export function SearchInput({
    input,
    setInput,
    loading,
    selectedFiles,
    fileInputRef,
    onFileSelect,
    onRemoveFile,
    onSubmit,
    placeholder = "Start writing your proposal...",
    className = "home-search-form",
    sidebarWidth
}: SearchInputProps) {
    return (
        <form
            onSubmit={onSubmit}
            className={className}
            style={{
                left: `calc(${sidebarWidth}px + (100vw - ${sidebarWidth}px) / 2)`,
                width: `calc(100vw - ${sidebarWidth}px - 6rem)`
            }}
        >
            <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.xlsx,.xls,image/*"
                onChange={onFileSelect}
                style={{ display: 'none' }}
            />

            {selectedFiles.length > 0 && (
                <div className="file-chips-container">
                    {selectedFiles.map((file, index) => (
                        <div key={index} className="file-chip">
                            <Paperclip size={14} />
                            <span>{file.name}</span>
                            <button
                                type="button"
                                onClick={() => onRemoveFile(index)}
                                className="file-chip-remove"
                            >
                                <X size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <div className="chat-input-row">
                <textarea
                    value={input}
                    onChange={(e) => {
                        setInput(e.target.value);
                        e.target.style.height = 'auto';
                        e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
                    }}
                    placeholder={placeholder}
                    disabled={loading}
                    rows={1}
                    className="chat-textarea"
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            if (!loading && input.trim()) {
                                (e.target as HTMLTextAreaElement).form?.requestSubmit();
                            }
                        }
                    }}
                />
                <button
                    type="button"
                    className="attachment-icon-btn"
                    onClick={() => {
                        fileInputRef.current?.click();
                    }}
                    title="Attach file (PDF, DOCX, Excel, Images)"
                >
                    <Paperclip size={20} />
                </button>
                <button type="submit" disabled={loading || !input.trim()} className="send-icon-btn">
                    {loading ? (
                        <span className="loading-spinner">...</span>
                    ) : (
                        <Send size={20} />
                    )}
                </button>
            </div>
        </form>
    );
}
