import React, { useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import type { Submission, CountryRule } from '../types';
import { 
  ArrowLeft, 
  UploadCloud, 
  FileCheck, 
  FileWarning, 
  FileClock, 
  Download,
  Play,
  Loader2,
  Info,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Eye,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function SubmissionDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // States
  const [selectedDocType, setSelectedDocType] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [validationLoading, setValidationLoading] = useState(false);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  // Fetch Submission detail
  const { data: submission, isLoading, error } = useQuery<Submission>({
    queryKey: ['submission', id],
    queryFn: async () => {
      const response = await api.get(`submissions/${id}/`);
      return response.data;
    },
    refetchInterval: 5000, // Refresh every 5s to check OCR updates
  });

  // Fetch Country Rules to see required documents
  const { data: rulesList = [] } = useQuery<CountryRule[]>({
    queryKey: ['country-rules'],
    queryFn: async () => {
      const response = await api.get('country-rules/');
      return response.data;
    }
  });

  // Run validation mutation
  const runValidationMutation = useMutation({
    mutationFn: async () => {
      setValidationLoading(true);
      const response = await api.post(`submissions/${id}/validate_rules/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] });
    },
    onError: (err) => {
      console.error(err);
      alert("Failed to run rules validation. Check OCR data.");
    },
    onSettled: () => {
      setValidationLoading(false);
    }
  });

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-slate-400">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mr-3" />
        <span>Loading submission audit panel...</span>
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

  // Find country rule required docs
  const matchingRule = rulesList.find(
    r => r.country.toLowerCase() === submission.country.toLowerCase() &&
         r.visa_type.toLowerCase() === submission.visa_type.toLowerCase()
  );

  const requiredDocuments = matchingRule?.required_documents || ['Passport', 'Bank Statement'];

  // Map uploaded documents
  const uploadedDocs = submission.documents || [];
  const uploadedNames = uploadedDocs.map(d => d.name.toLowerCase().trim());

  // File Upload Handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFileToServer(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFileToServer(e.target.files[0]);
    }
  };

  const uploadFileToServer = async (file: File) => {
    if (!selectedDocType) {
      alert("Please select the Document Type from the dropdown first.");
      return;
    }

    // Client side size check (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      alert("File size exceeds the 5MB limit. Please upload a smaller file.");
      return;
    }

    // Client side type check (PDF, PNG, JPG, DOCX)
    const allowedExtensions = ['.pdf', '.png', '.jpg', '.jpeg', '.docx'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedExtensions.includes(fileExtension)) {
      alert("Invalid file type. Supported types: PDF, PNG, JPG, JPEG, DOCX");
      return;
    }

    setUploading(true);
    setUploadProgress(15);
    
    const formData = new FormData();
    formData.append('submission', submission.id);
    formData.append('name', selectedDocType);
    formData.append('file', file);

    try {
      setUploadProgress(45);
      await api.post('documents/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });
      setUploadProgress(90);
      queryClient.invalidateQueries({ queryKey: ['submission', id] });
      setSelectedDocType('');
      // Trigger auto-check of rules engine
      runValidationMutation.mutate();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || "Upload failed. Please review console logs.");
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const triggerDownloadReport = async () => {
    try {
      const response = await api.get(`submissions/${id}/download_report/`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Compliance_Report_${submission.client_detail.name.replace(/\s+/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      console.error("PDF download fail", err);
      alert("Failed to download PDF report. Please run compliance validation first.");
    }
  };

  const toggleDocExpand = (docId: string) => {
    setExpandedDoc(expandedDoc === docId ? null : docId);
  };

  // Color mapping for report score
  const report = submission.validation_report;
  const score = report?.score ?? 0;
  const reportStatus = report?.status ?? 'Unchecked';

  let scoreColor = 'text-slate-400 border-slate-700 bg-slate-800/20';
  let bannerColor = 'bg-slate-900 border-slate-800 text-slate-400';
  let bannerIcon = Info;

  if (reportStatus === 'Passed') {
    scoreColor = 'text-emerald-400 border-emerald-500/30 bg-emerald-500/5';
    bannerColor = 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400';
    bannerIcon = CheckCircle;
  } else if (reportStatus === 'Warning') {
    scoreColor = 'text-amber-400 border-amber-500/30 bg-amber-500/5';
    bannerColor = 'bg-amber-500/5 border-amber-500/20 text-amber-400';
    bannerIcon = AlertTriangle;
  } else if (reportStatus === 'Failed') {
    scoreColor = 'text-rose-400 border-rose-500/30 bg-rose-500/5';
    bannerColor = 'bg-rose-500/5 border-rose-500/20 text-rose-400';
    bannerIcon = XCircle;
  }

  const BannerIcon = bannerIcon;

  return (
    <div className="space-y-6">
      {/* Navigation and Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800/40 pb-4">
        <div className="flex items-center gap-3">
          <Link to="/submissions" className="p-2 bg-slate-800/60 hover:bg-slate-700/60 rounded-lg text-slate-400 hover:text-slate-200 transition-all border border-slate-800">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-slate-100">Application Audit Panel</h1>
            <p className="text-xs text-slate-400">Validate checklist completeness and inspect structured OCR details.</p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button
            onClick={() => runValidationMutation.mutate()}
            disabled={validationLoading || uploadedDocs.length === 0}
            className="flex-1 sm:flex-initial bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg py-2 px-4 font-semibold text-xs transition-all duration-150 flex items-center justify-center gap-1.5 cursor-pointer shadow-lg shadow-indigo-600/10 hover:shadow-indigo-600/20"
          >
            {validationLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5" />
            )}
            Run Verification
          </button>
          
          {report && (
            <button
              onClick={triggerDownloadReport}
              className="flex-1 sm:flex-initial bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg py-2 px-4 font-semibold text-xs transition-all duration-150 flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              Download Report
            </button>
          )}
        </div>
      </div>

      {/* Main layout grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Client Details, Document Checklists and OCR fields */}
        <div className="lg:col-span-2 space-y-6">
          {/* Client summary card */}
          <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">Applicant</span>
              <span className="text-xs font-bold text-slate-200">{submission.client_detail.name}</span>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">Passport Number</span>
              <span className="text-xs font-bold text-indigo-400">{submission.client_detail.passport_number}</span>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">Destination</span>
              <span className="text-xs font-bold text-slate-200">{submission.country} &bull; {submission.visa_type}</span>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">Created Date</span>
              <span className="text-xs font-bold text-slate-400">{new Date(submission.created_at).toLocaleDateString()}</span>
            </div>
          </div>

          {/* Document Checklist & Uploader */}
          <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl space-y-5">
            <h2 className="text-sm font-bold text-slate-200 pb-2 border-b border-slate-800/40">Checklist & Document Uploader</h2>

            {/* Checklist Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {requiredDocuments.map((reqDoc: string, idx: number) => {
                const isUploaded = uploadedNames.includes(reqDoc.toLowerCase().trim());
                const matchingDoc = uploadedDocs.find(d => d.name.toLowerCase().trim() === reqDoc.toLowerCase().trim());
                
                return (
                  <div key={idx} className={`p-3 rounded-lg border flex items-center justify-between ${
                    isUploaded 
                      ? matchingDoc?.status === 'Valid' 
                        ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-300'
                        : 'bg-rose-500/5 border-rose-500/20 text-rose-300'
                      : 'bg-slate-900/40 border-slate-800/60 text-slate-400'
                  }`}>
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

            {/* Drag and Drop Uploader */}
            <div className="space-y-3 pt-3">
              <div className="flex items-center gap-3 max-w-sm">
                <select
                  value={selectedDocType}
                  onChange={(e) => setSelectedDocType(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:outline-none rounded-lg py-2 px-3 text-xs text-slate-300 cursor-pointer font-semibold"
                >
                  <option value="">-- Choose Document Category --</option>
                  {requiredDocuments.map((req: string, idx: number) => (
                    <option key={idx} value={req}>{req}</option>
                  ))}
                </select>
              </div>

              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => selectedDocType && fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center flex flex-col items-center justify-center cursor-pointer transition-all ${
                  !selectedDocType ? 'opacity-40 cursor-not-allowed border-slate-850' :
                  dragActive ? 'border-indigo-500 bg-indigo-500/5' : 'border-slate-800 hover:border-slate-700/80 hover:bg-slate-900/10'
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
                
                <UploadCloud className="w-8 h-8 text-slate-500 mb-3" />
                <p className="text-xs font-bold text-slate-300">
                  {selectedDocType ? `Upload ${selectedDocType}` : 'Select a document category above'}
                </p>
                <p className="text-[10px] text-slate-500 mt-1.5">
                  Drag and drop file here, or click to browse. Max size 5MB (PDF, PNG, JPG, DOCX)
                </p>
                
                {uploading && (
                  <div className="w-full max-w-xs mt-4">
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                    </div>
                    <span className="text-[9px] text-slate-400 mt-1 block">Uploading compliance document...</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Extracted OCR Viewer Panel */}
          {uploadedDocs.length > 0 && (
            <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl space-y-4">
              <h2 className="text-sm font-bold text-slate-200 pb-2 border-b border-slate-800/40">Extracted OCR Text & Heuristics</h2>
              
              <div className="space-y-2.5">
                {uploadedDocs.map((doc) => {
                  const isOpen = expandedDoc === doc.id;
                  return (
                    <div key={doc.id} className="border border-slate-800/80 rounded-lg overflow-hidden bg-slate-900/10">
                      <button
                        onClick={() => toggleDocExpand(doc.id)}
                        className="w-full flex justify-between items-center p-3 text-left hover:bg-slate-800/20 transition-all"
                      >
                        <div className="flex items-center gap-3">
                          {doc.status === 'Valid' ? (
                            <FileCheck className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <FileWarning className="w-4 h-4 text-rose-400" />
                          )}
                          <div>
                            <span className="text-xs font-bold text-slate-200">{doc.name}</span>
                            <span className="text-[9px] text-slate-500 block">Uploaded {new Date(doc.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          {doc.file_url && (
                            <a
                              href={doc.file_url}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                              title="View uploaded document"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </a>
                          )}
                          {isOpen ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                        </div>
                      </button>

                      {isOpen && (
                        <div className="p-4 bg-slate-950/40 border-t border-slate-800/50 space-y-3">
                          {/* Extracted JSON Metadata */}
                          <div>
                            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">OCR Structured JSON</div>
                            <pre className="text-[10px] text-indigo-300 font-mono bg-slate-950 p-3 rounded border border-slate-800 overflow-x-auto">
                              {JSON.stringify(doc.extracted_data, null, 2)}
                            </pre>
                          </div>

                          {/* Rule Checks Detail */}
                          <div>
                            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Compliance Rules Assessment</div>
                            <div className={`p-2.5 rounded text-xs border ${
                              doc.status === 'Valid' ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400/90' : 'bg-rose-500/5 border-rose-500/10 text-rose-400/90'
                            }`}>
                              {doc.validation_result?.details || doc.validation_result?.errors?.join(', ') || 'Document verification checked.'}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right 1 Column: Compliance Score & Reports Banner */}
        <div className="space-y-6">
          {/* Radial score box */}
          <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl flex flex-col items-center text-center">
            <h2 className="text-sm font-bold text-slate-200 mb-6">Validation Score</h2>
            
            {/* Score Ring */}
            <div className={`w-32 h-32 rounded-full border-4 flex flex-col items-center justify-center mb-6 shadow-lg ${scoreColor}`}>
              <span className="text-3xl font-extrabold tracking-tight">{score}</span>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">out of 100</span>
            </div>

            {/* Status Banner */}
            <div className={`w-full p-3 border rounded-lg flex items-center justify-center gap-2 mb-2 ${bannerColor}`}>
              <BannerIcon className="w-4 h-4 shrink-0" />
              <span className="text-xs font-bold">Compliance Status: {reportStatus}</span>
            </div>
            
            <span className="text-[9px] text-slate-500 italic mt-1">Check score recalculates automatically on new uploads</span>
          </div>

          {/* Audit report details */}
          {report && (
            <div className="p-5 bg-[#0a0e1a]/80 border border-slate-800/60 rounded-xl space-y-4">
              <h2 className="text-sm font-bold text-slate-200 pb-2 border-b border-slate-800/40">Compliance Audit Log</h2>

              {/* Correct Documents Check */}
              {report.correct_documents.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 text-emerald-400">Validated Documents</div>
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

              {/* Missing Documents Check */}
              {report.missing_documents.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 text-rose-400">Missing Documents</div>
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

              {/* Warnings and issues checklist */}
              {report.issues.length > 0 && (
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 text-amber-400">Identified Warning Issues</div>
                  <div className="space-y-1.5">
                    {report.issues.map((issue, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-xs text-slate-400 leading-snug">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                        <span>{issue}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations Box */}
              <div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Consultant Recommendations</div>
                <div className="p-3 bg-indigo-500/5 border border-indigo-500/10 text-indigo-300/90 text-xs rounded-lg leading-relaxed">
                  {report.recommendations || "Review all checklist requirements to complete."}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
