import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, ArrowLeft, Trash2 } from 'lucide-react';
import { ResponsiveNav } from '../components/ResponsiveNav';
import { SideNav } from '../components/SideNav';

export const Documents = () => {
  const navigate = useNavigate();
  const [userSub, setUserSub] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDesktop, setIsDesktop] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{
    document_id: string;
    filename: string;
    size_bytes: number;
    vector_count: number;
    uploaded_at: string;
  }>>([]);

  useEffect(() => {
    checkAuth();
    loadDocuments();
  }, []);

  // Detect desktop vs mobile for content layout adjustment
  useEffect(() => {
    const checkDesktop = () => {
      setIsDesktop(window.innerWidth >= 768);
    };

    checkDesktop();
    window.addEventListener('resize', checkDesktop);
    return () => window.removeEventListener('resize', checkDesktop);
  }, []);

  const checkAuth = async () => {
    try {
      const res = await fetch('/auth/me', { credentials: 'include' });
      if (res.status === 200) {
        const me = await res.json();
        const sub = me.user?.sub || '';
        setUserSub(sub);
      } else {
        navigate('/login');
      }
    } catch (e) {
      console.error('Auth check failed', e);
      navigate('/login');
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await fetch('/internal/knowledge/list', {
        credentials: 'same-origin',
        headers: {
          'X-Internal-API-Key': import.meta.env.VITE_BACKEND_AGENT_INTERNAL_API_KEY || ''
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUploadedFiles(data.documents || []);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Only PDF files are supported');
        return;
      }
      setSelectedFile(file);
      setError('');
      setSuccess('');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('user_sub', userSub);

      const response = await fetch(
        `${import.meta.env.VITE_BACKEND_AGENT_URL || 'http://127.0.0.1:9000'}/internal/knowledge/upload`,
        {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'X-Internal-API-Key': import.meta.env.VITE_BACKEND_AGENT_INTERNAL_API_KEY || ''
          },
          body: formData
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Upload failed');
      }

      const result = await response.json();
      setSuccess(`Document "${result.filename}" uploaded successfully! ${result.vector_count} chunks processed.`);
      setSelectedFile(null);
      await loadDocuments();
    } catch (err: any) {
      setError(err.message || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <main className="page" style={{ position: 'relative', minHeight: '100vh', paddingBottom: '120px' }}>
      {/* Side Navigation */}
      <SideNav />
      <div className="max-w-7xl mx-auto px-8 py-10" style={{ marginLeft: isDesktop ? '80px' : '0' }}>
        <button
          onClick={() => navigate('/assistant')}
          className="mb-8 px-4 py-2.5 bg-white/60 hover:bg-white/80 text-[var(--text-main)] rounded-lg transition-all duration-300 flex items-center gap-2 font-medium border border-[var(--line)]"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Assistant
        </button>
        
        <div className="mb-10">
          <h1 className="text-4xl font-bold text-[var(--text-main)] mb-3">
            Knowledge Documents
          </h1>
          <p className="text-[var(--text-soft)] text-lg">
            Upload PDF documents to enhance the AI's knowledge base for better contextual responses
          </p>
        </div>

        {error && (
          <div className="mb-8 p-5 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-4 text-red-700">
            <AlertCircle className="w-6 h-6" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-8 p-5 bg-green-50 border border-green-200 rounded-2xl flex items-center gap-4 text-green-700">
            <CheckCircle className="w-6 h-6" />
            <span className="font-medium">{success}</span>
          </div>
        )}

        {/* Two Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Upload Section */}
          <div className="bg-white rounded-2xl p-8 shadow-lg border-l-4 border-[var(--teal)]">
            <h2 className="text-2xl font-semibold text-[var(--text-main)] mb-2 flex items-center gap-3">
              <div className="p-2 bg-[var(--teal-soft)] rounded-lg">
                <Upload className="w-6 h-6 text-[var(--teal)]" />
              </div>
              Upload Document
            </h2>
            <p className="text-[var(--text-soft)] mb-6">Add new PDF files to your knowledge base</p>

            <div className="border-2 border-dashed border-[var(--teal)]/30 bg-[var(--teal-soft)] rounded-2xl p-10 text-center hover:border-[var(--teal)] hover:bg-[var(--teal-soft)] transition-all duration-300 cursor-pointer">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer block"
              >
                <FileText className="w-16 h-16 text-[var(--teal)] mx-auto mb-4" />
                <p className="text-[var(--text-main)] font-medium text-lg mb-2">
                  {selectedFile ? selectedFile.name : 'Click to select a PDF file'}
                </p>
                <p className="text-[var(--text-soft)]">
                  Only PDF files are supported
                </p>
              </label>
            </div>

            {selectedFile && (
              <div className="mt-6 flex items-center justify-between p-5 bg-[var(--teal-soft)] rounded-xl border border-[var(--teal)]/30">
                <div className="flex items-center gap-4">
                  <FileText className="w-6 h-6 text-[var(--teal)]" />
                  <div>
                    <span className="text-[var(--text-main)] font-medium">{selectedFile.name}</span>
                    <span className="text-[var(--text-soft)] text-sm ml-3">
                      ({formatFileSize(selectedFile.size)})
                    </span>
                  </div>
                </div>
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="px-5 py-3 bg-[var(--teal)] hover:bg-[var(--teal-deep)] disabled:bg-[var(--text-soft)] text-white rounded-xl transition-colors flex items-center gap-2 font-medium shadow-md hover:shadow-lg"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5" />
                      Upload
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Documents List */}
          <div className="bg-white rounded-2xl p-8 shadow-lg">
            <h2 className="text-2xl font-semibold text-[var(--text-main)] mb-2 flex items-center gap-3">
              <div className="p-2 bg-[var(--teal-soft)] rounded-lg">
                <FileText className="w-6 h-6 text-[var(--teal)]" />
              </div>
              Uploaded Documents
            </h2>
            <p className="text-[var(--text-soft)] mb-6">Your current knowledge base files</p>

            {uploadedFiles.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-16 h-16 text-[var(--teal)]/30 mx-auto mb-4" />
                <p className="text-[var(--text-soft)]">No documents uploaded yet</p>
              </div>
            ) : (
              <div className="space-y-4">
                {uploadedFiles.map((doc) => (
                  <div
                    key={doc.document_id}
                    className="flex items-center justify-between p-4 bg-[var(--bg-sand)] rounded-xl border border-[var(--line)] hover:bg-[var(--bg-cream)] transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <FileText className="w-5 h-5 text-[var(--teal)]" />
                      <div>
                        <span className="text-[var(--text-main)] font-medium block">{doc.filename}</span>
                        <span className="text-[var(--text-soft)] text-sm">
                          {formatFileSize(doc.size_bytes)} • {doc.vector_count} chunks
                        </span>
                      </div>
                    </div>
                    <button
                      className="p-2 text-[var(--teal)] hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Responsive Navigation */}
      <ResponsiveNav />
    </main>
  );
};