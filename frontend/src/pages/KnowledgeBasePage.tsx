import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BookOpen,
  Search,
  UploadCloud,
  FileText,
  Trash2,
  CheckCircle2,
  Layers,
  Sparkles,
  ExternalLink,
  X
} from 'lucide-react';

import { apiClient } from '../api/client';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { KnowledgeDocument, RetrievedChunk } from '../types';

export const KnowledgeBasePage: React.FC = () => {
  const queryClient = useQueryClient();

  // Search Test Panel State
  const [searchQuery, setSearchQuery] = useState('How much does the Professional tier cost?');
  const [topK, setTopK] = useState(3);
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDocument | null>(null);

  // Upload State
  const [uploadCategory, setUploadCategory] = useState('General');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  // Queries
  const { data: documents, isLoading: isDocsLoading } = useQuery({
    queryKey: ['kbDocuments'],
    queryFn: apiClient.getDocuments,
  });

  const { data: searchResults, isFetching: isSearching, refetch: executeSearch } = useQuery({
    queryKey: ['kbSearch', searchQuery, topK],
    queryFn: () => apiClient.searchKnowledge(searchQuery, topK),
    enabled: false,
  });

  // Mutations
  const uploadMutation = useMutation({
    mutationFn: ({ file, category }: { file: File; category: string }) =>
      apiClient.uploadDocument(file, category),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['kbDocuments'] });
      setUploadStatus(`Indexed ${res.chunk_count} chunks for "${res.title}".`);
      setUploadFile(null);
      setTimeout(() => setUploadStatus(null), 3000);
    },
    onError: (err: any) => {
      setUploadStatus(`Error: ${err.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kbDocuments'] });
    },
  });

  const docs = documents || [];

  return (
    <div className="page-light space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Enterprise Knowledge Base & RAG</h1>
        <p className="page-description">
          Dense semantic vector indices, BM25 sparse keyword matching, and multi-format document ingestion
        </p>
      </div>

      {/* Top Row: Upload Dropzone & Hybrid Search Playground */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Upload Card (5 cols) */}
        <div className="surface-card space-y-4 p-4 sm:p-5 lg:col-span-5">
          <div className="flex items-center space-x-2 border-b border-slate-700 pb-3">
            <UploadCloud className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Ingest New Knowledge Document</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-300 mb-1">Target Category</label>
              <select
                value={uploadCategory}
                onChange={(e) => setUploadCategory(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
              >
                <option value="General">General Overview</option>
                <option value="Product">Product Capabilities</option>
                <option value="Pricing">Pricing & Commercials</option>
                <option value="Enterprise">Enterprise & Security</option>
                <option value="Integrations">Integrations & API</option>
                <option value="Objections">Objection Handling</option>
                <option value="Competitive">Competitive Intelligence</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 mb-1">Document File (.md, .txt, .pdf, .docx)</label>
              <div               className="cursor-pointer rounded-xl border-2 border-dashed border-[#d9deed] bg-[#f8f9fd] p-4 text-center transition-colors hover:border-indigo-400">
                <input
                  type="file"
                  accept=".md,.txt,.pdf,.docx,.doc"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs text-[#687391] file:mr-3 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-3 file:py-2 file:text-xs file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100"
                />
              </div>
            </div>

            {uploadStatus && (
              <div className="p-2.5 rounded-lg bg-indigo-950/60 border border-indigo-800 text-indigo-300 font-medium">
                {uploadStatus}
              </div>
            )}

            <button
              onClick={() => {
                if (uploadFile) {
                  uploadMutation.mutate({ file: uploadFile, category: uploadCategory });
                }
              }}
              disabled={!uploadFile || uploadMutation.isPending}
              className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg font-semibold transition-colors"
            >
              {uploadMutation.isPending ? 'Chunking & Embedding...' : 'Ingest Document'}
            </button>
          </div>
        </div>

        {/* Hybrid Search Playground (7 cols) */}
        <div className="surface-card space-y-4 p-4 sm:p-5 lg:col-span-7">
          <div className="flex items-center space-x-2 border-b border-slate-700 pb-3">
            <Search className="w-4 h-4 text-teal-400" />
            <h3 className="text-sm font-semibold text-white">Hybrid RAG Retrieval Benchmark Test</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ask any product, pricing, or technical question..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={() => executeSearch()}
                disabled={isSearching || !searchQuery.trim()}
                className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg font-semibold flex items-center space-x-1"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Search RRF</span>
              </button>
            </div>

            {/* Results Preview */}
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {isSearching ? (
                <LoadingSpinner size="sm" label="Searching ChromaDB & BM25 indices..." />
              ) : searchResults?.results && searchResults.results.length > 0 ? (
                searchResults.results.map((chunk: RetrievedChunk, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-slate-900/80 rounded-lg border border-slate-700/80 space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-teal-300">
                        {chunk.document_name}
                      </span>
                      <div className="flex items-center space-x-2">
                        <Badge variant="info" size="sm">
                          RRF: {chunk.rrf_score}
                        </Badge>
                        <Badge variant="neutral" size="sm">
                          {chunk.category}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-[11px] text-slate-300 line-clamp-2 italic">
                      "{chunk.text}"
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-slate-400 text-center py-6">
                  Enter a test query to test real-time fusion retrieval across knowledge chunks.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Ingested Documents Grid */}
      <div className="surface-card space-y-4 p-4 sm:p-5">
        <div className="flex items-center justify-between border-b border-slate-700 pb-3">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">
              Indexed Documents ({docs.length})
            </h3>
          </div>
          <span className="text-xs text-slate-400">
            Stored in ChromaDB 'nexusflow_kb'
          </span>
        </div>

        {isDocsLoading ? (
          <LoadingSpinner size="md" label="Loading knowledge docs..." className="py-12" />
        ) : docs.length === 0 ? (
          <p className="text-center text-xs text-slate-400 py-8">
            No knowledge documents found. Run the ingestion script or upload files above.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {docs.map((doc: KnowledgeDocument) => (
              <div
                key={doc.id}
                className="flex flex-col justify-between space-y-3 rounded-xl border border-[#e8eaf4] bg-[#fafbfe] p-4 transition-all hover:border-[#cdd3e8]"
              >
                <div className="space-y-1.5">
                  <div className="flex items-start justify-between gap-2">
                    <span className="line-clamp-2 text-xs font-bold text-white">{doc.title}</span>
                    <div className="flex shrink-0 flex-col items-end gap-1">
                      <Badge variant="primary" size="sm">
                        {doc.category}
                      </Badge>
                      <Badge variant={doc.status === 'indexed' ? 'success' : doc.status === 'error' ? 'danger' : 'neutral'} size="sm">
                        {doc.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                    <Layers className="w-3.5 h-3.5 text-teal-400" />
                    <span>{doc.chunk_count} Text Chunks</span>
                  </div>
                  <p className="text-[10px] text-slate-500 font-mono truncate">
                    Hash: {doc.content_hash.slice(0, 16)}...
                  </p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
                  <span className="text-[10px] text-slate-400">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </span>
                  <button
                    type="button"
                    aria-label={`Delete ${doc.title}`}
                    onClick={() => deleteMutation.mutate(doc.id)}
                    className="rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-rose-50 hover:text-rose-600"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
