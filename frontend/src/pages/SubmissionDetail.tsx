import React, { useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api, { runAIAssessment, downloadReport } from '../services/api';
import type { Submission, CountryRule, DocumentCategory, Document } from '../types';
import { DOCUMENT_CATEGORY_LABELS } from '../types';
import EligibilityScoreCard from '../components/EligibilityScoreCard';
import AIAnalysisPanel from '../components/AIAnalysisPanel';
import RiskBadge from '../components/RiskBadge';
import {
  ArrowLeft, UploadCloud, FileCheck, FileWarning, FileClock,
  Download, Play, Loader2, Info, CheckCircle, AlertTriangle,
  XCircle, Eye, ChevronDown, ChevronUp, Sparkles
} from 'lucide-react';

const ALL_DOCUMENT_TYPES: Array<{ value: DocumentCategory; label: string }> = [
  { value: 'passport', label: 'Passport' },
  { value: 'bank_statement', label: 'Bank Statement' },
  { value: 'salary_slip', label: 'Salary Slip' },
  { value: 'employment_letter', label: 'Employment Letter' },
  { value: 'tax_return', label: 'Tax Return / ITR' },
  { value: 'travel_history', label: 'Travel History' },
  { value: 'invitation_letter', label: 'Invitation Letter' },
  { value: 'hotel_booking', label: 'Hotel Booking' },
  { value: 'flight_booking', label: 'Flight Booking / Reservation' },
  { value: 'cover_letter', label: 'Cover Letter' },
  { value: 'other', label: 'Other Document' },
];

export default function SubmissionDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedDocType, setSelectedDocType] = useState<DocumentCategory | ''>('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [validationLoading, setValidationLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'docs' | 'ocr'>('docs');

  // Fetch Submission detail — refresh every 5s to pick up processing updates
  const { data: submission, isLoading, error } = useQuery<Submission>({
    queryKey: ['submission', id],
    queryFn: async () => {
      const response = await api.get(`submissions/${id}/`);
      return response.data;
    },
    refetchInterval: 5000,
  });

  // Fetch Country Rules for required docs checklist
  const { data: rulesList = [] } = useQuery<CountryRule[]>({
    queryKey: ['country-rules'],
    queryFn: async () => {
      const response = await api.get('country-rules/');
      return response.data;
    },
  });

  // Run rules validation
  const runValidationMutation = useMutation({
    mutationFn: async () => {
      setValidationLoading(true);
      const response = await api.post(`submissions/${id}/validate_rules/`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['submission', id] }),
    onError: (err: any) => {
      console.error(err);
      alert('Failed to run rules validation.');
    },
    onSettled: () => setValidationLoading(false),
  });

  // Run full AI assessment
  const runAIAssessmentMutation = useMutation({
    mutationFn: async () => {
      if (!id) throw new Error('No submission ID');
      setAiLoading(true);
      return await runAIAssessment(id);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['submission', id] }),
    onError: (err: any) => {
      console.error(err);
      alert(err?.response?.data?.detail || 'AI assessment failed.');
    },
    onSettled: () => setAiLoading(false),
  });

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mr-3" />
        <span>Loading application audit panel...</span>
      </div>
    );
  }

  if (error || !submission) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl text-center">
        Failed to fetch application details. Ensure submission ID is correct.
      </div>
    );
  }

  const matchingRule = rulesList.find(
    (r) =>
      r.country.toLowerCase() === submission.country.toLowerCase() &&
      r.visa_type.toLowerCase() === submission.visa_type.toLowerCase()
  );

  const requiredDocuments = matchingRule?.required_documents || ['Passport', 'Bank Statement'];
  const uploadedDocs = submission.documents || [];
  const uploadedNames = uploadedDocs.map((d) => d.name.toLowerCase().trim());

  // File upload handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) await uploadFileToServer(e.dataTransfer.files[0]);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) await uploadFileToServer(e.target.files[0]);
  };

  const uploadFileToServer = async (file: File) => {
    if (!selectedDocType) {
      alert('Please select the Document Type from the dropdown first.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert('File size exceeds 10MB limit.');
      return;
    }
    const allowedExtensions = ['.pdf', '.png', '.jpg', '.jpeg', '.docx'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      alert('Invalid file type. Supported: PDF, PNG, JPG, JPEG, DOCX');
      return;
    }

    setUploading(true);
    setUploadProgress(15);

    const label = ALL_DOCUMENT_TYPES.find((d) => d.value === selectedDocType)?.label || selectedDocType;
    const formData = new FormData();
    formData.append('submission', submission.id);
    formData.append('name', label);
    formData.append('category', selectedDocType);
    formData.append('file', file);

    try {
      setUploadProgress(45);
      await api.post('documents/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadProgress(90);
      queryClient.invalidateQueries({ queryKey: ['submission', id] });
      setSelectedDocType('');
      // Auto-run validation after upload
      runValidationMutation.mutate();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDownloadReport = async () => {
    try {
      await downloadReport(submission.id, submission.application_id);
    } catch {
      alert('Failed to download report. Please run validation first.');
    }
  };

  const toggleDocExpand = (docId: string) =>
    setExpandedDoc(expandedDoc === docId ? null : docId);

  const report = submission.validation_report;
  const eligibility = submission.eligibility_score;
  const score = report?.score ?? 0;
  const reportStatus = report?.status ?? 'Unchecked';

  let scoreColor = 'text-slate-400 border-slate-700 bg-slate-800/20';
  let bannerColor = 'bg-slate-900 border-slate-800 text-slate-400';
  let BannerIcon = Info;

  if (reportStatus === 'Passed') {
    scoreColor = 'text-emerald-400 border-emerald-500/30 bg-emerald-500/5';
    bannerColor = 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400';
    BannerIcon = CheckCircle;
  } else if (reportStatus === 'Warning') {
    scoreColor = 'text-amber-400 border-amber-500/30 bg-amber-500/5';
    bannerColor = 'bg-amber-500/5 border-amber-500/20 text-amber-400';
    BannerIcon = AlertTriangle;
  } else if (reportStatus === 'Failed') {
    scoreColor = 'text-rose-400 border-rose-500/30 bg-rose-500/5';
    bannerColor = 'bg-rose-500/5 border-rose-500/20 text-rose-400';
    BannerIcon = XCircle;
  }

  const processingStatusConfig = {
    pending: { color: '#94a3b8', label: 'Pending' },
    processing: { color: '#818cf8', label: 'Processing...' },
    completed: { color: '#10b981', label: 'Assessed' },
    failed: { color: '#ef4444', label: 'Failed' },
  }[submission.processing_status] || { color: '#94a3b8', label: 'Pending' };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800/40 pb-4">
        <div className="flex items-center gap-3">
          <Link
            to="/submissions"
            className="p-2 bg-slate-800/60 hover:bg-slate-700/60 rounded-lg text-slate-400 hover:text-slate-200 transition-all border border-slate-800"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-slate-100">Application Audit Panel</h1>
              <span className="text-xs font-bold text-indigo-400 bg-indigo-400/10 border border-indigo-400/20 px-2 py-0.5 rounded-full">
                {submission.application_id}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {submission.client_detail.name} · {submission.country} · {submission.visa_type}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto flex-wrap">
          {/* Processing status pill */}
          <span style={{
            padding: '4px 12px',
            borderRadius: 99,
            fontSize: 11,
            fontWeight: 700,
            color: processingStatusConfig.color,
            background: `${processingStatusConfig.color}18`,
            border: `1px solid ${processingStatusConfig.color}40`,
          }}>
            {processingStatusConfig.label}
          </span>

          {/* Run Rules Validation */}
          <button
            id="run-validation-btn"
            onClick={() => runValidationMutation.mutate()}
            disabled={validationLoading || uploadedDocs.length === 0}
            className="flex-1 sm:flex-initial bg-slate-800 hover:bg-slate-700 disabled:opacity-50 border border-slate-700 text-slate-200 rounded-lg py-2 px-4 font-semibold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer"
          >
            {validationLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            Run Rules Check
          </button>

          {/* Run AI Assessment — primary CTA */}
          <button
            id="run-ai-assessment-btn"
            onClick={() => runAIAssessmentMutation.mutate()}
            disabled={aiLoading || uploadedDocs.length === 0}
            className="flex-1 sm:flex-initial bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white rounded-lg py-2 px-4 font-semibold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-lg shadow-indigo-600/20"
          >
            {aiLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            {aiLoading ? 'Analyzing...' : 'Run AI Assessment'}
          </button>

          {/* Download Report */}
          {report && (
            <button
              id="download-report-btn"
              onClick={handleDownloadReport}
              className="flex-1 sm:flex-initial bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg py-2 px-4 font-semibold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              Download Report
            </button>
          )}
        </div>
      </div>

      {/* Client Info Strip */}
      <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl grid grid-cols-2 md:grid-cols-5 gap-4">
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">Applicant</span>
          <span className="text-xs font-bold text-slate-200">{submission.client_detail.name}</span>
        </div>
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">Passport</span>
          <span className="text-xs font-bold text-indigo-400">{submission.client_detail.passport_number}</span>
        </div>
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">Destination</span>
          <span className="text-xs font-bold text-slate-200">{submission.country} · {submission.visa_type}</span>
        </div>
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">Application ID</span>
          <span className="text-xs font-bold text-indigo-400">{submission.application_id}</span>
        </div>
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">AI Risk</span>
          {eligibility ? (
            <RiskBadge risk={eligibility.risk_level} size="sm" />
          ) : (
            <span className="text-xs text-slate-500">Not assessed</span>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Document Checklist & Uploader */}
          <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl space-y-5">
            <h2 className="text-sm font-bold text-slate-200 pb-2 border-b border-slate-800/40">
              Checklist &amp; Document Uploader
            </h2>

            {/* Required Docs Checklist */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {requiredDocuments.map((reqDoc: string, idx: number) => {
                const isUploaded = uploadedNames.includes(reqDoc.toLowerCase().trim());
                const matchingDoc = uploadedDocs.find(
                  (d) => d.name.toLowerCase().trim() === reqDoc.toLowerCase().trim()
                );
                return (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border flex items-center justify-between ${
                      isUploaded
                        ? matchingDoc?.status === 'Valid'
                          ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-300'
                          : 'bg-rose-500/5 border-rose-500/20 text-rose-300'
                        : 'bg-slate-900/40 border-slate-800/60 text-slate-400'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {isUploaded ? (
                        matchingDoc?.status === 'Valid' ? (
                          <FileCheck className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <FileWarning className="w-4 h-4 text-rose-400" />
                        )
                      ) : (
                        <FileClock className="w-4 h-4 text-slate-500" />
                      )}
                      <span className="text-xs font-bold">{reqDoc}</span>
                    </div>
                    <span className="text-[10px] font-semibold">
                      {isUploaded ? matchingDoc?.status : 'Missing'}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Uploader */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center gap-3">
                <select
                  value={selectedDocType}
                  onChange={(e) => setSelectedDocType(e.target.value as DocumentCategory | '')}
                  className="w-full max-w-xs bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-300 cursor-pointer font-semibold"
                >
                  <option value="">-- Select Document Category --</option>
                  {ALL_DOCUMENT_TYPES.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => selectedDocType && fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center flex flex-col items-center justify-center transition-all ${
                  !selectedDocType
                    ? 'opacity-40 cursor-not-allowed border-slate-800'
                    : dragActive
                    ? 'border-indigo-500 bg-indigo-500/5 cursor-copy'
                    : 'border-slate-800 hover:border-indigo-500/40 hover:bg-slate-900/10 cursor-pointer'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.png,.jpg,.jpeg,.docx"
                  className="hidden"
                  disabled={!selectedDocType}
                />
                <UploadCloud className={`w-8 h-8 mb-3 ${dragActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                <p className="text-xs font-bold text-slate-300">
                  {selectedDocType
                    ? `Upload ${ALL_DOCUMENT_TYPES.find((d) => d.value === selectedDocType)?.label}`
                    : 'Select a document category above'}
                </p>
                <p className="text-[10px] text-slate-500 mt-1.5">
                  Drag &amp; drop, or click to browse · PDF, PNG, JPG, DOCX · Max 10MB
                </p>
                {uploading && (
                  <div className="w-full max-w-xs mt-4">
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <span className="text-[9px] text-slate-400 mt-1 block">
                      Uploading & running OCR analysis...
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Documents Viewer */}
          {uploadedDocs.length > 0 && (
            <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl space-y-4">
              {/* Tabs */}
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/40">
                <h2 className="text-sm font-bold text-slate-200">Uploaded Documents</h2>
                <div className="flex gap-1 bg-slate-900/50 rounded-lg p-1">
                  {(['docs', 'ocr'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                        activeTab === tab
                          ? 'bg-indigo-600 text-white'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {tab === 'docs' ? 'Overview' : 'OCR / AI Data'}
                    </button>
                  ))}
                </div>
              </div>

              {activeTab === 'docs' && (
                <div className="space-y-2">
                  {uploadedDocs.map((doc: Document) => (
                    <div
                      key={doc.id}
                      className="border border-slate-800/80 rounded-lg overflow-hidden bg-slate-900/10"
                    >
                      <div className="flex items-center justify-between p-3">
                        <div className="flex items-center gap-3">
                          {doc.status === 'Valid' ? (
                            <FileCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                          ) : (
                            <FileWarning className="w-4 h-4 text-rose-400 shrink-0" />
                          )}
                          <div>
                            <span className="text-xs font-bold text-slate-200">{doc.name}</span>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                {doc.category?.replace(/_/g, ' ') || 'other'}
                              </span>
                              {doc.confidence_score > 0 && (
                                <span className={`text-[9px] font-semibold ${
                                  doc.confidence_score >= 0.7 ? 'text-emerald-400' :
                                  doc.confidence_score >= 0.4 ? 'text-amber-400' : 'text-slate-500'
                                }`}>
                                  OCR: {(doc.confidence_score * 100).toFixed(0)}%
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {doc.file_url && (
                            <a
                              href={doc.file_url}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </a>
                          )}
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                            doc.status === 'Valid'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : doc.status === 'Invalid'
                              ? 'bg-rose-500/10 text-rose-400'
                              : 'bg-slate-700/50 text-slate-400'
                          }`}>
                            {doc.status}
                          </span>
                        </div>
                      </div>
                      {/* AI anomalies preview */}
                      {doc.ai_analysis?.anomalies?.length > 0 && (
                        <div className="px-3 pb-3">
                          {doc.ai_analysis.anomalies.map((a: string, i: number) => (
                            <div key={i} className="flex items-start gap-1.5 text-[10px] text-amber-400/80 mt-1">
                              <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                              <span>{a}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'ocr' && (
                <div className="space-y-3">
                  {uploadedDocs.map((doc: Document) => {
                    const isOpen = expandedDoc === doc.id;
                    return (
                      <div key={doc.id} className="border border-slate-800/80 rounded-lg overflow-hidden">
                        <button
                          onClick={() => toggleDocExpand(doc.id)}
                          className="w-full flex justify-between items-center p-3 text-left hover:bg-slate-800/20 transition-all"
                        >
                          <span className="text-xs font-bold text-slate-200">{doc.name}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-slate-500">
                              {doc.category?.replace(/_/g, ' ')}
                            </span>
                            {isOpen ? (
                              <ChevronUp className="w-4 h-4 text-slate-500" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-slate-500" />
                            )}
                          </div>
                        </button>
                        {isOpen && (
                          <div className="p-4 bg-slate-950/40 border-t border-slate-800/50 space-y-3">
                            {/* AI Analysis */}
                            {Object.keys(doc.ai_analysis || {}).length > 0 && (
                              <div>
                                <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider mb-1">
                                  AI Analysis
                                </div>
                                <pre className="text-[10px] text-indigo-300 font-mono bg-slate-950 p-3 rounded border border-slate-800 overflow-x-auto max-h-48">
                                  {JSON.stringify(doc.ai_analysis, null, 2)}
                                </pre>
                              </div>
                            )}
                            {/* Extracted OCR Data */}
                            {Object.keys(doc.extracted_data || {}).length > 0 && (
                              <div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                                  OCR Heuristic Extraction
                                </div>
                                <pre className="text-[10px] text-slate-400 font-mono bg-slate-950 p-3 rounded border border-slate-800 overflow-x-auto max-h-36">
                                  {JSON.stringify(doc.extracted_data, null, 2)}
                                </pre>
                              </div>
                            )}
                            {/* Validation result */}
                            <div>
                              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                                Rules Engine Result
                              </div>
                              <div className={`p-2.5 rounded text-xs border ${
                                doc.status === 'Valid'
                                  ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400/90'
                                  : 'bg-rose-500/5 border-rose-500/10 text-rose-400/90'
                              }`}>
                                {doc.validation_result?.details ||
                                  doc.validation_result?.errors?.join(', ') ||
                                  'Document checked.'}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* AI Analysis Panel */}
          {eligibility && (
            <AIAnalysisPanel eligibilityScore={eligibility} />
          )}
        </div>

        {/* Right Column: Scores + Report */}
        <div className="space-y-6">
          {/* AI Eligibility Score Card */}
          {eligibility ? (
            <EligibilityScoreCard score={eligibility} />
          ) : (
            /* Placeholder when not yet assessed */
            <div className="p-6 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl text-center space-y-4">
              <div className="text-4xl mb-2">🤖</div>
              <h3 className="text-sm font-bold text-slate-200">AI Assessment Not Run</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Upload at least one document, then click{' '}
                <strong className="text-indigo-400">Run AI Assessment</strong> to get the
                5-category eligibility score, risk analysis, and recommendations.
              </p>
              <button
                onClick={() => runAIAssessmentMutation.mutate()}
                disabled={aiLoading || uploadedDocs.length === 0}
                className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-40 text-white rounded-lg py-2.5 font-semibold text-xs transition-all flex items-center justify-center gap-2"
              >
                {aiLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {aiLoading ? 'Analyzing...' : 'Run AI Assessment'}
              </button>
            </div>
          )}

          {/* Rules Compliance Score */}
          <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl flex flex-col items-center text-center">
            <h2 className="text-sm font-bold text-slate-200 mb-5">Rules Compliance</h2>
            <div className={`w-28 h-28 rounded-full border-4 flex flex-col items-center justify-center mb-5 shadow-lg ${scoreColor}`}>
              <span className="text-3xl font-extrabold tracking-tight">{score}</span>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">/ 100</span>
            </div>
            <div className={`w-full p-3 border rounded-lg flex items-center justify-center gap-2 mb-2 ${bannerColor}`}>
              <BannerIcon className="w-4 h-4 shrink-0" />
              <span className="text-xs font-bold">Status: {reportStatus}</span>
            </div>
            <span className="text-[9px] text-slate-500 italic mt-1">
              Recalculates automatically on new uploads
            </span>
          </div>

          {/* Compliance Audit Log */}
          {report && (
            <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl space-y-4">
              <h2 className="text-sm font-bold text-slate-200 pb-2 border-b border-slate-800/40">
                Compliance Audit Log
              </h2>

              {report.correct_documents.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider mb-1.5">
                    Validated Documents
                  </div>
                  <div className="space-y-1">
                    {report.correct_documents.map((doc, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-xs text-slate-300">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span>{doc}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {report.missing_documents.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold text-rose-400 uppercase tracking-wider mb-1.5">
                    Missing Documents
                  </div>
                  <div className="space-y-1">
                    {report.missing_documents.map((doc, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-xs text-slate-300">
                        <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                        <span>{doc}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {report.issues.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold text-amber-400 uppercase tracking-wider mb-1.5">
                    Identified Issues
                  </div>
                  <div className="space-y-1.5">
                    {report.issues.map((issue, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                        <span>{issue}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                  Recommendations
                </div>
                <div className="p-3 bg-indigo-500/5 border border-indigo-500/10 text-indigo-300/90 text-xs rounded-lg leading-relaxed">
                  {report.recommendations || 'Review all checklist requirements to complete.'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
