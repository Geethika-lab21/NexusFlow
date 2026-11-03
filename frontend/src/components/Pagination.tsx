import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  total: number;
  skip: number;
  limit: number;
  onPageChange: (newSkip: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  total,
  skip,
  limit,
  onPageChange,
}) => {
  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const startItem = total === 0 ? 0 : skip + 1;
  const endItem = Math.min(skip + limit, total);

  return (
    <div className="flex flex-col items-start justify-between gap-3 rounded-xl border border-[#e7e9f4] bg-[#fafbfe] px-4 py-3 sm:flex-row sm:items-center">
      <div className="text-xs text-[#74809b]">
        Showing <span className="font-semibold text-[#394665]">{startItem}</span> to{' '}
        <span className="font-semibold text-[#394665]">{endItem}</span> of{' '}
        <span className="font-semibold text-[#394665]">{total}</span> results
      </div>

      <div className="flex items-center space-x-2">
        <button
          onClick={() => onPageChange(Math.max(0, skip - limit))}
          disabled={currentPage <= 1}
          aria-label="Previous page"
          className="rounded-lg border border-[#e0e4f0] bg-white p-1.5 text-[#687391] transition-colors hover:bg-[#f3f4fc] hover:text-[#394665] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <span className="px-2 text-xs font-medium text-[#596583]">
          Page {currentPage} of {totalPages}
        </span>

        <button
          onClick={() => onPageChange(skip + limit)}
          disabled={currentPage >= totalPages}
          aria-label="Next page"
          className="rounded-lg border border-[#e0e4f0] bg-white p-1.5 text-[#687391] transition-colors hover:bg-[#f3f4fc] hover:text-[#394665] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
