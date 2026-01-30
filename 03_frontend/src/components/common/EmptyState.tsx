import type { ReactNode } from 'react';

export type EmptyStateVariant =
  | 'no_data'
  | 'no_conversations'
  | 'no_costs'
  | 'no_qa_pairs'
  | 'error';

export type EmptyStateSize = 'normal' | 'compact';

export interface EmptyStateProps {
  variant: EmptyStateVariant;
  title?: string;
  description?: string;
  icon?: ReactNode;
  showIcon?: boolean;
  ctaLabel?: string;
  onCtaClick?: () => void;
  className?: string;
  size?: EmptyStateSize;
}

interface VariantConfig {
  title: string;
  description: string;
  icon: ReactNode;
}

const VARIANT_CONFIGS: Record<EmptyStateVariant, VariantConfig> = {
  no_data: {
    title: 'No data available',
    description: 'There is no data to display at this time.',
    icon: <DataIcon />,
  },
  no_conversations: {
    title: 'No conversations yet',
    description: 'Start a conversation to see activity here.',
    icon: <ConversationIcon />,
  },
  no_costs: {
    title: 'No cost data',
    description: 'Costs will appear here after processing queries.',
    icon: <CostIcon />,
  },
  no_qa_pairs: {
    title: 'No QA pairs',
    description: 'Import QA pairs to get started with your knowledge base.',
    icon: <QAIcon />,
  },
  error: {
    title: 'Something went wrong',
    description: 'An error occurred while loading data. Please try again.',
    icon: <ErrorIcon />,
  },
};

function DataIcon() {
  return (
    <svg
      data-testid="empty-state-icon"
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="8" y="12" width="48" height="40" rx="4" stroke="#D1D5DB" strokeWidth="2" />
      <path d="M8 24H56" stroke="#D1D5DB" strokeWidth="2" />
      <circle cx="32" cy="38" r="8" stroke="#D1D5DB" strokeWidth="2" />
      <path d="M28 38L31 41L36 35" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ConversationIcon() {
  return (
    <svg
      data-testid="empty-state-icon"
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M16 12H48C50.2091 12 52 13.7909 52 16V36C52 38.2091 50.2091 40 48 40H32L20 52V40H16C13.7909 40 12 38.2091 12 36V16C12 13.7909 13.7909 12 16 12Z"
        stroke="#D1D5DB"
        strokeWidth="2"
      />
      <path d="M24 24H40" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" />
      <path d="M24 32H36" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function CostIcon() {
  return (
    <svg
      data-testid="empty-state-icon"
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="32" cy="32" r="20" stroke="#D1D5DB" strokeWidth="2" />
      <path d="M32 20V44" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" />
      <path d="M26 26C26 26 28 24 32 24C36 24 38 27 38 29C38 32 34 33 32 33C30 33 26 34 26 37C26 40 28 42 32 42C36 42 38 40 38 40" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function QAIcon() {
  return (
    <svg
      data-testid="empty-state-icon"
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="12" y="8" width="40" height="48" rx="4" stroke="#D1D5DB" strokeWidth="2" />
      <path d="M20 20H44" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" />
      <path d="M20 28H44" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" />
      <path d="M20 36H36" stroke="#D1D5DB" strokeWidth="2" strokeLinecap="round" />
      <circle cx="32" cy="48" r="4" stroke="#D1D5DB" strokeWidth="2" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg
      data-testid="empty-state-icon"
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="32" cy="32" r="20" stroke="#EF4444" strokeWidth="2" />
      <path d="M32 22V36" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" />
      <circle cx="32" cy="42" r="2" fill="#EF4444" />
    </svg>
  );
}

export function EmptyState({
  variant,
  title,
  description,
  icon,
  showIcon = true,
  ctaLabel,
  onCtaClick,
  className = '',
  size = 'normal',
}: EmptyStateProps) {
  const config = VARIANT_CONFIGS[variant];
  const displayTitle = title ?? config.title;
  const displayDescription = description ?? config.description;
  const displayIcon = icon ?? config.icon;

  const sizeClass = size === 'compact' ? 'empty-state--compact' : 'empty-state--normal';

  return (
    <div
      role="status"
      className={`empty-state ${sizeClass} ${className}`.trim()}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: size === 'compact' ? '24px' : '48px',
        textAlign: 'center',
        color: '#6B7280',
      }}
    >
      {showIcon && (
        <div style={{ marginBottom: size === 'compact' ? '12px' : '24px' }}>
          {displayIcon}
        </div>
      )}

      <h3
        style={{
          margin: 0,
          marginBottom: '8px',
          fontSize: size === 'compact' ? '16px' : '20px',
          fontWeight: 600,
          color: '#374151',
        }}
      >
        {displayTitle}
      </h3>

      <p
        style={{
          margin: 0,
          marginBottom: ctaLabel ? '16px' : 0,
          fontSize: size === 'compact' ? '14px' : '16px',
          maxWidth: '360px',
        }}
      >
        {displayDescription}
      </p>

      {ctaLabel && onCtaClick && (
        <button
          type="button"
          onClick={onCtaClick}
          style={{
            padding: '10px 20px',
            fontSize: '14px',
            fontWeight: 500,
            color: 'white',
            backgroundColor: '#3B82F6',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          {ctaLabel}
        </button>
      )}
    </div>
  );
}
