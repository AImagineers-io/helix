import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyState, EmptyStateVariant } from '../EmptyState';

describe('EmptyState', () => {
  describe('rendering', () => {
    it('should render with default message', () => {
      render(<EmptyState variant="no_data" />);

      expect(screen.getByText('No data available')).toBeInTheDocument();
    });

    it('should render custom title', () => {
      render(<EmptyState variant="no_data" title="Custom Title" />);

      expect(screen.getByText('Custom Title')).toBeInTheDocument();
    });

    it('should render custom description', () => {
      render(<EmptyState variant="no_data" description="Custom description text" />);

      expect(screen.getByText('Custom description text')).toBeInTheDocument();
    });
  });

  describe('variants', () => {
    it('should render no_data variant with appropriate content', () => {
      render(<EmptyState variant="no_data" />);

      expect(screen.getByText('No data available')).toBeInTheDocument();
      expect(screen.getByTestId('empty-state-icon')).toBeInTheDocument();
    });

    it('should render no_conversations variant with appropriate content', () => {
      render(<EmptyState variant="no_conversations" />);

      expect(screen.getByText('No conversations yet')).toBeInTheDocument();
      expect(screen.getByText(/start a conversation/i)).toBeInTheDocument();
    });

    it('should render no_costs variant with appropriate content', () => {
      render(<EmptyState variant="no_costs" />);

      expect(screen.getByText('No cost data')).toBeInTheDocument();
      expect(screen.getByText(/costs will appear/i)).toBeInTheDocument();
    });

    it('should render no_qa_pairs variant with appropriate content', () => {
      render(<EmptyState variant="no_qa_pairs" />);

      expect(screen.getByText('No QA pairs')).toBeInTheDocument();
    });

    it('should render error variant with appropriate content', () => {
      render(<EmptyState variant="error" />);

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });
  });

  describe('call to action', () => {
    it('should render CTA button when provided', () => {
      const onCtaClick = vi.fn();
      render(
        <EmptyState
          variant="no_qa_pairs"
          ctaLabel="Import QA pairs"
          onCtaClick={onCtaClick}
        />
      );

      expect(screen.getByRole('button', { name: 'Import QA pairs' })).toBeInTheDocument();
    });

    it('should call onCtaClick when CTA button is clicked', () => {
      const onCtaClick = vi.fn();
      render(
        <EmptyState
          variant="no_qa_pairs"
          ctaLabel="Import QA pairs"
          onCtaClick={onCtaClick}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: 'Import QA pairs' }));

      expect(onCtaClick).toHaveBeenCalledTimes(1);
    });

    it('should not render CTA button when ctaLabel is not provided', () => {
      render(<EmptyState variant="no_data" />);

      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });
  });

  describe('icon customization', () => {
    it('should render custom icon when provided', () => {
      const CustomIcon = () => <span data-testid="custom-icon">Custom</span>;
      render(<EmptyState variant="no_data" icon={<CustomIcon />} />);

      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });

    it('should hide icon when showIcon is false', () => {
      render(<EmptyState variant="no_data" showIcon={false} />);

      expect(screen.queryByTestId('empty-state-icon')).not.toBeInTheDocument();
    });
  });

  describe('styling', () => {
    it('should apply custom className', () => {
      const { container } = render(<EmptyState variant="no_data" className="custom-class" />);

      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('should support compact size', () => {
      const { container } = render(<EmptyState variant="no_data" size="compact" />);

      expect(container.firstChild).toHaveClass('empty-state--compact');
    });

    it('should default to normal size', () => {
      const { container } = render(<EmptyState variant="no_data" />);

      expect(container.firstChild).toHaveClass('empty-state--normal');
    });
  });

  describe('accessibility', () => {
    it('should have appropriate aria attributes', () => {
      render(<EmptyState variant="no_data" />);

      const emptyState = screen.getByRole('status');
      expect(emptyState).toBeInTheDocument();
    });

    it('should have accessible button when CTA is present', () => {
      const onCtaClick = vi.fn();
      render(
        <EmptyState
          variant="no_qa_pairs"
          ctaLabel="Import QA pairs"
          onCtaClick={onCtaClick}
        />
      );

      expect(screen.getByRole('button', { name: 'Import QA pairs' })).toBeInTheDocument();
    });
  });
});
