/**
 * Empty State Component
 * Displays graceful UI when no data is available
 */

import React from 'react';

interface EmptyStateProps {
    icon?: string;
    title: string;
    description: string;
    action?: {
        label: string;
        onClick: () => void;
    };
}

export function EmptyState({ icon = '📚', title, description, action }: EmptyStateProps) {
    return (
        <div className="empty-state">
            <div className="empty-state__icon">{icon}</div>
            <h3 className="empty-state__title">{title}</h3>
            <p className="empty-state__description">{description}</p>
            {action && (
                <button className="btn btn--primary" onClick={action.onClick} style={{ marginTop: '1rem' }}>
                    {action.label}
                </button>
            )}
        </div>
    );
}

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
    return (
        <div className="loading">
            <div className="spinner" />
            <span style={{ marginLeft: '1rem', color: 'var(--color-text-secondary)' }}>{message}</span>
        </div>
    );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
    return (
        <div className="empty-state">
            <div className="empty-state__icon">⚠️</div>
            <h3 className="empty-state__title">Something went wrong</h3>
            <p className="empty-state__description">{message}</p>
            {onRetry && (
                <button className="btn btn--secondary" onClick={onRetry} style={{ marginTop: '1rem' }}>
                    Try Again
                </button>
            )}
        </div>
    );
}
