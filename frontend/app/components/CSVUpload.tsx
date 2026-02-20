'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { analyzeCsv } from '@/app/client/api';

const columns = ['transaction_id', 'sender_id', 'receiver_id', 'amount', 'timestamp'];

// ── CSV File Icon (teal rounded square with doc + download arrow) ──
const CSVIcon = () => (
  <div style={{
    width: '80px', height: '80px',
    background: 'linear-gradient(145deg, #00926B, #007a55)',
    borderRadius: '18px',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    boxShadow: '0 8px 32px rgba(0,146,107,0.4)',
    position: 'relative',
  }}>
    {/* Background doc silhouette */}
    <svg width="52" height="52" viewBox="0 0 52 52" fill="none">
      {/* Back doc */}
      <rect x="14" y="6" width="28" height="36" rx="4" fill="rgba(255,255,255,0.2)" transform="rotate(-8 14 6)" />
      {/* Front doc */}
      <rect x="12" y="8" width="28" height="36" rx="4" fill="white" />
      {/* Lines */}
      <rect x="18" y="16" width="16" height="2" rx="1" fill="#00926B" />
      <rect x="18" y="21" width="12" height="2" rx="1" fill="#00926B" />
      {/* Download circle */}
      <circle cx="36" cy="38" r="10" fill="#00926B" />
      <path d="M36 33v8M33 38l3 3 3-3" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  </div>
);

export default function CSVUpload() {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setError(null);
    const f = e.dataTransfer.files?.[0];
    if (f?.name.toLowerCase().endsWith('.csv')) setFile(f);
    else if (f) setError('Please upload a .csv file');
  };
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeCsv(file);
      if (!mountedRef.current) return;
      router.push(`/check-fraud?session=${encodeURIComponent(res.session_token)}`);
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : 'Analysis failed');
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  };

  return (
    <section
      id="upload-csv"
      style={{
      background: '#020202',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 24px',
      fontFamily: "var(--font-subheading), 'Segoe UI', sans-serif",
      color: '#fff',
    }}>

      {/* ── Header (outside the card) ── */}
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        {/* GET STARTED label */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          gap: '10px', marginBottom: '20px',
        }}>
          <div style={{ width: '28px', height: '1.5px', background: 'rgba(255,255,255,0.45)' }} />
          <span style={{
            fontSize: '10px', letterSpacing: '3.5px',
            color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase',
          }}>
            GET STARTED
          </span>
        </div>

        {/* Title */}
        <h1 style={{
          margin: '0 0 18px',
          fontSize: 'clamp(36px, 5.5vw, 58px)',
          fontWeight: '800',
          lineHeight: '1.12',
          letterSpacing: '-2px',
          fontFamily: "var(--font-heading), Georgia, serif",
        }}>
          Drop Your CSV.<br />
          Expose <span style={{ color: '#00926B' }}>The Ring.</span>
        </h1>

        {/* Subtitle */}
        <p style={{
          margin: 0,
          fontSize: '15px',
          color: 'rgba(255,255,255,0.55)',
          lineHeight: '1.6',
        }}>
          Upload your transaction data and get full forensic results in under 30 seconds.
        </p>
      </div>

      {/* ── Drop Zone Card ── */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          width: '100%',
          maxWidth: '620px',
          background: isDragging
            ? 'rgba(0,146,107,0.06)'
            : 'rgba(2,2,2,0.9)',
          borderRadius: '18px',
          border: `2px dashed ${isDragging ? '#00926B' : 'rgba(255,255,255,0.25)'}`,
          padding: '52px 40px 44px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0',
          transition: 'border-color 0.2s, background 0.2s',
          cursor: 'default',
        }}
      >
        {/* Icon */}
        <div style={{ marginBottom: '22px' }}>
          <CSVIcon />
        </div>

        {/* Title */}
        <div style={{
          fontSize: '19px',
          fontWeight: '700',
          color: '#ffffff',
          marginBottom: '10px',
          textAlign: 'center',
        }}>
          Drag & drop your CSV file
        </div>

        {/* Browse + size */}
        <div style={{
          fontSize: '13.5px',
          color: 'rgba(255,255,255,0.55)',
          marginBottom: '28px',
          textAlign: 'center',
        }}>
          <span
            onClick={() => inputRef.current?.click()}
            style={{
              color: '#00926B',
              textDecoration: 'underline',
              cursor: 'pointer',
              textUnderlineOffset: '3px',
            }}
          >
            or click to browse
          </span>
          {' · '}
          <span style={{ color: '#ef4444', fontWeight: '600' }}>Max size 5MB</span>
        </div>

        {/* Hidden file input */}
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {error && (
          <p style={{ color: '#ef4444', fontSize: '14px', marginBottom: '12px', textAlign: 'center' }}>
            {error}
          </p>
        )}

        {/* Choose File / Analyze buttons */}
        <div style={{ display: 'flex', gap: '12px', marginBottom: '32px', flexWrap: 'wrap', justifyContent: 'center' }}>
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            style={{
              background: 'transparent',
              color: '#00926B',
              border: '2px solid #00926B',
              borderRadius: '10px',
              padding: '13px 28px',
              fontSize: '15px',
              fontWeight: '700',
              cursor: 'pointer',
              transition: 'all 0.18s',
            }}
          >
            {file ? `✓ ${file.name}` : 'Choose File'} →
          </button>
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={!file || loading}
            style={{
              background: file && !loading ? '#00926B' : 'rgba(255,255,255,0.2)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '10px',
              padding: '13px 36px',
              fontSize: '15px',
              fontWeight: '700',
              cursor: file && !loading ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'background 0.18s',
            }}
            onMouseEnter={e => file && !loading && (e.currentTarget.style.background = '#007a55')}
            onMouseLeave={e => file && !loading && (e.currentTarget.style.background = '#00926B')}
          >
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
        </div>

        {/* Column tags */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
          {columns.map(col => (
            <span key={col} style={{
              padding: '5px 16px',
              borderRadius: '999px',
              border: '1px solid rgba(255,255,255,0.22)',
              background: 'transparent',
              fontSize: '12.5px',
              color: 'rgba(255,255,255,0.65)',
              fontFamily: "'Fira Code', monospace",
              letterSpacing: '0.2px',
            }}>
              {col}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
